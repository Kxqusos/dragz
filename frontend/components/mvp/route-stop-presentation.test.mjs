import assert from "node:assert/strict";
import test from "node:test";

import {
  getRouteDirectionStopLabel,
  getRouteMapMarkerLabel,
  getRouteStopIndexLabel
} from "./route-stop-presentation.ts";

const originStart = {
  pharmacyId: "origin",
  label: "Ваше местоположение",
  lat: 47.2,
  lon: 39.7,
  order: 0
};

const pharmacyStop = {
  pharmacyId: "pharmacy-1",
  label: "ЛАДА-2-я Краснодарская, 145 Д",
  lat: 47.21,
  lon: 39.71,
  order: 1
};

const originReturn = {
  pharmacyId: "origin",
  label: "Ваше местоположение",
  lat: 47.2,
  lon: 39.7,
  order: 2
};

test("shows user origin stops as 'Вы' instead of numeric indices", () => {
  assert.equal(getRouteStopIndexLabel(originStart), "Вы");
  assert.equal(getRouteStopIndexLabel(pharmacyStop), "2.");
  assert.equal(getRouteStopIndexLabel(originReturn), "Вы");
});

test("shows user origin markers as 'Вы' on the map", () => {
  assert.equal(getRouteMapMarkerLabel(originStart), "Вы");
  assert.equal(getRouteMapMarkerLabel(pharmacyStop), "2");
  assert.equal(getRouteMapMarkerLabel(originReturn), "Вы");
});

test("uses the short user label in the route direction path", () => {
  assert.equal(getRouteDirectionStopLabel(originStart), "Вы");
  assert.equal(getRouteDirectionStopLabel(pharmacyStop), "ЛАДА-2-я Краснодарская, 145 Д");
  assert.equal(getRouteDirectionStopLabel(originReturn), "Вы");
});
