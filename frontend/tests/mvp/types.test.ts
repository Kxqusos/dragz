import { describe, expect, it } from "vitest";
import {
  hasRouteableSelection,
  type DrugSuggestion,
  type PharmacyOffer,
  type RouteStop
} from "@/lib/mvp/types";

describe("mvp types", () => {
  it("accepts normalized objects for suggestions, offers, and route stops", () => {
    const suggestion: DrugSuggestion = {
      id: "ibuprofen-200",
      title: "Ибупрофен 200 мг",
      kind: "drug",
      confidence: 0.92,
      rationale: "Подходит для симптома головной боли"
    };

    const offer: PharmacyOffer = {
      pharmacyId: "ph-1",
      pharmacyName: "Аптека 1",
      address: "Ростов-на-Дону, ул. Тестовая, 1",
      lat: 47.222,
      lon: 39.718,
      price: 129,
      inStock: true,
      quantityLabel: "14 упаковок",
      matchedDrug: "Ибупрофен 200 мг"
    };

    const stop: RouteStop = {
      pharmacyId: "ph-1",
      label: "Аптека 1",
      lat: 47.222,
      lon: 39.718,
      order: 0
    };

    expect(suggestion.kind).toBe("drug");
    expect(offer.price).toBe(129);
    expect(stop.order).toBe(0);
    expect(hasRouteableSelection([offer])).toBe(false);
    expect(hasRouteableSelection([offer, { ...offer, pharmacyId: "ph-2" }])).toBe(true);
  });
});
