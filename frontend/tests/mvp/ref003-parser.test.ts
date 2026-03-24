import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import {
  parseRef003ResultsPage,
  parseRef003SearchPage
} from "@/lib/server/ref003";

const fixturesDir = join(process.cwd(), "lib/mvp/fixtures");

describe("ref003 parser", () => {
  it("extracts search form metadata", () => {
    const html = readFileSync(join(fixturesDir, "ref003-search-page.html"), "utf8");
    const result = parseRef003SearchPage(html);

    expect(result.action).toContain("/index.php/search");
    expect(result.cityFieldName).toBe("city_id");
    expect(result.areaFieldName).toBe("area_id");
    expect(result.drugFieldName).toBe("drugname");
    expect(result.defaultCity.label).toBe("Ростов-на-Дону и область");
  });

  it("returns empty offers and warnings for unstable result pages", () => {
    const html = readFileSync(join(fixturesDir, "ref003-results-page.html"), "utf8");
    const result = parseRef003ResultsPage(html);

    expect(result.offers).toEqual([]);
    expect(result.warnings).toContain("php-notice");
    expect(result.query).toBe("ибупрофен");
  });
});
