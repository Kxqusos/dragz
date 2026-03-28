import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const componentSource = readFileSync(
  join(import.meta.dirname, "SearchExperience.tsx"),
  "utf8"
);
const stylesSource = readFileSync(
  join(import.meta.dirname, "search-experience.module.css"),
  "utf8"
);

test("wraps the route build button in a dedicated layout container", () => {
  assert.match(
    componentSource,
    /<div className=\{styles\.routeActions\}>[\s\S]*Построить маршрут по корзине/
  );
});

test("defines dedicated spacing rules for the route action container", () => {
  assert.match(stylesSource, /\.routeActions\s*\{/);
});
