import { NextResponse } from "next/server";
import type { PharmacyOffer } from "@/lib/mvp/types";
import { buildRouteStops, shouldBuildRoute } from "@/lib/server/routing";

type RouteBody = {
  origin?: {
    lat: number;
    lon: number;
  };
  pharmacies?: PharmacyOffer[];
};

export async function POST(request: Request) {
  const body = (await request.json()) as RouteBody;

  if (!body.origin || !body.pharmacies) {
    return NextResponse.json({ error: "origin and pharmacies are required" }, { status: 400 });
  }

  if (!shouldBuildRoute(body.pharmacies)) {
    return NextResponse.json({ error: "at least two pharmacies are required" }, { status: 400 });
  }

  const orderedStops = buildRouteStops(body.origin, body.pharmacies);

  return NextResponse.json({
    totalDurationMinutes: 12 + body.pharmacies.length * 3,
    totalDistanceKm: Number((2.4 + body.pharmacies.length * 1.1).toFixed(1)),
    orderedStops
  });
}
