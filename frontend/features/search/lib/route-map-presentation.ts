export function buildRouteLineFeature(geometry: Array<[number, number]>) {
  return {
    type: "Feature" as const,
    geometry: {
      type: "LineString" as const,
      coordinates: geometry,
    },
    properties: {},
  };
}

export function buildRouteArrowFeature(geometry: Array<[number, number]>) {
  return {
    type: "Feature" as const,
    geometry: {
      type: "LineString" as const,
      coordinates: geometry,
    },
    properties: {
      arrow: "➜",
    },
  };
}
