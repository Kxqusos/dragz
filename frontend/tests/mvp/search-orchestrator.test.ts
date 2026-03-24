import { describe, expect, it, vi } from "vitest";
import { runMvpSearch } from "@/lib/server/search-orchestrator";

describe("search orchestrator", () => {
  it("calls the llm for symptom-style queries and returns suggestions", async () => {
    const result = await runMvpSearch(
      {
        query: "Препарат от головной боли",
        cityId: "0",
        areaId: "0"
      },
      {
        suggestDrugs: vi.fn().mockResolvedValue([
          {
            id: "ibuprofen-200",
            title: "Ибупрофен 200 мг",
            kind: "drug",
            confidence: 0.9,
            rationale: "Подходит для симптома головной боли"
          }
        ]),
        searchRef003: vi.fn().mockResolvedValue([])
      }
    );

    expect(result.mode).toBe("suggestions");
    expect(result.suggestions).toHaveLength(1);
    expect(result.offers).toEqual([]);
  });

  it("hits ref003 directly for exact drug queries", async () => {
    const searchRef003 = vi.fn().mockResolvedValue([
      {
        pharmacyId: "ph-1",
        pharmacyName: "Аптека 1",
        address: "Ростов-на-Дону, ул. Тестовая, 1",
        lat: 47.222,
        lon: 39.718,
        price: 129,
        inStock: true,
        quantityLabel: "14 упаковок",
        matchedDrug: "Ибупрофен 200 мг"
      }
    ]);

    const result = await runMvpSearch(
      {
        query: "Ибупрофен 200 мг",
        cityId: "0",
        areaId: "0"
      },
      {
        suggestDrugs: vi.fn(),
        searchRef003
      }
    );

    expect(result.mode).toBe("offers");
    expect(result.suggestions).toEqual([]);
    expect(result.offers).toHaveLength(1);
    expect(searchRef003).toHaveBeenCalledOnce();
  });
});
