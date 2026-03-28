import asyncio

from app.api.routes import search as search_routes
from app.schemas import PharmacyOffer


def test_bulk_offer_geocoding_does_not_share_request_session(monkeypatch):
    observed_sessions: list[object | None] = []

    async def fake_resolve_offer_list(query: str, *, city_id: str, area_id: str):
        return [
            PharmacyOffer(
                pharmacy_id="1",
                pharmacy_name="Аптека 1",
                address="ул. Пушкинская, 10",
                lat=0,
                lon=0,
                price=100,
                in_stock=True,
                quantity_label="1 шт",
                matched_drug="Ибупрофен",
            ),
            PharmacyOffer(
                pharmacy_id="2",
                pharmacy_name="Аптека 2",
                address="ул. Чехова, 4",
                lat=0,
                lon=0,
                price=120,
                in_stock=True,
                quantity_label="1 шт",
                matched_drug="Ибупрофен",
            ),
        ]

    async def fake_geocode_address(
        address: str,
        settings,
        *,
        near=None,
        cache=None,
        db_session=None,
        client=None,
        force_refresh=False,
    ):
        observed_sessions.append(db_session)
        return (47.22, 39.71)

    monkeypatch.setattr(search_routes, "_resolve_offer_list", fake_resolve_offer_list)
    monkeypatch.setattr(search_routes, "geocode_address", fake_geocode_address)

    async def scenario():
        shared_request_session = object()
        offers = await search_routes._resolve_offer_list_with_geodata(
            "ибупрофен",
            city_id="1",
            area_id="0",
            near=(47.22, 39.71),
            db_session=shared_request_session,
        )

        assert len(offers) == 2
        assert observed_sessions == [None, None]

    asyncio.run(scenario())
