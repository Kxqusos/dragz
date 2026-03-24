export type DrugSuggestion = {
  id: string;
  title: string;
  kind: "drug" | "symptom";
  confidence: number;
  rationale: string;
};

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

export type RouteStop = {
  pharmacyId: string;
  label: string;
  lat: number;
  lon: number;
  order: number;
};

export function hasRouteableSelection(offers: PharmacyOffer[]): boolean {
  return offers.length >= 2;
}
