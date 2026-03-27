import asyncio
from collections.abc import Awaitable, Callable
import logging

from app.schemas import PharmacyOffer

logger = logging.getLogger(__name__)

async def enrich_offers_with_geodata(
    offers: list[PharmacyOffer],
    geocode: Callable[[str], Awaitable[tuple[float, float] | None]],
    *,
    limit: int = 30,
    concurrency: int = 5,
) -> list[PharmacyOffer]:
    semaphore = asyncio.Semaphore(concurrency)
    scoped_offers = offers[:limit]
    unique_addresses = list(dict.fromkeys(offer.address for offer in scoped_offers))
    logger.info(
        "offer_enrichment_start total=%d limit=%d concurrency=%d unique_addresses=%d",
        len(offers),
        limit,
        concurrency,
        len(unique_addresses),
    )

    async def geocode_one(address: str) -> tuple[float, float] | None:
        try:
            async with semaphore:
                coordinates = await geocode(address)
        except Exception:
            coordinates = None
            logger.exception("offer_enrichment_error address=%r", address)
        return coordinates

    resolved_by_address = dict(
        zip(unique_addresses, await asyncio.gather(*(geocode_one(address) for address in unique_addresses)))
    )

    enriched: list[PharmacyOffer] = []
    for offer in scoped_offers:
        coordinates = resolved_by_address.get(offer.address)
        if coordinates is None:
            logger.info("offer_enrichment_unresolved pharmacy=%r address=%r", offer.pharmacy_name, offer.address)
            enriched.append(offer)
            continue

        lat, lon = coordinates
        logger.info(
            "offer_enrichment_resolved pharmacy=%r address=%r lat=%s lon=%s",
            offer.pharmacy_name,
            offer.address,
            lat,
            lon,
        )
        enriched.append(offer.model_copy(update={"lat": lat, "lon": lon}))

    resolved = sum(1 for offer in enriched if (offer.lat != 0 or offer.lon != 0))
    logger.info("offer_enrichment_complete processed=%d resolved=%d unresolved=%d", len(enriched), resolved, len(enriched) - resolved)
    return enriched
