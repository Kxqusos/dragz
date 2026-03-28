import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.jobs.refresh_geocodes import refresh_passive_geocodes
from app.services.pharmacy_coordinates import upsert_pharmacy_coordinate_record


def test_refresh_job_uses_database_records_instead_of_redis_scan():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        now = datetime(2026, 3, 29, 1, 0, tzinfo=UTC)
        refreshed_addresses: list[str] = []

        async def fake_geocode(address, settings, *, cache=None, db_session=None, force_refresh=False, near=None, client=None):
            refreshed_addresses.append(address)
            return (47.231, 39.723)

        async with session_factory() as session:
            await upsert_pharmacy_coordinate_record(
                session,
                address="ул. Пушкинская, 10",
                status="resolved",
                lat=47.2,
                lon=39.7,
                provider="geoapify",
                updated_at=now - timedelta(hours=100),
            )
            await upsert_pharmacy_coordinate_record(
                session,
                address="ул. Чехова, 4",
                status="resolved",
                lat=47.3,
                lon=39.8,
                provider="geoapify",
                updated_at=now - timedelta(hours=1),
            )

            settings = Settings(
                geocode_refresh_timezone="Europe/Moscow",
                geocode_refresh_window_start="00:00",
                geocode_refresh_window_end="06:00",
                geocode_refresh_interval_hours=72,
                geocode_unresolved_refresh_interval_hours=72,
                geocode_refresh_batch_size=100,
                geocode_provider_cooldown_seconds=600,
            )

            result = await refresh_passive_geocodes(
                None,
                settings,
                db_session=session,
                geocode=fake_geocode,
                now=now,
            )

            assert result == {"scanned": 2, "selected": 1, "refreshed": 1}
            assert refreshed_addresses == ["ул. Пушкинская, 10"]

        await engine.dispose()

    asyncio.run(scenario())
