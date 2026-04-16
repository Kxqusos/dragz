import assert from "node:assert/strict";
import test from "node:test";

import { formatDistanceKm } from "./offer-distance-format.ts";

test("shows sub-kilometer distances as decimals instead of rounding to zero", () => {
  assert.equal(formatDistanceKm(0.34), "0.3 км");
  assert.equal(formatDistanceKm(0.96), "1.0 км");
});

test("shows larger distances with one decimal place", () => {
  assert.equal(formatDistanceKm(2.44), "2.4 км");
  assert.equal(formatDistanceKm(12.01), "12.0 км");
});
