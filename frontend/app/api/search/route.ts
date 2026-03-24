import { NextResponse } from "next/server";
import { demoOffers, demoSuggestions } from "@/lib/mvp/demo";
import { callOpenRouter } from "@/lib/server/openrouter";
import { runMvpSearch } from "@/lib/server/search-orchestrator";

type SearchBody = {
  query?: string;
  cityId?: string;
  areaId?: string;
};

export async function POST(request: Request) {
  const body = (await request.json()) as SearchBody;
  const query = body.query?.trim();

  if (!query) {
    return NextResponse.json({ error: "query is required" }, { status: 400 });
  }

  const result = await runMvpSearch(
    {
      query,
      cityId: body.cityId ?? "0",
      areaId: body.areaId ?? "0"
    },
    {
      suggestDrugs: async ({ query: searchQuery }) => {
        const apiKey = process.env.OPENROUTER_API_KEY;
        const model = process.env.OPENROUTER_MODEL;

        if (!apiKey || !model) {
          return demoSuggestions.filter(
            (suggestion) =>
              searchQuery.toLowerCase().includes("голов") || suggestion.title.includes("Ибупрофен")
          );
        }

        return callOpenRouter({
          apiKey,
          model,
          query: searchQuery,
          locale: "ru-RU"
        });
      },
      searchRef003: async ({ drugTitle }) => {
        return demoOffers.filter((offer) => offer.matchedDrug === drugTitle || drugTitle.includes("Ибупрофен"));
      }
    }
  );

  return NextResponse.json(result);
}
