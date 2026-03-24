import type { DrugSuggestion, PharmacyOffer, RouteStop } from "@/lib/mvp/types";

export const demoSuggestions: DrugSuggestion[] = [
  {
    id: "ibuprofen-200",
    title: "Ибупрофен 200 мг",
    kind: "drug",
    confidence: 0.92,
    rationale: "Частый безрецептурный вариант при головной боли."
  },
  {
    id: "paracetamol-500",
    title: "Парацетамол 500 мг",
    kind: "drug",
    confidence: 0.84,
    rationale: "Подходит как базовый вариант при боли и температуре."
  }
];

export const demoOffers: PharmacyOffer[] = [
  {
    pharmacyId: "neo-proletarskaya",
    pharmacyName: "Неофарм Пролетарская",
    address: "Ростов-на-Дону, Пролетарская ул., 14",
    lat: 47.224,
    lon: 39.723,
    price: 129,
    inStock: true,
    quantityLabel: "14 упаковок",
    matchedDrug: "Ибупрофен 200 мг"
  },
  {
    pharmacyId: "stolichki-taganskaya",
    pharmacyName: "Столички Таганская",
    address: "Ростов-на-Дону, Таганская ул., 22",
    lat: 47.229,
    lon: 39.731,
    price: 133,
    inStock: true,
    quantityLabel: "9 упаковок",
    matchedDrug: "Ибупрофен 200 мг"
  },
  {
    pharmacyId: "gorzdrav-marksistskaya",
    pharmacyName: "Горздрав Марксистская",
    address: "Ростов-на-Дону, Марксистская ул., 9",
    lat: 47.231,
    lon: 39.735,
    price: 145,
    inStock: true,
    quantityLabel: "2 упаковки",
    matchedDrug: "Ибупрофен 200 мг"
  }
];

export type RoutePreview = {
  totalDurationMinutes: number;
  totalDistanceKm: number;
  orderedStops: RouteStop[];
};
