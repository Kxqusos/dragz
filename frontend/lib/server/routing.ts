import type { PharmacyOffer, RouteStop } from "@/lib/mvp/types";

type MinimalPharmacySelection = Pick<
  PharmacyOffer,
  "pharmacyId" | "pharmacyName" | "lat" | "lon"
>;

type UserLocation = {
  lat: number;
  lon: number;
};

type RouteableSelection = Array<Pick<MinimalPharmacySelection, "pharmacyId">>;

export function shouldBuildRoute(pharmacies: RouteableSelection): boolean {
  return pharmacies.length >= 2;
}

export function buildRouteStops(
  userLocation: UserLocation,
  pharmacies: MinimalPharmacySelection[]
): RouteStop[] {
  return [
    {
      pharmacyId: "origin",
      label: "Ваше местоположение",
      lat: userLocation.lat,
      lon: userLocation.lon,
      order: 0
    },
    ...pharmacies.map((pharmacy, index) => ({
      pharmacyId: pharmacy.pharmacyId,
      label: pharmacy.pharmacyName,
      lat: pharmacy.lat,
      lon: pharmacy.lon,
      order: index + 1
    }))
  ];
}
