from app.schemas import PharmacyOffer, RouteResponse, RouteStop


def build_route(origin: tuple[float, float], pharmacies: list[PharmacyOffer]) -> RouteResponse:
    ordered_stops = [
        RouteStop(
            pharmacy_id="origin",
            label="Ваше местоположение",
            lat=origin[0],
            lon=origin[1],
            order=0,
        ),
        *[
            RouteStop(
                pharmacy_id=pharmacy.pharmacy_id,
                label=pharmacy.pharmacy_name,
                lat=pharmacy.lat,
                lon=pharmacy.lon,
                order=index + 1,
            )
            for index, pharmacy in enumerate(pharmacies)
        ],
    ]
    return RouteResponse(
        total_duration_minutes=12 + len(pharmacies) * 3,
        total_distance_km=round(2.4 + len(pharmacies) * 1.1, 1),
        ordered_stops=ordered_stops,
    )
