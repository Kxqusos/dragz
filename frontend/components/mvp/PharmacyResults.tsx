import type { PharmacyOffer } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";

type PharmacyResultsProps = {
  offers: PharmacyOffer[];
  selectedIds: Set<string>;
  onToggle: (offer: PharmacyOffer) => void;
};

export function PharmacyResults({
  offers,
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

        return (
          <article key={offer.pharmacyId} className={styles.offerCard}>
            <div>
              <strong>{offer.pharmacyName}</strong>
              <p>{offer.address}</p>
              <span>
                {offer.price} ₽ • {offer.quantityLabel}
              </span>
            </div>
            <button
              className={styles.secondaryButton}
              type="button"
              onClick={() => onToggle(offer)}
            >
              {isSelected ? "Убрать из маршрута" : "Выбрать для маршрута"}
            </button>
          </article>
        );
      })}
    </div>
  );
}
