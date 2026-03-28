from fastapi import APIRouter, HTTPException
import logging

from app.cache.redis import create_redis_client
from app.core.config import Settings
from app.schemas import RouteRequest
from app.services.route_planner import build_route_with_roads


router = APIRouter(prefix="/api/route", tags=["route"])
settings = Settings()
redis_client = create_redis_client(settings.redis_url)
logger = logging.getLogger(__name__)


@router.post("")
async def route(payload: RouteRequest):
    if len(payload.pharmacies) < 1:
        raise HTTPException(status_code=400, detail="at least one pharmacy is required")

    logger.info(
        "route_request origin=(%s,%s) pharmacy_count=%d",
        payload.origin.lat,
        payload.origin.lon,
        len(payload.pharmacies),
    )
    result = await build_route_with_roads((payload.origin.lat, payload.origin.lon), payload.pharmacies, settings, cache=redis_client)
    logger.info(
        "route_response stop_count=%d distance_km=%s duration_min=%s",
        len(result.ordered_stops),
        result.total_distance_km,
        result.total_duration_minutes,
    )
    return result
