import type { PharmacyOffer } from "@/lib/mvp/types";

export const DEFAULT_VISIBLE_OFFERS = 5;

export function getVisibleOffers(
  offers: PharmacyOffer[],
  isExpanded: boolean,
  visibleCount = DEFAULT_VISIBLE_OFFERS
): PharmacyOffer[] {
  if (isExpanded) {
    return offers;
  }

  return offers.slice(0, visibleCount);
}

export function shouldShowMoreOffers(
  offerCount: number,
  isExpanded: boolean,
  visibleCount = DEFAULT_VISIBLE_OFFERS
): boolean {
  return !isExpanded && offerCount > visibleCount;
}
