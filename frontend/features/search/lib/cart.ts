import type { CartItem, PharmacyOffer } from "@/features/search/model/types";
import { getPharmacyGroupKey } from "@/features/search/model/types";

export function buildRoutePharmaciesFromCart(items: CartItem[]): PharmacyOffer[] {
  const uniquePharmacies = new Map<string, PharmacyOffer>();

  for (const item of items) {
    const key = getPharmacyGroupKey(item);
    if (!uniquePharmacies.has(key)) {
      uniquePharmacies.set(key, item);
    }
  }

  return [...uniquePharmacies.values()];
}

export function countItemsForPharmacy(items: CartItem[], offer: Pick<CartItem, "pharmacyName" | "address">): number {
  const key = getPharmacyGroupKey(offer);
  return items.filter((item) => getPharmacyGroupKey(item) === key).length;
}
