import { z } from "zod";
import type { DrugSuggestion } from "@/lib/mvp/types";

const suggestionSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  kind: z.enum(["drug", "symptom"]),
  confidence: z.number().min(0).max(1),
  rationale: z.string().min(1)
});

const suggestionsPayloadSchema = z.object({
  suggestions: z.array(suggestionSchema)
});

type BuildSuggestionPromptArgs = {
  query: string;
  locale: string;
};

type CallOpenRouterArgs = {
  apiKey: string;
  model: string;
  query: string;
  locale: string;
  baseUrl?: string;
  fetchImpl?: typeof fetch;
};

export function buildSuggestionPrompt({
  query,
  locale
}: BuildSuggestionPromptArgs): string {
  return [
    `Locale: ${locale}`,
    "Return JSON only.",
    'Use the shape {"suggestions":[{"id":"...","title":"...","kind":"drug","confidence":0.0,"rationale":"..."}]}.',
    "Suggest OTC-friendly drug names or exact market names that are useful for the user query.",
    "Do not invent prices, pharmacies, or inventory.",
    `User query: ${query}`
  ].join("\n");
}

export function normalizeOpenRouterSuggestions(input: unknown): DrugSuggestion[] {
  return suggestionsPayloadSchema.parse(input).suggestions;
}

export async function callOpenRouter({
  apiKey,
  model,
  query,
  locale,
  baseUrl = "https://openrouter.ai/api/v1",
  fetchImpl = fetch
}: CallOpenRouterArgs): Promise<DrugSuggestion[]> {
  const response = await fetchImpl(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "user",
          content: buildSuggestionPrompt({ query, locale })
        }
      ]
    })
  });

  if (!response.ok) {
    throw new Error(`OpenRouter request failed with status ${response.status}`);
  }

  const payload = (await response.json()) as {
    choices?: Array<{
      message?: {
        content?: string;
      };
    }>;
  };

  const content = payload.choices?.[0]?.message?.content;

  if (!content) {
    throw new Error("OpenRouter response did not include message content");
  }

  return normalizeOpenRouterSuggestions(JSON.parse(content));
}
