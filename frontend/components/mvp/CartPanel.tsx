import type { CartItem } from "@/lib/mvp/types";
import { countItemsForPharmacy } from "@/lib/mvp/cart";
import styles from "./search-experience.module.css";

type CartPanelProps = {
  items: CartItem[];
  uniquePharmacyCount: number;
  onRemove: (item: CartItem) => void;
  onClear: () => void;
};

export function CartPanel({ items, uniquePharmacyCount, onRemove, onClear }: CartPanelProps) {
  if (items.length === 0) {
    return (
      <p className={styles.cardText}>
        Добавьте предложения из поиска в корзину. Потом из неё можно построить маршрут по
        аптекам с несколькими препаратами.
      </p>
    );
  }

  return (
    <div className={styles.cartWrap}>
      <div className={styles.cartHeader}>
        <div>
          <strong className={styles.cartTitle}>Корзина</strong>
          <p className={styles.cartMeta}>
            {items.length} поз. • {uniquePharmacyCount} апт.
          </p>
        </div>
        <button className={styles.inlineButton} type="button" onClick={onClear}>
          Очистить
        </button>
      </div>

      <div className={styles.selectedList}>
        {items.map((item) => {
          const pharmacyItemCount = countItemsForPharmacy(items, item);

          return (
            <article key={item.pharmacyId} className={styles.selectedItem}>
              <div className={styles.cartItemBody}>
                <strong>{item.matchedDrug}</strong>
                <span>{item.quantityLabel}</span>
                <span>
                  {item.pharmacyName} • {item.address}
                </span>
                <span>{item.price} ₽</span>
                {pharmacyItemCount > 1 ? (
                  <span className={styles.cartBadge}>
                    В этой аптеке ещё {pharmacyItemCount - 1} поз.
                  </span>
                ) : null}
              </div>
              <button
                className={styles.secondaryButton}
                type="button"
                onClick={() => onRemove(item)}
              >
                Убрать
              </button>
            </article>
          );
        })}
      </div>
    </div>
  );
}
