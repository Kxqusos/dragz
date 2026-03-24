import type { RouteStop } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";

type RoutePreview = {
  totalDurationMinutes: number;
  totalDistanceKm: number;
  orderedStops: RouteStop[];
};

type RouteSummaryProps = {
  route: RoutePreview;
};

export function RouteSummary({
  route
}: RouteSummaryProps) {
  return (
    <section className={styles.routeSummary}>
      <div className={styles.routeMetrics}>
        <strong>{route.totalDurationMinutes} мин</strong>
        <span>время в пути</span>
      </div>
      <div className={styles.routeMetrics}>
        <strong>{route.totalDistanceKm} км</strong>
        <span>общая длина маршрута</span>
      </div>

      <ol className={styles.routeStops}>
        {route.orderedStops.map((stop) => (
          <li key={`${stop.pharmacyId}-${stop.order}`}>
            <span>{stop.order + 1}.</span>
            <strong>{stop.label}</strong>
          </li>
        ))}
      </ol>
    </section>
  );
}
