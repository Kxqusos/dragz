import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base
from app.services.pharmacy_coordinates import (
    get_persisted_coordinates,
    list_due_pharmacy_coordinates,
    upsert_pharmacy_coordinate_record,
)


async def _prepare_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


def test_upserted_resolved_coordinates_are_persisted_and_reused():
    async def scenario():
        engine, session_factory = await _prepare_session()
        async with session_factory() as session:
            await upsert_pharmacy_coordinate_record(
                session,
                address="ул. Пушкинская, 10",
                status="resolved",
                lat=47.222,
                lon=39.711,
                provider="geoapify",
                query="Ростов-на-Дону, ул. Пушкинская, 10",
                updated_at=datetime.now(UTC),
            )

            coordinates = await get_persisted_coordinates(session, "ул. Пушкинская, 10")
            assert coordinates == (47.222, 39.711)

        await engine.dispose()

    asyncio.run(scenario())


def test_due_records_filter_by_status_and_timestamp():
    async def scenario():
        engine, session_factory = await _prepare_session()
        now = datetime(2026, 3, 28, tzinfo=UTC)

        async with session_factory() as session:
            await upsert_pharmacy_coordinate_record(
                session,
                address="ул. Садовая, 1",
                status="resolved",
                lat=47.1,
                lon=39.7,
                provider="geoapify",
                updated_at=now - timedelta(hours=100),
            )
            await upsert_pharmacy_coordinate_record(
                session,
                address="пр. Буденновский, 2",
                status="unresolved",
                updated_at=now - timedelta(hours=100),
            )
            await upsert_pharmacy_coordinate_record(
                session,
                address="пр. Стачки, 3",
                status="rate_limited",
                updated_at=now - timedelta(seconds=1200),
            )
            await upsert_pharmacy_coordinate_record(
                session,
                address="ул. Чехова, 4",
                status="resolved",
                lat=47.21,
                lon=39.72,
                provider="geoapify",
                updated_at=now - timedelta(hours=1),
            )

            due_records = await list_due_pharmacy_coordinates(
                session,
                now=now,
                resolved_interval_hours=72,
                unresolved_interval_hours=72,
                cooldown_seconds=600,
                limit=10,
            )

            assert [record.original_address for record in due_records] == [
                "ул. Садовая, 1",
                "пр. Буденновский, 2",
                "пр. Стачки, 3",
            ]

        await engine.dispose()

    asyncio.run(scenario())
