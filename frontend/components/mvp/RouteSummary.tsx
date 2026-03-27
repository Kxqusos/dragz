import type { RoutePreview } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";

type RouteSummaryProps = {
  route: RoutePreview;
};

export function RouteSummary({
  route
}: RouteSummaryProps) {
  const directionStops = route.orderedStops.map((stop, index, stops) => {
    if (stop.pharmacyId === "origin" && index === 0) {
      return "Ваше местоположение";
    }

    if (stop.pharmacyId === "origin" && index === stops.length - 1) {
      return "Ваше местоположение";
    }

    return stop.label;
  });

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
            <span className={styles.stopIndex}>{stop.order + 1}.</span>
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
