import type { PharmacyOffer, RoutePreview } from "@/lib/mvp/types";
import { logUiEvent } from "@/lib/client/logger";
import { getBackendUrl } from "@/lib/api/base-url";

type SearchResponse = {
  offers: PharmacyOffer[];
  warnings: string[];
};

type BackendOffer = {
  pharmacy_id: string;
  pharmacy_name: string;
  address: string;
  lat: number;
  lon: number;
  price: number;
  in_stock: boolean;
  quantity_label: string;
  matched_drug: string;
};

type BackendSearchResponse = {
  suggestions?: unknown[];
  offers: BackendOffer[];
  warnings?: string[];
};

type BackendRouteResponse = {
  total_duration_minutes: number;
  total_distance_km: number;
  ordered_stops: Array<{
    pharmacy_id: string;
    label: string;
    lat: number;
    lon: number;
    order: number;
  }>;
  route_geometry?: Array<[number, number]>;
};

export async function searchBackend(payload: {
  query: string;
  cityId: string;
  areaId: string;
  lat?: number;
  lon?: number;
}): Promise<SearchResponse> {
  logUiEvent("search_backend_request", payload);
  const response = await fetch(`${getBackendUrl()}/api/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logUiEvent("search_backend_error", { status: response.status, payload });
    throw new Error(`Search request failed with status ${response.status}`);
  }

  const data = (await response.json()) as BackendSearchResponse;
  const requestId = readResponseHeader(response, "X-Request-ID");
  logUiEvent("search_backend_response", {
    offers: data.offers.length,
    warnings: data.warnings ?? [],
    requestId
  });

  return {
    offers: data.offers.map((offer) => ({
      pharmacyId: offer.pharmacy_id,
      pharmacyName: offer.pharmacy_name,
      address: offer.address,
      lat: offer.lat,
      lon: offer.lon,
      price: offer.price,
      inStock: offer.in_stock,
      quantityLabel: offer.quantity_label,
      matchedDrug: offer.matched_drug
    })),
    warnings: data.warnings ?? []
  };
}

export async function buildRoute(payload: {
  origin: {
    lat: number;
    lon: number;
  };
  pharmacies: PharmacyOffer[];
}): Promise<RoutePreview> {
  logUiEvent("route_backend_request", {
    origin: payload.origin,
    pharmacyCount: payload.pharmacies.length
  });
  const response = await fetch(`${getBackendUrl()}/api/route`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logUiEvent("route_backend_error", { status: response.status });
    throw new Error(`Route request failed with status ${response.status}`);
  }

  const data = (await response.json()) as BackendRouteResponse;
  const requestId = readResponseHeader(response, "X-Request-ID");
  logUiEvent("route_backend_response", {
    stopCount: data.ordered_stops.length,
    distanceKm: data.total_distance_km,
    durationMinutes: data.total_duration_minutes,
    requestId
  });

  return {
    totalDurationMinutes: data.total_duration_minutes,
    totalDistanceKm: data.total_distance_km,
    orderedStops: data.ordered_stops.map((stop) => ({
      pharmacyId: stop.pharmacy_id,
      label: stop.label,
      lat: stop.lat,
      lon: stop.lon,
      order: stop.order
    })),
    routeGeometry: data.route_geometry ?? []
  };
}

function readResponseHeader(response: Response, headerName: string): string | null {
  const headers = response.headers as Headers | undefined;
  return headers?.get?.(headerName) ?? null;
}
