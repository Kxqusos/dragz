import type { RouteStop } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";

type RoutePreview = {
  totalDurationMinutes: number;
  totalDistanceKm: number;
  orderedStops: RouteStop[];
};

type RouteMapProps = {
  route: RoutePreview;
};

export function RouteMap({
  route
}: RouteMapProps) {
  return (
    <div className={styles.mapCard} aria-label="Карта маршрута">
      {route.orderedStops.map((stop) => (
        <span
          key={`${stop.pharmacyId}-${stop.order}`}
          className={styles.mapMarker}
          style={{
            left: `${18 + stop.order * 24}%`,
            top: `${24 + (stop.order % 2) * 28}%`
          }}
        >
          {stop.order + 1}
        </span>
      ))}
    </div>
  );
}
