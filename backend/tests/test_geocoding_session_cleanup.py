import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import Settings
from app.services import geocoding


@dataclass
class _ResolvedRecord:
    status: str
    lat: float
    lon: float
    provider: str | None
    query: str | None
    updated_at: datetime


class _FakeSession:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def test_geocode_closes_owned_session_on_early_db_return(monkeypatch):
    created_sessions: list[_FakeSession] = []

    def fake_session_factory():
        def build_session():
            session = _FakeSession()
            created_sessions.append(session)
            return session

        return build_session

    async def fake_get_record(session, address):
        return _ResolvedRecord(
            status="resolved",
            lat=47.222,
            lon=39.711,
            provider="geoapify",
            query="Ростов-на-Дону, ул. Пушкинская, 10",
            updated_at=datetime.now(UTC),
        )

    async def fake_set_cached_record(cache, address, record, *, ttl):
        return None

    monkeypatch.setattr(geocoding, "get_session_factory", fake_session_factory)
    monkeypatch.setattr(geocoding, "get_pharmacy_coordinate_record", fake_get_record)
    monkeypatch.setattr(geocoding, "set_cached_geocode_record", fake_set_cached_record)

    async def scenario():
        result = await geocoding.geocode_address(
            "ул. Пушкинская, 10",
            Settings(),
            cache=None,
            db_session=None,
        )

        assert result == (47.222, 39.711)
        assert len(created_sessions) == 1
        assert created_sessions[0].closed is True

    asyncio.run(scenario())
