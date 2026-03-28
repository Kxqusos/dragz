import assert from "node:assert/strict";
import test from "node:test";

import {
  getVisibleOffers,
  shouldShowMoreOffers
} from "./offer-list-presentation.ts";

const offers = Array.from({ length: 7 }, (_, index) => ({
  pharmacyId: `pharmacy-${index + 1}`
}));

test("shows only the first five offers before expansion", () => {
  assert.deepEqual(
    getVisibleOffers(offers, false).map((offer) => offer.pharmacyId),
    ["pharmacy-1", "pharmacy-2", "pharmacy-3", "pharmacy-4", "pharmacy-5"]
  );
});

test("shows every offer after expansion", () => {
  assert.equal(getVisibleOffers(offers, true).length, 7);
});

test("shows the expand button only when hidden offers remain", () => {
  assert.equal(shouldShowMoreOffers(offers.length, false), true);
  assert.equal(shouldShowMoreOffers(offers.length, true), false);
  assert.equal(shouldShowMoreOffers(5, false), false);
});
