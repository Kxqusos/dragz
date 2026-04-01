import httpx
import re
import logging
from dataclasses import dataclass
from redis.asyncio import Redis
from datetime import UTC, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.dependencies import get_session_factory
from app.services.cache import (
    get_cached_geocode_record,
    is_provider_in_cooldown,
    set_cached_geocode_record,
    set_provider_cooldown,
    try_acquire_geocode_provider_quota,
)
from app.services.pharmacy_coordinates import (
    get_pharmacy_coordinate_record,
    upsert_pharmacy_coordinate_record,
)
from app.services.search_engine.address import (
    AddressMatchResult,
    build_geocode_queries as build_search_engine_geocode_queries,
    evaluate_address_match,
    normalize_address_for_matching as normalize_search_engine_address,
)

ROSTOV_REGION_BOUNDS = {
    "min_lat": 45.9,
    "max_lat": 50.4,
    "min_lon": 38.2,
    "max_lon": 44.4,
}

logger = logging.getLogger(__name__)
GEOCODE_RESOLVED_TTL_SECONDS = 60 * 60 * 24 * 14
GEOCODE_UNRESOLVED_TTL_SECONDS = 60 * 60 * 24
GEOCODE_RATE_LIMITED_TTL_SECONDS = 60 * 10


@dataclass(frozen=True)
class GeocodeCandidateSelection:
    resolved_coords: tuple[float, float] | None
    match_result: AddressMatchResult


def normalize_address_for_geocoding(address: str) -> str:
    queries = build_search_engine_geocode_queries(address, default_city="Ростов-на-Дону")
    return queries[0] if queries else address.replace("_", " ").strip()


def build_geocode_queries(address: str) -> list[str]:
    return build_search_engine_geocode_queries(address, default_city="Ростов-на-Дону")


def normalize_address_for_matching(address: str) -> str:
    return normalize_search_engine_address(address, default_city="Ростов-на-Дону")


def is_within_rostov_region(lat: float, lon: float) -> bool:
    return (
        ROSTOV_REGION_BOUNDS["min_lat"] <= lat <= ROSTOV_REGION_BOUNDS["max_lat"]
        and ROSTOV_REGION_BOUNDS["min_lon"] <= lon <= ROSTOV_REGION_BOUNDS["max_lon"]
    )


async def geocode_address(
    address: str,
    settings: Settings,
    *,
    near: tuple[float, float] | None = None,
    cache: Redis | None = None,
    db_session: AsyncSession | None = None,
    client: httpx.AsyncClient | None = None,
    force_refresh: bool = False,
) -> tuple[float, float] | None:
    owns_client = client is None
    owns_db_session = db_session is None
    active_db_session = db_session or get_session_factory()()
    active_client = client or httpx.AsyncClient(
        timeout=6.0,
        headers={"User-Agent": f"{settings.app_name}/1.0"},
    )
    try:
        query_variants = build_geocode_queries(address)
        logger.info("geocode_start address=%r queries=%s near=%s", address, query_variants, near)

        persisted_record = None
        if not force_refresh and active_db_session is not None:
            persisted_record = await get_pharmacy_coordinate_record(active_db_session, address)
            if persisted_record is not None:
                logger.info("geocode_db_hit address=%r status=%s", address, persisted_record.status)
                if (
                    persisted_record.status == "resolved"
                    and persisted_record.lat is not None
                    and persisted_record.lon is not None
                ):
                    await set_cached_geocode_record(
                        cache,
                        address,
                        {
                            "status": "resolved",
                            "original_address": address,
                            "lat": persisted_record.lat,
                            "lon": persisted_record.lon,
                            "provider": persisted_record.provider,
                            "query": persisted_record.query,
                            "updated_at": persisted_record.updated_at.isoformat(),
                        },
                        ttl=GEOCODE_RESOLVED_TTL_SECONDS,
                    )
                    return (persisted_record.lat, persisted_record.lon)
                return None
            logger.info("geocode_db_miss address=%r", address)

        cached_record = None if force_refresh else await get_cached_geocode_record(cache, address)
        if cached_record is not None:
            logger.info("geocode_cache_hit address=%r status=%s", address, cached_record.get("status"))
            if cached_record.get("status") == "resolved":
                lat = cached_record.get("lat")
                lon = cached_record.get("lon")
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    if active_db_session is not None:
                        await upsert_pharmacy_coordinate_record(
                            active_db_session,
                            address=address,
                            status="resolved",
                            lat=float(lat),
                            lon=float(lon),
                            provider=str(cached_record.get("provider") or ""),
                            query=str(cached_record.get("query") or ""),
                            matching_key=normalize_address_for_matching(address),
                            match_strategy=str(cached_record.get("match_strategy") or "cached-resolved"),
                            confidence_tier=str(cached_record.get("confidence_tier") or "high"),
                            updated_at=_parse_updated_at(cached_record.get("updated_at")),
                        )
                    return (float(lat), float(lon))
            if active_db_session is not None:
                await upsert_pharmacy_coordinate_record(
                    active_db_session,
                    address=address,
                    status=str(cached_record.get("status") or "unresolved"),
                    provider=str(cached_record.get("provider") or "") or None,
                    query=str(cached_record.get("query") or "") or None,
                    matching_key=normalize_address_for_matching(address),
                    match_strategy=str(cached_record.get("match_strategy") or "cached-nonresolved"),
                    confidence_tier=str(cached_record.get("confidence_tier") or "low"),
                    updated_at=_parse_updated_at(cached_record.get("updated_at")),
                )
            return None
        logger.info("geocode_cache_miss address=%r", address)

        for query_text in query_variants:
            if settings.geoapify_api_key:
                geoapify_quota_available = await try_acquire_geocode_provider_quota(
                    cache,
                    "geoapify",
                    daily_limit=settings.geocode_provider_daily_request_limit,
                    safety_buffer=settings.geocode_provider_daily_safety_buffer,
                )
                if not geoapify_quota_available:
                    logger.warning("geocode_provider_quota_exhausted provider=geoapify address=%r", address)
                else:
                    geoapify_params = {
                        "text": query_text,
                        "filter": "countrycode:ru",
                        "limit": 5,
                        "apiKey": settings.geoapify_api_key,
                    }
                    if near is not None:
                        geoapify_params["bias"] = f"proximity:{near[1]},{near[0]}"

                    response = await active_client.get(
                        "https://api.geoapify.com/v1/geocode/search",
                        params=geoapify_params,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    features = payload.get("features", [])
                    logger.info(
                        "geocode_provider_response provider=geoapify address=%r query=%r candidates=%d",
                        address,
                        query_text,
                        len(features),
                    )
                    geoapify_match = pick_matching_geoapify_candidate(address, features)
                    if geoapify_match is not None and geoapify_match.match_result.is_match:
                        updated_at = datetime.now(UTC)
                        if active_db_session is not None:
                            await upsert_pharmacy_coordinate_record(
                                active_db_session,
                                address=address,
                                status="resolved",
                                lat=geoapify_match.resolved_coords[0],
                                lon=geoapify_match.resolved_coords[1],
                                provider="geoapify",
                                query=query_text,
                                matching_key=geoapify_match.match_result.matching_key,
                                match_strategy=geoapify_match.match_result.match_strategy,
                                confidence_tier=geoapify_match.match_result.confidence_tier,
                                updated_at=updated_at,
                            )
                        await set_cached_geocode_record(
                            cache,
                            address,
                            {
                                "status": "resolved",
                                "original_address": address,
                                "lat": geoapify_match.resolved_coords[0],
                                "lon": geoapify_match.resolved_coords[1],
                                "provider": "geoapify",
                                "query": query_text,
                                "match_strategy": geoapify_match.match_result.match_strategy,
                                "confidence_tier": geoapify_match.match_result.confidence_tier,
                                "updated_at": updated_at.isoformat(),
                            },
                            ttl=GEOCODE_RESOLVED_TTL_SECONDS,
                        )
                        return geoapify_match.resolved_coords
                    if geoapify_match is not None and active_db_session is not None:
                        await upsert_pharmacy_coordinate_record(
                            active_db_session,
                            address=address,
                            status="unresolved",
                            provider="geoapify",
                            query=query_text,
                            matching_key=geoapify_match.match_result.matching_key,
                            match_strategy=geoapify_match.match_result.match_strategy,
                            confidence_tier=geoapify_match.match_result.confidence_tier,
                            updated_at=datetime.now(UTC),
                        )
                    logger.info("geocode_provider_fallback address=%r query=%r from=geoapify to=nominatim", address, query_text)

            if await is_provider_in_cooldown(cache, "nominatim"):
                logger.info("geocode_provider_skipped address=%r provider=nominatim reason=cooldown", address)
                updated_at = datetime.now(UTC)
                if active_db_session is not None:
                    await upsert_pharmacy_coordinate_record(
                        active_db_session,
                        address=address,
                        status="rate_limited",
                        provider="nominatim",
                        query=query_text,
                        matching_key=normalize_address_for_matching(address),
                        match_strategy="provider-rate-limited",
                        confidence_tier="low",
                        updated_at=updated_at,
                    )
                await set_cached_geocode_record(
                    cache,
                    address,
                    {
                        "status": "rate_limited",
                        "provider": "nominatim",
                        "query": query_text,
                        "original_address": address,
                        "updated_at": updated_at.isoformat(),
                    },
                    ttl=GEOCODE_RATE_LIMITED_TTL_SECONDS,
                )
                return None

            nominatim_params = {
                "q": query_text,
                "format": "jsonv2",
                "limit": 5,
                "countrycodes": "ru",
            }
            if near is not None:
                lat, lon = near
                nominatim_params["bounded"] = "1"
                nominatim_params["viewbox"] = f"{lon - 0.1},{lat + 0.18},{lon + 0.1},{lat - 0.18}"

            response = await active_client.get(
                "https://nominatim.openstreetmap.org/search",
                params=nominatim_params,
            )
            if response.status_code == 429:
                logger.warning("geocode_provider_rate_limited provider=nominatim address=%r query=%r", address, query_text)
                cooldown_seconds = settings.geocode_provider_cooldown_seconds
                updated_at = datetime.now(UTC)
                await set_provider_cooldown(cache, "nominatim", ttl=cooldown_seconds)
                if active_db_session is not None:
                    await upsert_pharmacy_coordinate_record(
                        active_db_session,
                        address=address,
                        status="rate_limited",
                        provider="nominatim",
                        query=query_text,
                        matching_key=normalize_address_for_matching(address),
                        match_strategy="provider-rate-limited",
                        confidence_tier="low",
                        updated_at=updated_at,
                    )
                await set_cached_geocode_record(
                    cache,
                    address,
                    {
                        "status": "rate_limited",
                        "provider": "nominatim",
                        "query": query_text,
                        "updated_at": updated_at.isoformat(),
                    },
                    ttl=cooldown_seconds,
                )
                return None
            response.raise_for_status()
            payload = response.json()
            logger.info(
                "geocode_provider_response provider=nominatim address=%r query=%r candidates=%d",
                address,
                query_text,
                len(payload),
            )
            nominatim_match = pick_matching_nominatim_candidate(address, payload)
            if nominatim_match is not None and nominatim_match.match_result.is_match:
                updated_at = datetime.now(UTC)
                if active_db_session is not None:
                    await upsert_pharmacy_coordinate_record(
                        active_db_session,
                        address=address,
                        status="resolved",
                        lat=nominatim_match.resolved_coords[0],
                        lon=nominatim_match.resolved_coords[1],
                        provider="nominatim",
                        query=query_text,
                        matching_key=nominatim_match.match_result.matching_key,
                        match_strategy=nominatim_match.match_result.match_strategy,
                        confidence_tier=nominatim_match.match_result.confidence_tier,
                        updated_at=updated_at,
                    )
                await set_cached_geocode_record(
                    cache,
                    address,
                    {
                        "status": "resolved",
                        "original_address": address,
                        "lat": nominatim_match.resolved_coords[0],
                        "lon": nominatim_match.resolved_coords[1],
                        "provider": "nominatim",
                        "query": query_text,
                        "match_strategy": nominatim_match.match_result.match_strategy,
                        "confidence_tier": nominatim_match.match_result.confidence_tier,
                        "updated_at": updated_at.isoformat(),
                    },
                    ttl=GEOCODE_RESOLVED_TTL_SECONDS,
                )
                return nominatim_match.resolved_coords
            if nominatim_match is not None and active_db_session is not None:
                await upsert_pharmacy_coordinate_record(
                    active_db_session,
                    address=address,
                    status="unresolved",
                    provider="nominatim",
                    query=query_text,
                    matching_key=nominatim_match.match_result.matching_key,
                    match_strategy=nominatim_match.match_result.match_strategy,
                    confidence_tier=nominatim_match.match_result.confidence_tier,
                    updated_at=datetime.now(UTC),
                )

            if settings.yandex_geocoder_api_key:
                if not await try_acquire_geocode_provider_quota(
                    cache,
                    "yandex",
                    daily_limit=settings.geocode_provider_daily_request_limit,
                    safety_buffer=settings.geocode_provider_daily_safety_buffer,
                ):
                    logger.warning("geocode_provider_quota_exhausted provider=yandex address=%r", address)
                    continue
                yandex_response = await active_client.get(
                    "https://geocode-maps.yandex.ru/v1/",
                    params={
                        "apikey": settings.yandex_geocoder_api_key,
                        "geocode": query_text,
                        "format": "json",
                        "results": 5,
                    },
                )
                yandex_response.raise_for_status()
                yandex_payload = yandex_response.json()
                yandex_match = pick_matching_yandex_candidate(address, yandex_payload)
                if yandex_match is not None and yandex_match.match_result.is_match:
                    updated_at = datetime.now(UTC)
                    if active_db_session is not None:
                        await upsert_pharmacy_coordinate_record(
                            active_db_session,
                            address=address,
                            status="resolved",
                            lat=yandex_match.resolved_coords[0],
                            lon=yandex_match.resolved_coords[1],
                            provider="yandex",
                            query=query_text,
                            matching_key=yandex_match.match_result.matching_key,
                            match_strategy=yandex_match.match_result.match_strategy,
                            confidence_tier=yandex_match.match_result.confidence_tier,
                            updated_at=updated_at,
                        )
                    await set_cached_geocode_record(
                        cache,
                        address,
                        {
                            "status": "resolved",
                            "original_address": address,
                            "lat": yandex_match.resolved_coords[0],
                            "lon": yandex_match.resolved_coords[1],
                            "provider": "yandex",
                            "query": query_text,
                            "match_strategy": yandex_match.match_result.match_strategy,
                            "confidence_tier": yandex_match.match_result.confidence_tier,
                            "updated_at": updated_at.isoformat(),
                        },
                        ttl=GEOCODE_RESOLVED_TTL_SECONDS,
                    )
                    return yandex_match.resolved_coords
                if yandex_match is not None and active_db_session is not None:
                    await upsert_pharmacy_coordinate_record(
                        active_db_session,
                        address=address,
                        status="unresolved",
                        provider="yandex",
                        query=query_text,
                        matching_key=yandex_match.match_result.matching_key,
                        match_strategy=yandex_match.match_result.match_strategy,
                        confidence_tier=yandex_match.match_result.confidence_tier,
                        updated_at=datetime.now(UTC),
                    )

        updated_at = datetime.now(UTC)
        if active_db_session is not None:
            await upsert_pharmacy_coordinate_record(
                active_db_session,
                address=address,
                status="unresolved",
                query=query_variants[-1] if query_variants else None,
                matching_key=normalize_address_for_matching(address),
                match_strategy="no-match",
                confidence_tier="none",
                updated_at=updated_at,
            )
        await set_cached_geocode_record(
            cache,
            address,
            {
                "status": "unresolved",
                "reason": "no-match",
                "original_address": address,
                "updated_at": updated_at.isoformat(),
            },
            ttl=GEOCODE_UNRESOLVED_TTL_SECONDS,
        )
        return None
    finally:
        if owns_db_session:
            await active_db_session.close()
        if owns_client:
            await active_client.aclose()


def _parse_updated_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return datetime.fromisoformat(value)


def pick_matching_nominatim_candidate(
    requested_address: str,
    payload: list[dict],
) -> GeocodeCandidateSelection | None:
    best_weak_match: GeocodeCandidateSelection | None = None

    for candidate in payload:
        try:
            lat = float(candidate["lat"])
            lon = float(candidate["lon"])
        except (KeyError, TypeError, ValueError):
            logger.info("geocode_candidate_rejected address=%r reason=invalid-coordinates candidate=%r", requested_address, candidate)
            continue

        if not is_within_rostov_region(lat, lon):
            logger.info(
                "geocode_candidate_rejected address=%r reason=outside-rostov candidate=%r",
                requested_address,
                candidate.get("display_name", ""),
            )
            continue

        display_name = candidate.get("display_name", "")
        match_result = evaluate_address_match(
            expected_address=requested_address,
            candidate_address=display_name,
            default_city="Ростов-на-Дону",
        )
        if match_result.is_match:
            logger.info(
                "geocode_candidate_selected address=%r provider=nominatim candidate=%r coords=(%s,%s)",
                requested_address,
                display_name,
                lat,
                lon,
            )
            return GeocodeCandidateSelection(resolved_coords=(lat, lon), match_result=match_result)
        if best_weak_match is None and match_result.confidence_tier == "low":
            best_weak_match = GeocodeCandidateSelection(resolved_coords=None, match_result=match_result)
        logger.info(
            "geocode_candidate_rejected address=%r reason=address-mismatch candidate=%r",
            requested_address,
            display_name,
        )

    if best_weak_match is not None:
        logger.info("geocode_weak_match address=%r provider=nominatim strategy=%s", requested_address, best_weak_match.match_result.match_strategy)
        return best_weak_match
    logger.info("geocode_no_match address=%r provider=nominatim", requested_address)
    return None


def pick_matching_geoapify_candidate(
    requested_address: str,
    features: list[dict],
) -> GeocodeCandidateSelection | None:
    best_weak_match: GeocodeCandidateSelection | None = None

    for feature in features:
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        if len(coordinates) != 2:
            logger.info("geocode_candidate_rejected address=%r reason=invalid-coordinates candidate=%r", requested_address, feature)
            continue

        lon, lat = coordinates
        if not is_within_rostov_region(lat, lon):
            logger.info(
                "geocode_candidate_rejected address=%r reason=outside-rostov candidate=%r",
                requested_address,
                feature.get("properties", {}).get("formatted", ""),
            )
            continue

        properties = feature.get("properties", {})
        formatted = " ".join(
            part for part in [
                properties.get("formatted", ""),
                properties.get("street", ""),
                properties.get("housenumber", ""),
            ] if part
        )
        match_result = evaluate_address_match(
            expected_address=requested_address,
            candidate_address=formatted,
            default_city="Ростов-на-Дону",
        )
        if match_result.is_match:
            logger.info(
                "geocode_candidate_selected address=%r provider=geoapify candidate=%r coords=(%s,%s)",
                requested_address,
                formatted,
                lat,
                lon,
            )
            return GeocodeCandidateSelection(resolved_coords=(lat, lon), match_result=match_result)
        if best_weak_match is None and match_result.confidence_tier == "low":
            best_weak_match = GeocodeCandidateSelection(resolved_coords=None, match_result=match_result)
        logger.info(
            "geocode_candidate_rejected address=%r reason=address-mismatch candidate=%r",
            requested_address,
            formatted,
        )

    if best_weak_match is not None:
        logger.info("geocode_weak_match address=%r provider=geoapify strategy=%s", requested_address, best_weak_match.match_result.match_strategy)
        return best_weak_match
    logger.info("geocode_no_match address=%r provider=geoapify", requested_address)
    return None


def pick_matching_yandex_candidate(
    requested_address: str,
    payload: dict,
) -> GeocodeCandidateSelection | None:
    best_weak_match: GeocodeCandidateSelection | None = None
    features = (
        payload.get("response", {})
        .get("GeoObjectCollection", {})
        .get("featureMember", [])
    )

    for feature in features:
        geo_object = feature.get("GeoObject", {})
        formatted = (
            geo_object.get("metaDataProperty", {})
            .get("GeocoderMetaData", {})
            .get("text", "")
        )
        point = geo_object.get("Point", {}).get("pos", "")
        parts = point.split()
        if len(parts) != 2:
            logger.info("geocode_candidate_rejected address=%r reason=invalid-coordinates candidate=%r", requested_address, feature)
            continue

        try:
            lon = float(parts[0])
            lat = float(parts[1])
        except ValueError:
            logger.info("geocode_candidate_rejected address=%r reason=invalid-coordinates candidate=%r", requested_address, feature)
            continue

        if not is_within_rostov_region(lat, lon):
            logger.info(
                "geocode_candidate_rejected address=%r reason=outside-rostov candidate=%r",
                requested_address,
                formatted,
            )
            continue

        match_result = evaluate_address_match(
            expected_address=requested_address,
            candidate_address=formatted,
            default_city="Ростов-на-Дону",
        )
        if match_result.is_match:
            logger.info(
                "geocode_candidate_selected address=%r provider=yandex candidate=%r coords=(%s,%s)",
                requested_address,
                formatted,
                lat,
                lon,
            )
            return GeocodeCandidateSelection(resolved_coords=(lat, lon), match_result=match_result)
        if best_weak_match is None and match_result.confidence_tier == "low":
            best_weak_match = GeocodeCandidateSelection(resolved_coords=None, match_result=match_result)

    if best_weak_match is not None:
        logger.info("geocode_weak_match address=%r provider=yandex strategy=%s", requested_address, best_weak_match.match_result.match_strategy)
        return best_weak_match
    logger.info("geocode_no_match address=%r provider=yandex", requested_address)
    return None
