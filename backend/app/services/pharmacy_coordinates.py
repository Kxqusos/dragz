from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PharmacyCoordinate
from app.services.cache import normalize_geocode_cache_address


def normalize_pharmacy_coordinate_address(address: str) -> str:
    return normalize_geocode_cache_address(address)


async def get_pharmacy_coordinate_record(
    session: AsyncSession,
    address: str,
) -> PharmacyCoordinate | None:
    normalized_address = normalize_pharmacy_coordinate_address(address)
    result = await session.execute(
        select(PharmacyCoordinate).where(
            PharmacyCoordinate.normalized_address == normalized_address
        )
    )
    return result.scalar_one_or_none()


async def get_persisted_coordinates(
    session: AsyncSession,
    address: str,
) -> tuple[float, float] | None:
    record = await get_pharmacy_coordinate_record(session, address)
    if record is None or record.status != "resolved":
        return None
    if record.lat is None or record.lon is None:
        return None
    return (record.lat, record.lon)


async def upsert_pharmacy_coordinate_record(
    session: AsyncSession,
    *,
    address: str,
    status: str,
    lat: float | None = None,
    lon: float | None = None,
    provider: str | None = None,
    query: str | None = None,
    updated_at: datetime | None = None,
) -> PharmacyCoordinate:
    normalized_address = normalize_pharmacy_coordinate_address(address)
    record = await get_pharmacy_coordinate_record(session, address)

    if record is None:
        record = PharmacyCoordinate(
            normalized_address=normalized_address,
            original_address=address,
            status=status,
            lat=lat,
            lon=lon,
            provider=provider,
            query=query,
            updated_at=updated_at or datetime.now(UTC),
        )
        session.add(record)
    else:
        record.original_address = address
        record.status = status
        record.lat = lat
        record.lon = lon
        record.provider = provider
        record.query = query
        record.updated_at = updated_at or datetime.now(UTC)

    await session.commit()
    await session.refresh(record)
    return record


def pharmacy_coordinate_record_is_due_for_refresh(
    record: PharmacyCoordinate,
    *,
    now: datetime,
    resolved_interval_hours: int,
    unresolved_interval_hours: int,
    cooldown_seconds: int,
) -> bool:
    updated_at = record.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)

    if record.status == "rate_limited":
        return updated_at + timedelta(seconds=cooldown_seconds) <= now
    if record.status == "resolved":
        return updated_at + timedelta(hours=resolved_interval_hours) <= now
    return updated_at + timedelta(hours=unresolved_interval_hours) <= now


async def list_due_pharmacy_coordinates(
    session: AsyncSession,
    *,
    now: datetime,
    resolved_interval_hours: int,
    unresolved_interval_hours: int,
    cooldown_seconds: int,
    limit: int,
) -> list[PharmacyCoordinate]:
    result = await session.execute(
        select(PharmacyCoordinate).order_by(
            PharmacyCoordinate.updated_at.asc(),
            PharmacyCoordinate.id.asc(),
        )
    )
    records = result.scalars().all()

    due_records: list[PharmacyCoordinate] = []
    for record in records:
        if pharmacy_coordinate_record_is_due_for_refresh(
            record,
            now=now,
            resolved_interval_hours=resolved_interval_hours,
            unresolved_interval_hours=unresolved_interval_hours,
            cooldown_seconds=cooldown_seconds,
        ):
            due_records.append(record)
        if len(due_records) >= limit:
            break

    return due_records
