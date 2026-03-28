import type { PharmacyOffer } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";

type PharmacyResultsProps = {
  offers: PharmacyOffer[];
  distanceKmById: Map<string, number>;
  selectedIds: Set<string>;
  onToggle: (offer: PharmacyOffer) => void;
};

export function PharmacyResults({
  offers,
  distanceKmById,
  selectedIds,
  onToggle
}: PharmacyResultsProps) {
  if (offers.length === 0) {
    return (
      <p className={styles.emptyState}>
        После выбора препарата здесь появятся аптеки, доступные для маршрута.
      </p>
    );
  }

  return (
    <div className={styles.offerList}>
      {offers.map((offer) => {
        const isSelected = selectedIds.has(offer.pharmacyId);
        const distanceKm = distanceKmById.get(offer.pharmacyId);

        return (
          <article key={offer.pharmacyId} className={styles.offerCard}>
            <div>
              <h3 className={styles.offerTitle}>{offer.pharmacyName}</h3>
              <p>{offer.address}</p>
              <p className={styles.offerDrugMeta}>
                {offer.matchedDrug} • {offer.inStock ? "В наличии" : "Нет в наличии"}
              </p>
              <div className={styles.offerMetaRow}>
                <span>
                  {offer.price} ₽ • {offer.quantityLabel}
                </span>
                {Number.isFinite(distanceKm) ? (
                  <span className={styles.offerDistance}>{formatDistanceKm(distanceKm ?? 0)}</span>
                ) : (
                  <span className={styles.offerDistancePending}>Координаты уточняются</span>
                )}
              </div>
            </div>
            <button
              className={styles.secondaryButton}
              type="button"
              onClick={() => onToggle(offer)}
            >
              {isSelected ? "Убрать из корзины" : "Добавить в корзину"}
            </button>
          </article>
        );
      })}
    </div>
  );
}

function formatDistanceKm(distanceKm: number): string {
  return `${Math.max(0, Math.round(distanceKm))} км`;
}
