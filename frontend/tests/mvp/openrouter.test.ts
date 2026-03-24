import { describe, expect, it } from "vitest";
import {
  buildSuggestionPrompt,
  normalizeOpenRouterSuggestions
} from "@/lib/server/openrouter";

describe("openrouter suggestion flow", () => {
  it("builds a symptom-to-drug prompt with strict json output instructions", () => {
    const prompt = buildSuggestionPrompt({
      query: "Препарат от головной боли",
      locale: "ru-RU"
    });

    expect(prompt).toContain("JSON");
    expect(prompt).toContain("головной боли");
    expect(prompt).toContain("suggestions");
  });

  it("normalizes llm output into ranked suggestions", () => {
    const result = normalizeOpenRouterSuggestions({
      suggestions: [
        {
          id: "ibuprofen-200",
          title: "Ибупрофен 200 мг",
          kind: "drug",
          confidence: 0.9,
          rationale: "Подходит для симптома головной боли"
        }
      ]
    });

    expect(result[0]?.title).toBe("Ибупрофен 200 мг");
    expect(result[0]?.confidence).toBe(0.9);
  });
});
