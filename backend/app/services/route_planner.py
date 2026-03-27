import httpx
import logging
from redis.asyncio import Redis

from app.core.config import Settings
from app.schemas import RoutePharmacy, RouteResponse, RouteStop
from app.services.geocoding import geocode_address

logger = logging.getLogger(__name__)

def _fallback_route(normalized_stops: list[RouteStop], pharmacy_count: int, valid_coords: list[list[float]]) -> RouteResponse:
    logger.info(
        "route_planner_fallback pharmacy_count=%d stop_count=%d valid_coords=%d",
        pharmacy_count,
        len(normalized_stops),
        len(valid_coords),
    )
    return RouteResponse(
        total_duration_minutes=12 + pharmacy_count * 3,
        total_distance_km=round(2.4 + pharmacy_count * 1.1, 1),
        ordered_stops=normalized_stops,
        route_geometry=valid_coords,
    )


async def build_route_with_roads(
    origin: tuple[float, float],
    pharmacies: list[RoutePharmacy],
    settings: Settings,
    client: httpx.AsyncClient | None = None,
    cache: Redis | None = None,
) -> RouteResponse:
    logger.info("route_planner_start origin=(%s,%s) pharmacy_count=%d", origin[0], origin[1], len(pharmacies))
    normalized_stops: list[RouteStop] = [_build_origin_stop(origin, order=0)]
    normalized_pharmacies: list[RouteStop] = []

    for index, pharmacy in enumerate(pharmacies, start=1):
        lat = pharmacy.lat
        lon = pharmacy.lon
        if (lat == 0 or lon == 0) and pharmacy.address:
            coords = await geocode_address(pharmacy.address, settings, cache=cache)
            if coords is not None:
                lat, lon = coords

        normalized_pharmacies.append(
            RouteStop(
                pharmacy_id=pharmacy.pharmacy_id,
                label=pharmacy.pharmacy_name,
                lat=lat,
                lon=lon,
                order=index,
            )
        )

    normalized_stops.extend(normalized_pharmacies)
    normalized_stops.append(_build_origin_stop(origin, order=len(normalized_stops)))

    valid_coords = [
        [stop.lon, stop.lat]
        for stop in normalized_stops
        if (stop.lat != 0 or stop.lon != 0)
    ]

    if len(valid_coords) < 2 or not settings.geoapify_api_key:
        return _fallback_route(normalized_stops, len(pharmacies), valid_coords)

    try:
        if client is None:
            async with httpx.AsyncClient(timeout=25.0) as owned_client:
                payload = await _request_geoapify_route(owned_client, normalized_stops, settings)
        else:
            payload = await _request_geoapify_route(client, normalized_stops, settings)
    except httpx.HTTPError:
        logger.exception("route_planner_geoapify_error")
        return _fallback_route(normalized_stops, len(pharmacies), valid_coords)

    features = payload.get("features", [])
    if not features:
        logger.info("route_planner_geoapify_empty_features")
        return _fallback_route(normalized_stops, len(pharmacies), valid_coords)

    properties = features[0].get("properties", {})
    geometry = features[0].get("geometry", {})
    coordinates = geometry.get("coordinates", [])
    multiline_geometry = coordinates if geometry.get("type") == "MultiLineString" else [coordinates]
    route_geometry = _flatten_route_geometry(multiline_geometry)

    if len(route_geometry) < 2:
        logger.info("route_planner_geoapify_invalid_geometry")
        return _fallback_route(normalized_stops, len(pharmacies), valid_coords)

    ordered_stops = _order_stops_from_geometry(origin, normalized_pharmacies, multiline_geometry)

    result = RouteResponse(
        total_duration_minutes=round(properties.get("time", 0) / 60),
        total_distance_km=round(properties.get("distance", 0) / 1000, 1),
        ordered_stops=ordered_stops,
        route_geometry=route_geometry,
    )
    logger.info(
        "route_planner_complete stop_count=%d geometry_points=%d distance_km=%s duration_min=%s",
        len(result.ordered_stops),
        len(result.route_geometry),
        result.total_distance_km,
        result.total_duration_minutes,
    )
    return result


async def _request_geoapify_route(
    client: httpx.AsyncClient,
    normalized_stops: list[RouteStop],
    settings: Settings,
) -> dict:
    logger.info("route_planner_geoapify_request stop_count=%d", len(normalized_stops))
    response = await client.get(
                "https://api.geoapify.com/v1/routing",
                params={
                    "waypoints": "|".join(
                        f"{stop.lat},{stop.lon}" for stop in normalized_stops if (stop.lat != 0 or stop.lon != 0)
                    ),
                    "mode": "drive",
                    "details": "route_details",
                    "optimize_stops": "true",
                    "apiKey": settings.geoapify_api_key,
                },
            )
    response.raise_for_status()
    payload = response.json()
    logger.info("route_planner_geoapify_response features=%d", len(payload.get("features", [])))
    return payload


def _build_origin_stop(origin: tuple[float, float], order: int) -> RouteStop:
    return RouteStop(
        pharmacy_id="origin",
        label="Ваше местоположение",
        lat=origin[0],
        lon=origin[1],
        order=order,
    )


def _flatten_route_geometry(multiline_coords: list) -> list[list[float]]:
    flattened: list[list[float]] = []

    for segment in multiline_coords:
        if not isinstance(segment, list):
            continue

        for point in segment:
            if not isinstance(point, list) or len(point) < 2:
                continue

            normalized_point = [point[0], point[1]]
            if flattened and flattened[-1] == normalized_point:
                continue

            flattened.append(normalized_point)

    return flattened


def _order_stops_from_geometry(
    origin: tuple[float, float],
    pharmacies: list[RouteStop],
    multiline_geometry: list[list[list[float]]],
) -> list[RouteStop]:
    remaining = pharmacies.copy()
    ordered_stops = [_build_origin_stop(origin, order=0)]

    for segment in multiline_geometry[:-1]:
        if not segment:
            continue

        endpoint = segment[-1]
        matching_index = _find_nearest_stop_index(endpoint, remaining)
        if matching_index is None:
            continue

        stop = remaining.pop(matching_index)
        ordered_stops.append(
            RouteStop(
                pharmacy_id=stop.pharmacy_id,
                label=stop.label,
                lat=stop.lat,
                lon=stop.lon,
                order=len(ordered_stops),
            )
        )

    ordered_stops.append(_build_origin_stop(origin, order=len(ordered_stops)))
    return ordered_stops


def _find_nearest_stop_index(point: list[float], pharmacies: list[RouteStop]) -> int | None:
    if len(point) < 2 or not pharmacies:
        return None

    best_index: int | None = None
    best_distance = float("inf")

    for index, stop in enumerate(pharmacies):
        distance = (stop.lon - point[0]) ** 2 + (stop.lat - point[1]) ** 2
        if distance < best_distance:
            best_distance = distance
            best_index = index

    return best_index
