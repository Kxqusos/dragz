import asyncio
from datetime import UTC, datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import create_redis_client
from app.core.config import Settings
from app.db.dependencies import get_session_factory
from app.db.models import PharmacyCoordinate
from app.services.geocoding import geocode_address
from app.services.pharmacy_coordinates import list_due_pharmacy_coordinates

logger = logging.getLogger(__name__)


def is_refresh_window_open(
    now: datetime,
    *,
    timezone_name: str,
    window_start: str,
    window_end: str,
) -> bool:
    local_now = now.astimezone(ZoneInfo(timezone_name))
    start_hour, start_minute = [int(part) for part in window_start.split(":", 1)]
    end_hour, end_minute = [int(part) for part in window_end.split(":", 1)]
    local_time = (local_now.hour, local_now.minute)
    start = (start_hour, start_minute)
    end = (end_hour, end_minute)

    if start <= end:
        return start <= local_time <= end

    return local_time >= start or local_time <= end


def record_is_due_for_refresh(
    record: dict,
    *,
    now: datetime,
    resolved_interval_hours: int,
    unresolved_interval_hours: int,
    cooldown_seconds: int,
) -> bool:
    updated_at_raw = record.get("updated_at")
    if not isinstance(updated_at_raw, str):
        return True

    updated_at = datetime.fromisoformat(updated_at_raw)
    status = record.get("status")

    if status == "rate_limited":
        return updated_at + timedelta(seconds=cooldown_seconds) <= now
    if status == "resolved":
        return updated_at + timedelta(hours=resolved_interval_hours) <= now

    return updated_at + timedelta(hours=unresolved_interval_hours) <= now


async def refresh_passive_geocodes(
    cache: Redis | None,
    settings: Settings,
    *,
    db_session: AsyncSession | None = None,
    geocode=geocode_address,
    now: datetime | None = None,
) -> dict[str, int]:
    current_time = now or datetime.now(UTC)
    if not is_refresh_window_open(
        current_time,
        timezone_name=settings.geocode_refresh_timezone,
        window_start=settings.geocode_refresh_window_start,
        window_end=settings.geocode_refresh_window_end,
    ):
        logger.info("refresh_geocode_job_skip_outside_window now=%s", current_time.isoformat())
        return {"scanned": 0, "selected": 0, "refreshed": 0}

    logger.info("refresh_geocode_job_start now=%s", current_time.isoformat())
    scanned = 0
    selected = 0
    refreshed = 0

    if db_session is None:
        logger.info("refresh_geocode_job_skip_missing_db_session")
        return {"scanned": 0, "selected": 0, "refreshed": 0}

    all_records_result = await db_session.execute(
        select(PharmacyCoordinate).order_by(
            PharmacyCoordinate.updated_at.asc(),
            PharmacyCoordinate.id.asc(),
        )
    )
    all_records = all_records_result.scalars().all()
    scanned = len(all_records)

    due_records = await list_due_pharmacy_coordinates(
        db_session,
        now=current_time,
        resolved_interval_hours=settings.geocode_refresh_interval_hours,
        unresolved_interval_hours=settings.geocode_unresolved_refresh_interval_hours,
        cooldown_seconds=settings.geocode_provider_cooldown_seconds,
        limit=settings.geocode_refresh_batch_size,
    )

    for record in due_records:
        original_address = record.original_address
        if not original_address:
            continue

        selected += 1
        coords = await geocode(
            original_address,
            settings,
            cache=cache,
            db_session=db_session,
            force_refresh=True,
        )
        if coords is not None:
            refreshed += 1

    logger.info(
        "refresh_geocode_job_complete scanned=%d selected=%d refreshed=%d",
        scanned,
        selected,
        refreshed,
    )
    return {"scanned": scanned, "selected": selected, "refreshed": refreshed}


async def main() -> None:
    settings = Settings()
    cache = create_redis_client(settings.redis_url)
    async with get_session_factory()() as session:
        await refresh_passive_geocodes(cache, settings, db_session=session)


if __name__ == "__main__":
    asyncio.run(main())
