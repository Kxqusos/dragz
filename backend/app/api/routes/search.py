from fastapi import APIRouter, Depends, HTTPException
from pydantic import AliasChoices, BaseModel, Field
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import create_redis_client
from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.schemas import SearchResponse
from app.services.cache import cached_resolve_offers, cached_suggest_drugs
from app.services.geocoding import geocode_address
from app.services.openrouter import suggest_drugs
from app.services.offer_enrichment import enrich_offers_with_geodata
from app.services.ref003.client import resolve_offers
from app.services.search_flow import run_search_flow, to_pharmacy_offer


router = APIRouter(prefix="/api/search", tags=["search"])
settings = Settings()
redis_client = create_redis_client(settings.redis_url)
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    query: str
    city_id: str = Field(
        default_factory=lambda: settings.default_city_id,
        validation_alias=AliasChoices("city_id", "cityId"),
    )
    area_id: str = Field(
        default_factory=lambda: settings.default_area_id,
        validation_alias=AliasChoices("area_id", "areaId"),
    )
    lat: float | None = None
    lon: float | None = None


@router.post("")
async def search(
    payload: SearchRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    logger.info(
        "search_request query=%r city_id=%s area_id=%s has_location=%s lat=%s lon=%s",
        query,
        payload.city_id,
        payload.area_id,
        payload.lat is not None and payload.lon is not None,
        payload.lat,
        payload.lon,
    )

    normalized = query.lower()
    if (
        "от " in normalized
        or "для " in normalized
        or "головной боли" in normalized
        or "простуды" in normalized
    ):
        suggestions = await cached_suggest_drugs(
            redis_client,
            query,
            lambda search_query: suggest_drugs(search_query, settings),
        )
        if suggestions:
            logger.info("search_response mode=suggestions query=%r count=%d", query, len(suggestions))
            return SearchResponse(mode="suggestions", suggestions=suggestions, offers=[])

    offers = await cached_resolve_offers(
        redis_client,
        query,
        lambda search_query, city_id="0", area_id="0": _resolve_offer_list_with_geodata(
            search_query,
            city_id=city_id,
            area_id=area_id,
            near=(payload.lat, payload.lon) if payload.lat is not None and payload.lon is not None else None,
            db_session=db_session,
        ),
        city_id=payload.city_id,
        area_id=payload.area_id,
    )
    result = run_search_flow(
        query,
        city_id=payload.city_id,
        area_id=payload.area_id,
        resolve_offers=lambda _query, city_id="0", area_id="0": offers,
    )
    logger.info("search_response mode=%s query=%r offers=%d warnings=%s", result.mode, query, len(result.offers), result.warnings)
    return result


async def _resolve_offer_list(query: str, *, city_id: str, area_id: str):
    search_results = await resolve_offers(query, city_id=city_id, area_id=area_id)
    return [to_pharmacy_offer(offer) for offer in search_results.offers]


async def _resolve_offer_list_with_geodata(
    query: str,
    *,
    city_id: str,
    area_id: str,
    near: tuple[float, float] | None = None,
    db_session: AsyncSession | None = None,
):
    offers = await _resolve_offer_list(query, city_id=city_id, area_id=area_id)
    return await enrich_offers_with_geodata(
        offers,
        lambda address: geocode_address(
            address,
            settings,
            near=near,
            cache=redis_client,
        ),
        limit=30,
    )
