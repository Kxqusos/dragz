from urllib.parse import urljoin
import logging

import httpx

from app.services.ref003.parser import Ref003SearchResults, Ref003Variant, parse_search_results
from app.services.search_engine.medicine import (
    build_drug_search_candidates as build_engine_search_candidates,
    normalize_query_key as normalize_engine_query_key,
)


BASE_URL = "http://www.ref003.ru/"
SEARCH_URL = "http://www.ref003.ru/index.php/search"
SEARCH_BASE_URL = "http://www.ref003.ru/index.php/"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
}
logger = logging.getLogger(__name__)
def build_variant_url(variant: Ref003Variant) -> str:
    return urljoin(SEARCH_BASE_URL, variant.href)


async def fetch_search_page(
    query: str,
    *,
    city_id: str = "0",
    area_id: str = "0",
    drug_id: str = "0",
    client: httpx.AsyncClient | None = None,
) -> Ref003SearchResults:
    owns_client = client is None
    active_client = client or httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=45.0)

    try:
        logger.info("ref003_search_page_request query=%r city_id=%s area_id=%s drug_id=%s", query, city_id, area_id, drug_id)
        response = await active_client.get(
            SEARCH_URL,
            params={
                "type_drugname": "torg",
                "drugname": query,
                "drugname_id": drug_id,
                "city_id": city_id,
                "area_id": area_id,
                "trace": "1" if drug_id != "0" else None,
            },
        )
        response.raise_for_status()
        parsed = parse_search_results(response.text)
        logger.info(
            "ref003_search_page_response query=%r variants=%d offers=%d warnings=%s",
            query,
            len(parsed.variants),
            len(parsed.offers),
            parsed.warnings,
        )
        return parsed
    finally:
        if owns_client:
            await active_client.aclose()


async def resolve_offers(
    query: str,
    *,
    city_id: str = "0",
    area_id: str = "0",
    client: httpx.AsyncClient | None = None,
) -> Ref003SearchResults:
    last_result: Ref003SearchResults | None = None
    candidates = build_search_candidates(query)
    logger.info("ref003_resolve_start query=%r candidates=%s", query, candidates)
    for candidate in candidates:
        initial = await fetch_search_page(candidate, city_id=city_id, area_id=area_id, client=client)
        last_result = initial
        if initial.offers:
            logger.info("ref003_resolve_success query=%r matched_candidate=%r mode=direct", query, candidate)
            return initial

        if not initial.variants:
            continue

        exact_variant = next(
            (variant for variant in initial.variants if normalize_query_key(variant.drug_name) == normalize_query_key(query)),
            initial.variants[0],
        )
        logger.info(
            "ref003_variant_selected query=%r candidate=%r variant=%r variant_id=%s",
            query,
            candidate,
            exact_variant.drug_name,
            exact_variant.drug_id,
        )

        owns_client = client is None
        active_client = client or httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=45.0)

        try:
            variant_url = build_variant_url(exact_variant)
            response = await active_client.get(variant_url)
            if response.is_error:
                logger.info("ref003_variant_fetch_failed query=%r variant=%r status=%s", query, exact_variant.drug_name, response.status_code)
                return Ref003SearchResults(
                    query=initial.query,
                    variants=initial.variants,
                    offers=[],
                    warnings=[*initial.warnings, "variant-fetch-failed"],
                )
            parsed_variant = parse_search_results(response.text)
            if parsed_variant.offers:
                logger.info("ref003_resolve_success query=%r matched_candidate=%r mode=variant offers=%d", query, candidate, len(parsed_variant.offers))
                return parsed_variant
        finally:
            if owns_client:
                await active_client.aclose()

    logger.info("ref003_resolve_empty query=%r", query)
    return last_result or Ref003SearchResults(query=query, variants=[], offers=[], warnings=["empty-results"])


def build_search_candidates(query: str) -> list[str]:
    return build_engine_search_candidates(query)


def normalize_query_key(query: str) -> str:
    return normalize_engine_query_key(query)
