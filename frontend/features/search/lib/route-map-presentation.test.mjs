import assert from "node:assert/strict";
import test from "node:test";

import {
  buildRouteLineFeature,
  buildRouteArrowFeature,
} from "./route-map-presentation.ts";

test("builds a line feature from ordered route geometry", () => {
  const geometry = [
    [39.71, 47.22],
    [39.72, 47.23],
  ];

  const feature = buildRouteLineFeature(geometry);

  assert.equal(feature.geometry.type, "LineString");
  assert.deepEqual(feature.geometry.coordinates, geometry);
});

test("builds a directional arrow feature for route rendering", () => {
  const geometry = [
    [39.71, 47.22],
    [39.72, 47.23],
    [39.73, 47.24],
  ];

  const feature = buildRouteArrowFeature(geometry);

  assert.equal(feature.geometry.type, "LineString");
  assert.deepEqual(feature.geometry.coordinates, geometry);
  assert.equal(feature.properties.arrow, "➜");
});
