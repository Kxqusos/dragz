# MVP Drug Route Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MVP flow where the user shares geolocation, searches with natural language or exact drug names, gets LLM-assisted drug suggestions, selects items into a list, sees matching pharmacies from `ref003`, and receives the fastest route when two or more pharmacies are relevant.

**Architecture:** Keep the browser thin and move all unstable integration logic server-side. The Next.js app should call internal route handlers for `search`, `route`, and `geolocate`, while the server handles `ref003` scraping, OpenRouter calls, normalization, ranking, and routing-provider orchestration. Treat `ref003` HTML as an unstable external dependency and build parser tests from saved fixtures so the UI can evolve without hitting the live site.

**Tech Stack:** Next.js App Router, React 19, TypeScript, Vitest, Testing Library, server-side HTML parsing with `cheerio`, OpenRouter HTTP API, MapLibre GL JS, Geoapify geocoding/routing APIs, browser geolocation API.

### Task 1: Define MVP domain contracts and fixtures

**Files:**
- Create: `frontend/lib/mvp/types.ts`
- Create: `frontend/lib/mvp/fixtures/ref003-search-page.html`
- Create: `frontend/lib/mvp/fixtures/ref003-results-page.html`
- Create: `frontend/lib/mvp/fixtures/openrouter-suggestion.json`
- Create: `frontend/tests/mvp/types.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import type { DrugSuggestion, PharmacyOffer, RouteStop } from "@/lib/mvp/types";

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
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/mvp/types.test.ts`

Expected: FAIL because `@/lib/mvp/types` does not exist.

**Step 3: Write minimal implementation**

```ts
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
```

**Step 4: Save realistic fixtures**

- Save one raw `ref003` search page fixture from the browser.
- Save one raw `ref003` results page fixture after searching a real drug.
- Save one representative OpenRouter JSON response fixture for symptom-to-drug suggestions.

**Step 5: Run test to verify it passes**

Run: `npm test -- tests/mvp/types.test.ts`

Expected: PASS

**Step 6: Commit**

```bash
git add lib/mvp/types.ts lib/mvp/fixtures tests/mvp/types.test.ts
git commit -m "feat: add mvp domain contracts"
```

### Task 2: Add `ref003` parser with fixture-backed tests

**Files:**
- Create: `frontend/lib/server/ref003.ts`
- Create: `frontend/tests/mvp/ref003-parser.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parseRef003SearchPage, parseRef003ResultsPage } from "@/lib/server/ref003";

describe("ref003 parser", () => {
  it("extracts search form metadata", () => {
    const html = readFileSync(join(process.cwd(), "lib/mvp/fixtures/ref003-search-page.html"), "utf8");
    const result = parseRef003SearchPage(html);

    expect(result.action).toContain("/index.php/search");
    expect(result.cityFieldName).toBe("city_id");
    expect(result.drugFieldName).toBe("drugname");
  });

  it("extracts pharmacy offers from results html", () => {
    const html = readFileSync(join(process.cwd(), "lib/mvp/fixtures/ref003-results-page.html"), "utf8");
    const result = parseRef003ResultsPage(html);

    expect(result.offers.length).toBeGreaterThan(0);
    expect(result.offers[0]?.pharmacyName).toBeTruthy();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/mvp/ref003-parser.test.ts`

Expected: FAIL because parser module does not exist.

**Step 3: Write minimal implementation**

- Use `cheerio.load(html)` to parse the page.
- Extract search form field names and default city/area selections from `#searchform`.
- Parse results rows into normalized `PharmacyOffer[]`.
- Return a parser result object that does not depend on React.

**Step 4: Add defensive parsing**

- Return empty arrays instead of throwing on missing tables.
- Add `warnings` for unexpected layouts.
- Keep raw text fragments when exact address or quantity parsing is ambiguous.

**Step 5: Run test to verify it passes**

Run: `npm test -- tests/mvp/ref003-parser.test.ts`

Expected: PASS

**Step 6: Commit**

```bash
git add lib/server/ref003.ts tests/mvp/ref003-parser.test.ts
git commit -m "feat: add ref003 parser"
```

### Task 3: Add OpenRouter suggestion client and prompt shaping

**Files:**
- Create: `frontend/lib/server/openrouter.ts`
- Create: `frontend/tests/mvp/openrouter.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { buildSuggestionPrompt, normalizeOpenRouterSuggestions } from "@/lib/server/openrouter";

describe("openrouter suggestion flow", () => {
  it("builds a symptom-to-drug prompt with strict json output instructions", () => {
    const prompt = buildSuggestionPrompt({
      query: "Препарат от головной боли",
      locale: "ru-RU"
    });

    expect(prompt).toContain("JSON");
    expect(prompt).toContain("головной боли");
  });

  it("normalizes llm output into ranked suggestions", () => {
    const result = normalizeOpenRouterSuggestions({
      suggestions: [
        { title: "Ибупрофен 200 мг", kind: "drug", confidence: 0.9, rationale: "..." }
      ]
    });

    expect(result[0]?.title).toBe("Ибупрофен 200 мг");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/mvp/openrouter.test.ts`

Expected: FAIL because module does not exist.

**Step 3: Write minimal implementation**

- `buildSuggestionPrompt()` should force JSON output with `suggestions[]`.
- `normalizeOpenRouterSuggestions()` should validate and coerce unknown data into `DrugSuggestion[]`.
- Add a small `callOpenRouter()` helper that accepts `query`, `baseUrl`, `apiKey`, and `model`.

**Step 4: Keep the LLM scope narrow**

- Only use OpenRouter for suggestion expansion and synonym help.
- Do not let the LLM invent pharmacy results or prices.
- If the user enters an exact drug name, skip or down-rank the LLM branch and search directly.

**Step 5: Run test to verify it passes**

Run: `npm test -- tests/mvp/openrouter.test.ts`

Expected: PASS

**Step 6: Commit**

```bash
git add lib/server/openrouter.ts tests/mvp/openrouter.test.ts
git commit -m "feat: add openrouter suggestion client"
```

### Task 4: Build the server-side search orchestrator

**Files:**
- Create: `frontend/lib/server/search-orchestrator.ts`
- Create: `frontend/app/api/search/route.ts`
- Create: `frontend/tests/mvp/search-orchestrator.test.ts`

**Step 1: Write the failing test**

```ts
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
          { id: "ibuprofen-200", title: "Ибупрофен 200 мг", kind: "drug", confidence: 0.9, rationale: "..." }
        ]),
        searchRef003: vi.fn().mockResolvedValue([])
      }
    );

    expect(result.mode).toBe("suggestions");
    expect(result.suggestions.length).toBe(1);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/mvp/search-orchestrator.test.ts`

Expected: FAIL because orchestrator does not exist.

**Step 3: Write minimal implementation**

- Detect whether the query looks like a symptom query or an exact drug query.
- For symptom queries: call OpenRouter, return suggestions, and optionally prefetch top suggestion search results.
- For exact drug queries: hit `ref003` immediately.
- Return one stable JSON shape from `/api/search`.

**Step 4: Add route handler**

- Parse JSON body with `query`, `cityId`, `areaId`, `lat`, `lon`.
- Call `runMvpSearch()`.
- Return `NextResponse.json(...)` with proper `400` handling for empty queries.

**Step 5: Run test to verify it passes**

Run: `npm test -- tests/mvp/search-orchestrator.test.ts`

Expected: PASS

**Step 6: Commit**

```bash
git add lib/server/search-orchestrator.ts app/api/search/route.ts tests/mvp/search-orchestrator.test.ts
git commit -m "feat: add mvp search api"
```

### Task 5: Build the route planner service

**Files:**
- Create: `frontend/lib/server/routing.ts`
- Create: `frontend/app/api/route/route.ts`
- Create: `frontend/tests/mvp/routing.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { buildRouteStops, shouldBuildRoute } from "@/lib/server/routing";

describe("routing rules", () => {
  it("requires at least two pharmacies to build a route", () => {
    expect(shouldBuildRoute([{ pharmacyId: "1" }])).toBe(false);
    expect(shouldBuildRoute([{ pharmacyId: "1" }, { pharmacyId: "2" }])).toBe(true);
  });

  it("builds ordered stops from user location and selected pharmacies", () => {
    const stops = buildRouteStops(
      { lat: 47.22, lon: 39.71 },
      [
        { pharmacyId: "1", pharmacyName: "A", lat: 47.23, lon: 39.72 },
        { pharmacyId: "2", pharmacyName: "B", lat: 47.24, lon: 39.73 }
      ]
    );

    expect(stops[0]?.label).toMatch(/Ваше местоположение/);
    expect(stops.length).toBe(3);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/mvp/routing.test.ts`

Expected: FAIL because routing module does not exist.

**Step 3: Write minimal implementation**

- `shouldBuildRoute()` returns `true` only for `>= 2` pharmacy stops.
- `buildRouteStops()` prepends the user origin.
- `fetchOptimizedRoute()` calls Geoapify routing with `optimize_stops=true` when there are multiple pharmacies.

**Step 4: Add route handler**

- Accept `origin` and selected `pharmacies[]`.
- Reject requests without location.
- Return geometry, ordered stops, total travel time, and total distance.

**Step 5: Run test to verify it passes**

Run: `npm test -- tests/mvp/routing.test.ts`

Expected: PASS

**Step 6: Commit**

```bash
git add lib/server/routing.ts app/api/route/route.ts tests/mvp/routing.test.ts
git commit -m "feat: add route planning api"
```

### Task 6: Build the new MVP shell and geolocation-first UX

**Files:**
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/page.module.css`
- Create: `frontend/tests/mvp/home-flow.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import HomePage from "@/app/page";

describe("mvp home flow", () => {
  it("shows geolocation CTA before search results flow", async () => {
    render(<HomePage />);

    expect(screen.getByRole("button", { name: /разрешить геолокацию/i })).toBeInTheDocument();
  });

  it("lets the user search by symptom phrase", async () => {
    const user = userEvent.setup();
    render(<HomePage />);

    const input = screen.getByRole("searchbox", { name: /поиск препарата/i });
    await user.type(input, "Препарат от головной боли");

    expect(input).toHaveValue("Препарат от головной боли");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/mvp/home-flow.test.tsx`

Expected: FAIL because the page still contains the old prototype.

**Step 3: Write minimal implementation**

- Replace the hero with a linear MVP narrative:
  1. request geolocation
  2. search box
  3. suggestions/results
  4. selected drug list
  5. pharmacy cards
  6. route panel
- Keep the visual language clean and direct for demos.
- Use obvious statuses: `awaiting-location`, `searching`, `showing-suggestions`, `showing-offers`, `building-route`.

**Step 4: Add geolocation handling**

- Use browser geolocation in a client component.
- Persist accepted location in component state.
- Show graceful fallback if geolocation is denied.

**Step 5: Run test to verify it passes**

Run: `npm test -- tests/mvp/home-flow.test.tsx`

Expected: PASS

**Step 6: Commit**

```bash
git add app/page.tsx app/page.module.css tests/mvp/home-flow.test.tsx
git commit -m "feat: add mvp geolocation-first shell"
```

### Task 7: Add suggestions, selected list, and pharmacy comparison UI

**Files:**
- Create: `frontend/components/mvp/SearchExperience.tsx`
- Create: `frontend/components/mvp/SelectedDrugList.tsx`
- Create: `frontend/components/mvp/PharmacyResults.tsx`
- Create: `frontend/tests/mvp/search-experience.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SearchExperience } from "@/components/mvp/SearchExperience";

describe("SearchExperience", () => {
  it("adds a suggested drug into the selected list", async () => {
    const user = userEvent.setup();
    render(
      <SearchExperience
        suggestions={[{ id: "1", title: "Ибупрофен 200 мг", kind: "drug", confidence: 0.9, rationale: "..." }]}
        offers={[]}
      />
    );

    await user.click(screen.getByRole("button", { name: /добавить ибупрофен 200 мг/i }));
    expect(screen.getByText(/ибупрофен 200 мг/i)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/mvp/search-experience.test.tsx`

Expected: FAIL because component does not exist.

**Step 3: Write minimal implementation**

- `SearchExperience` orchestrates calls to `/api/search`.
- `SelectedDrugList` stores chosen drugs.
- `PharmacyResults` renders normalized pharmacy cards sorted by travel time then price.

**Step 4: Add demo-safe UI states**

- Empty state before search
- Suggestion chips for symptom query results
- Inline error if `ref003` or OpenRouter fails
- “Добавить в список” on each suggestion or exact match

**Step 5: Run test to verify it passes**

Run: `npm test -- tests/mvp/search-experience.test.tsx`

Expected: PASS

**Step 6: Commit**

```bash
git add components/mvp tests/mvp/search-experience.test.tsx
git commit -m "feat: add mvp suggestion and results ui"
```

### Task 8: Add map and multi-pharmacy fastest route panel

**Files:**
- Create: `frontend/components/mvp/RouteMap.tsx`
- Create: `frontend/components/mvp/RouteSummary.tsx`
- Create: `frontend/tests/mvp/route-panel.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";
import { RouteSummary } from "@/components/mvp/RouteSummary";

describe("RouteSummary", () => {
  it("renders total route time when two or more pharmacies are selected", () => {
    render(
      <RouteSummary
        route={{
          totalDurationMinutes: 18,
          totalDistanceKm: 5.4,
          orderedStops: [
            { pharmacyId: "origin", label: "Ваше местоположение", lat: 0, lon: 0, order: 0 },
            { pharmacyId: "1", label: "Аптека 1", lat: 0, lon: 0, order: 1 },
            { pharmacyId: "2", label: "Аптека 2", lat: 0, lon: 0, order: 2 }
          ]
        }}
      />
    );

    expect(screen.getByText(/18 мин/i)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/mvp/route-panel.test.tsx`

Expected: FAIL because component does not exist.

**Step 3: Write minimal implementation**

- `RouteSummary` shows total time, distance, and ordered stops.
- `RouteMap` uses MapLibre and a Geoapify tile/style source.
- Only request `/api/route` when the selected pharmacy count is `>= 2`.

**Step 4: Keep the route panel MVP-safe**

- For one pharmacy: show CTA “Добавьте еще аптеку для быстрого маршрута”.
- For two or more pharmacies: show “Построить самый быстрый маршрут”.
- Display route failure without breaking the search flow.

**Step 5: Run test to verify it passes**

Run: `npm test -- tests/mvp/route-panel.test.tsx`

Expected: PASS

**Step 6: Commit**

```bash
git add components/mvp tests/mvp/route-panel.test.tsx
git commit -m "feat: add mvp route panel"
```

### Task 9: Add configuration, docs, and full verification

**Files:**
- Create: `frontend/.env.example`
- Modify: `frontend/README.md`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

**Step 1: Add required environment variables**

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
GEOAPIFY_API_KEY=
```

**Step 2: Add required dependencies**

- `cheerio`
- `zod`
- `maplibre-gl`

**Step 3: Document the external flow**

- `ref003` is scraped server-side over `http`
- OpenRouter is only for suggestions
- Geoapify is used for route building
- geolocation permission is required for the full route experience

**Step 4: Run full verification**

Run: `npm test`

Expected: PASS

Run: `npm run build`

Expected: PASS

**Step 5: Commit**

```bash
git add .env.example README.md package.json package-lock.json
git commit -m "chore: document mvp setup"
```
