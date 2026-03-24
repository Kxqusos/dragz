import type { DrugSuggestion, PharmacyOffer } from "@/lib/mvp/types";

type SearchParams = {
  query: string;
  cityId: string;
  areaId: string;
};

type SearchDependencies = {
  suggestDrugs: (args: SearchParams) => Promise<DrugSuggestion[]>;
  searchRef003: (args: SearchParams & { drugTitle: string }) => Promise<PharmacyOffer[]>;
};

type SearchResult =
  | {
      mode: "suggestions";
      suggestions: DrugSuggestion[];
      offers: PharmacyOffer[];
    }
  | {
      mode: "offers";
      suggestions: DrugSuggestion[];
      offers: PharmacyOffer[];
    };

function looksLikeSymptomQuery(query: string): boolean {
  const normalized = query.toLowerCase();

  return (
    normalized.includes("от ") ||
    normalized.includes("для ") ||
    normalized.includes("головной боли") ||
    normalized.includes("простуды")
  );
}

export async function runMvpSearch(
  params: SearchParams,
  dependencies: SearchDependencies
): Promise<SearchResult> {
  if (looksLikeSymptomQuery(params.query)) {
    const suggestions = await dependencies.suggestDrugs(params);

    return {
      mode: "suggestions",
      suggestions,
      offers: []
    };
  }

  const offers = await dependencies.searchRef003({
    ...params,
    drugTitle: params.query
  });

  return {
    mode: "offers",
    suggestions: [],
    offers
  };
}
