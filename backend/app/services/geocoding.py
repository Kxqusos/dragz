import httpx
import re
import logging
from redis.asyncio import Redis
from datetime import UTC, datetime

from app.core.config import Settings
from app.services.cache import (
    get_cached_geocode_record,
    is_provider_in_cooldown,
    set_cached_geocode_record,
    set_provider_cooldown,
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


def normalize_address_for_geocoding(address: str) -> str:
    normalized = address.replace("_", " ").strip()
    if "ростов" in normalized.lower():
        return normalized
    return f"Ростов-на-Дону, {normalized}"


def build_geocode_queries(address: str) -> list[str]:
    base = normalize_address_for_geocoding(address)
    cleaned = re.sub(r"\([^)]*\)", "", base)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    expanded = cleaned
    expanded = re.sub(r"\bул\.\s*", "улица ", expanded, flags=re.IGNORECASE)
    expanded = re.sub(r"\bпр\.\s*", "проспект ", expanded, flags=re.IGNORECASE)
    expanded = re.sub(r"\bпер\.\s*", "переулок ", expanded, flags=re.IGNORECASE)
    expanded = re.sub(r"\bбул\.\s*", "бульвар ", expanded, flags=re.IGNORECASE)
    expanded = re.sub(r",\s*", ", ", expanded)
    expanded = re.sub(r"(\d)\s*([А-Яа-яA-Za-z])\b", r"\1\2", expanded)
    shortened = re.sub(r"Ростов-на-Дону,\s*", "", expanded)
    shortened = re.sub(r"\b(улица|проспект|переулок|бульвар)\s+", "", shortened, flags=re.IGNORECASE)
    shortened = re.sub(r",\s*", " ", shortened)
    shortened = re.sub(r"\s+", " ", shortened).strip()

    queries: list[str] = []
    for candidate in (base, cleaned, expanded, f"Ростов-на-Дону, {shortened}" if shortened else ""):
        if candidate and candidate not in queries:
            queries.append(candidate)

    return queries


def normalize_address_for_matching(address: str) -> str:
    normalized = normalize_address_for_geocoding(address)
    normalized = re.sub(r"\([^)]*\)", "", normalized)
    normalized = normalized.lower().replace("ё", "е")
    normalized = re.sub(r"(\d+)-(?=[a-zа-я])", r"\1 ", normalized)
    normalized = re.sub(r"(\d+)[-\s]?(й|я|яй|ой)\b", r"\1", normalized)
    normalized = re.sub(r"\b(ул|улица|пр|проспект|пер|переулок|бул|бульвар|пл|площадь)\.?\b", " ", normalized)
    normalized = re.sub(r"[^a-zа-я0-9/ -]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


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
    client: httpx.AsyncClient | None = None,
    force_refresh: bool = False,
) -> tuple[float, float] | None:
    owns_client = client is None
    active_client = client or httpx.AsyncClient(
        timeout=6.0,
        headers={"User-Agent": f"{settings.app_name}/1.0"},
    )
    query_variants = build_geocode_queries(address)
    logger.info("geocode_start address=%r queries=%s near=%s", address, query_variants, near)

    cached_record = None if force_refresh else await get_cached_geocode_record(cache, address)
    if cached_record is not None:
        logger.info("geocode_cache_hit address=%r status=%s", address, cached_record.get("status"))
        if cached_record.get("status") == "resolved":
            lat = cached_record.get("lat")
            lon = cached_record.get("lon")
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                return (float(lat), float(lon))
        return None
    logger.info("geocode_cache_miss address=%r", address)

    try:
        for query_text in query_variants:
            if settings.geoapify_api_key:
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
                if geoapify_match is not None:
                    await set_cached_geocode_record(
                        cache,
                        address,
                        {
                            "status": "resolved",
                            "original_address": address,
                            "lat": geoapify_match[0],
                            "lon": geoapify_match[1],
                            "provider": "geoapify",
                            "query": query_text,
                            "updated_at": datetime.now(UTC).isoformat(),
                        },
                        ttl=GEOCODE_RESOLVED_TTL_SECONDS,
                    )
                    return geoapify_match
                logger.info("geocode_provider_fallback address=%r query=%r from=geoapify to=nominatim", address, query_text)

            if await is_provider_in_cooldown(cache, "nominatim"):
                logger.info("geocode_provider_skipped address=%r provider=nominatim reason=cooldown", address)
                await set_cached_geocode_record(
                    cache,
                    address,
                    {
                        "status": "rate_limited",
                        "provider": "nominatim",
                        "query": query_text,
                        "original_address": address,
                        "updated_at": datetime.now(UTC).isoformat(),
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
                await set_provider_cooldown(cache, "nominatim", ttl=cooldown_seconds)
                await set_cached_geocode_record(
                    cache,
                    address,
                    {"status": "rate_limited", "provider": "nominatim", "query": query_text},
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
            if nominatim_match is not None:
                await set_cached_geocode_record(
                    cache,
                    address,
                    {
                        "status": "resolved",
                        "original_address": address,
                        "lat": nominatim_match[0],
                        "lon": nominatim_match[1],
                        "provider": "nominatim",
                        "query": query_text,
                        "updated_at": datetime.now(UTC).isoformat(),
                    },
                    ttl=GEOCODE_RESOLVED_TTL_SECONDS,
                )
                return nominatim_match

        await set_cached_geocode_record(
            cache,
            address,
            {
                "status": "unresolved",
                "reason": "no-match",
                "original_address": address,
                "updated_at": datetime.now(UTC).isoformat(),
            },
            ttl=GEOCODE_UNRESOLVED_TTL_SECONDS,
        )
        return None
    finally:
        if owns_client:
            await active_client.aclose()


def pick_matching_nominatim_candidate(
    requested_address: str,
    payload: list[dict],
) -> tuple[float, float] | None:
    expected_street, expected_house = extract_address_parts(requested_address)

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
        if address_parts_match(display_name, expected_street, expected_house):
            logger.info(
                "geocode_candidate_selected address=%r provider=nominatim candidate=%r coords=(%s,%s)",
                requested_address,
                display_name,
                lat,
                lon,
            )
            return (lat, lon)
        logger.info(
            "geocode_candidate_rejected address=%r reason=address-mismatch candidate=%r",
            requested_address,
            display_name,
        )

    logger.info("geocode_no_match address=%r provider=nominatim", requested_address)
    return None


def pick_matching_geoapify_candidate(
    requested_address: str,
    features: list[dict],
) -> tuple[float, float] | None:
    expected_street, expected_house = extract_address_parts(requested_address)

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
        if address_parts_match(formatted, expected_street, expected_house):
            logger.info(
                "geocode_candidate_selected address=%r provider=geoapify candidate=%r coords=(%s,%s)",
                requested_address,
                formatted,
                lat,
                lon,
            )
            return (lat, lon)
        logger.info(
            "geocode_candidate_rejected address=%r reason=address-mismatch candidate=%r",
            requested_address,
            formatted,
        )

    logger.info("geocode_no_match address=%r provider=geoapify", requested_address)
    return None


def extract_address_parts(address: str) -> tuple[str, str]:
    normalized = normalize_address_for_matching(address)
    house_matches = re.findall(r"\b(\d+[a-zа-я0-9/-]*)\b", normalized)
    house = house_matches[-1] if house_matches else ""
    street_part = re.sub(rf"\b{re.escape(house)}\b(?!.*\b{re.escape(house)}\b)", " ", normalized).strip() if house else normalized
    street_part = re.sub(r"\b(ростов на дону|рядом|возле|напротив|ост)\b", " ", street_part)
    street_part = re.sub(r"\s+", " ", street_part).strip()
    street = street_part.split(",")[0].strip() if "," in street_part else street_part
    return street, house


def address_parts_match(candidate_address: str, expected_street: str, expected_house: str) -> bool:
    if not candidate_address:
        return True

    normalized_candidate = normalize_address_for_matching(candidate_address)

    if expected_street and expected_street not in normalized_candidate:
        return False

    if expected_house and expected_house not in normalized_candidate:
        return False

    return True
