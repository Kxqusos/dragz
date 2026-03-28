export type PharmacyOffer = {
  pharmacyId: string;
  pharmacyName: string;
  address: string;
  lat: number;
  lon: number;
  price: number;
  inStock: boolean;
  quantityLabel: string;
  matchedDrug: string;
};

export type CartItem = PharmacyOffer;

export type RouteStop = {
  pharmacyId: string;
  label: string;
  lat: number;
  lon: number;
  order: number;
};

export type RoutePreview = {
  totalDurationMinutes: number;
  totalDistanceKm: number;
  orderedStops: RouteStop[];
  routeGeometry?: Array<[number, number]>;
};

export function getPharmacyGroupKey(offer: Pick<PharmacyOffer, "pharmacyName" | "address">): string {
  return `${offer.pharmacyName}::${offer.address}`;
}

export function getUniquePharmacyCount(offers: PharmacyOffer[]): number {
  return new Set(offers.map((offer) => getPharmacyGroupKey(offer))).size;
}

export function hasRouteableSelection(offers: PharmacyOffer[]): boolean {
  return getUniquePharmacyCount(offers) >= 1;
}
