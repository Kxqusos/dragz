import { useEffect, useState } from "react";
import type { PharmacyOffer } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";
import {
  getVisibleOffers,
  shouldShowMoreOffers
} from "./offer-list-presentation";

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
  const [isExpanded, setIsExpanded] = useState(false);
  const offersKey = [...offers].map((offer) => offer.pharmacyId).sort().join("|");

  useEffect(() => {
    setIsExpanded(false);
  }, [offersKey]);

  if (offers.length === 0) {
    return (
      <p className={styles.emptyState}>
        После выбора препарата здесь появятся аптеки, доступные для маршрута.
      </p>
    );
  }

  const visibleOffers = getVisibleOffers(offers, isExpanded);
  const canShowMore = shouldShowMoreOffers(offers.length, isExpanded);

  return (
    <>
      <div className={styles.offerList}>
        {visibleOffers.map((offer) => {
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
      {canShowMore ? (
        <div className={styles.offerActions}>
          <button
            className={`${styles.secondaryButton} ${styles.showMoreButton}`}
            type="button"
            onClick={() => setIsExpanded(true)}
          >
            Показать больше
          </button>
        </div>
      ) : null}
    </>
  );
}

function formatDistanceKm(distanceKm: number): string {
  return `${Math.max(0, Math.round(distanceKm))} км`;
}
