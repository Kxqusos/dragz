from app.schemas import PharmacyOffer, SearchResponse
from app.services.ref003.parser import Ref003Offer


def _looks_like_symptom_query(query: str) -> bool:
    normalized = query.lower()
    return (
        "от " in normalized
        or "для " in normalized
        or "головной боли" in normalized
        or "простуды" in normalized
    )


def to_pharmacy_offer(offer: Ref003Offer) -> PharmacyOffer:
    pharmacy_id = f"{offer.pharmacy_name}:{offer.address}:{offer.price}:{offer.quantity_label}:{offer.matched_drug}"
    return PharmacyOffer(
        pharmacy_id=pharmacy_id,
        pharmacy_name=offer.pharmacy_name,
        address=offer.address,
        lat=0.0,
        lon=0.0,
        price=offer.price,
        in_stock=True,
        quantity_label=offer.quantity_label,
        matched_drug=offer.matched_drug,
    )


def run_search_flow(
    query: str,
    *,
    resolve_offers,
    city_id: str = "0",
    area_id: str = "0",
) -> SearchResponse:
    if _looks_like_symptom_query(query):
        return SearchResponse(mode="suggestions", suggestions=[], offers=[], warnings=["llm-unavailable"])

    offers = resolve_offers(query, city_id=city_id, area_id=area_id)
    return SearchResponse(mode="offers", offers=offers, suggestions=[])
