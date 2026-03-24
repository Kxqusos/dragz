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
        {
          pharmacyId: "1",
          pharmacyName: "A",
          lat: 47.23,
          lon: 39.72
        },
        {
          pharmacyId: "2",
          pharmacyName: "B",
          lat: 47.24,
          lon: 39.73
        }
      ]
    );

    expect(stops[0]?.label).toMatch(/Ваше местоположение/);
    expect(stops.length).toBe(3);
    expect(stops[2]?.order).toBe(2);
  });
});
