import type { RoutePreview } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";
import {
  getRouteDirectionStopLabel,
  getRouteStopIndexLabel
} from "./route-stop-presentation";

type RouteSummaryProps = {
  route: RoutePreview;
};

export function RouteSummary({
  route
}: RouteSummaryProps) {
  const directionStops = route.orderedStops.map(getRouteDirectionStopLabel);

  return (
    <section className={styles.routeSummary}>
      <div className={styles.routeMetricsRow}>
        <div className={styles.routeMetrics}>
          <strong>{route.totalDurationMinutes} мин</strong>
          <span>время в пути</span>
        </div>
        <div className={styles.routeMetrics}>
          <strong>{route.totalDistanceKm} км</strong>
          <span>общая длина маршрута</span>
        </div>
      </div>

      <div className={styles.directionCard}>
        <span className={styles.directionLabel}>Направление движения</span>
        <p className={styles.directionPath}>{directionStops.join(" → ")}</p>
      </div>

      <ol className={styles.routeStops}>
        {route.orderedStops.map((stop, index) => (
          <li key={`${stop.pharmacyId}-${stop.order}`}>
            <span className={styles.stopIndex}>{getRouteStopIndexLabel(stop)}</span>
            <div className={styles.stopBody}>
              <strong>{stop.label}</strong>
              <span className={styles.stopMeta}>
                {index === 0
                  ? "Старт"
                  : index === route.orderedStops.length - 1
                    ? "Возврат"
                    : `Далее к точке ${index + 2}`}
              </span>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
