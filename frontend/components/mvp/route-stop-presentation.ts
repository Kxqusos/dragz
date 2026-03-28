import type { RouteStop } from "../../lib/mvp/types";

function isOriginStop(stop: RouteStop): boolean {
  return stop.pharmacyId === "origin";
}

export function getRouteStopIndexLabel(stop: RouteStop): string {
  if (isOriginStop(stop)) {
    return "Вы";
  }

  return `${stop.order + 1}.`;
}

export function getRouteMapMarkerLabel(stop: RouteStop): string {
  if (isOriginStop(stop)) {
    return "Вы";
  }

  return `${stop.order + 1}`;
}

export function getRouteDirectionStopLabel(stop: RouteStop): string {
  if (isOriginStop(stop)) {
    return "Вы";
  }

  return stop.label;
}
