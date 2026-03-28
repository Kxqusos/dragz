import json
import re
from typing import Awaitable, Callable

from redis.asyncio import Redis

from app.schemas import PharmacyOffer, Suggestion

CACHE_VERSION = "v5"


async def cached_suggest_drugs(
    cache: Redis | None,
    query: str,
    producer: Callable[[str], Awaitable[list[Suggestion]]],
    *,
    ttl: int = 300,
) -> list[Suggestion]:
    cache_key = f"{CACHE_VERSION}:openrouter:suggestions:{query.strip().lower()}"

    if cache is not None:
        try:
            cached = await cache.get(cache_key)
        except Exception:
            cached = None
        if cached:
            return [Suggestion.model_validate(item) for item in json.loads(cached)]

    suggestions = await producer(query)

    if cache is not None:
        try:
            await cache.setex(
                cache_key,
                ttl,
                json.dumps([item.model_dump() for item in suggestions], ensure_ascii=False),
            )
        except Exception:
            pass

    return suggestions


async def cached_resolve_offers(
    cache: Redis | None,
    query: str,
    resolver: Callable[..., Awaitable[list[PharmacyOffer]]],
    *,
    city_id: str,
    area_id: str,
    ttl: int = 300,
) -> list[PharmacyOffer]:
    cache_key = f"{CACHE_VERSION}:ref003:offers:{city_id}:{area_id}:{query.strip().lower()}"

    if cache is not None:
        try:
            cached = await cache.get(cache_key)
        except Exception:
            cached = None
        if cached:
            return [PharmacyOffer.model_validate(item) for item in json.loads(cached)]

    offers = await resolver(query, city_id=city_id, area_id=area_id)

    if cache is not None:
        try:
            await cache.setex(
                cache_key,
                ttl,
                json.dumps([item.model_dump() for item in offers], ensure_ascii=False),
            )
        except Exception:
            pass

    return offers


def normalize_geocode_cache_address(address: str) -> str:
    return re.sub(r"\s+", " ", address.strip().lower())


def geocode_cache_key(address: str) -> str:
    return f"{CACHE_VERSION}:geocode:address:{normalize_geocode_cache_address(address)}"


def geocode_provider_cooldown_key(provider: str) -> str:
    return f"{CACHE_VERSION}:geocode:provider-cooldown:{provider}"


async def get_cached_geocode_record(cache: Redis | None, address: str) -> dict | None:
    if cache is None:
        return None
    try:
        cached = await cache.get(geocode_cache_key(address))
    except Exception:
        return None
    if not cached:
        return None
    try:
        return json.loads(cached)
    except Exception:
        return None


async def set_cached_geocode_record(
    cache: Redis | None,
    address: str,
    record: dict,
    *,
    ttl: int,
) -> None:
    if cache is None:
        return
    try:
        await cache.setex(
            geocode_cache_key(address),
            ttl,
            json.dumps(record, ensure_ascii=False),
        )
    except Exception:
        pass


async def is_provider_in_cooldown(cache: Redis | None, provider: str) -> bool:
    if cache is None:
        return False
    try:
        return await cache.get(geocode_provider_cooldown_key(provider)) is not None
    except Exception:
        return False


async def set_provider_cooldown(cache: Redis | None, provider: str, *, ttl: int) -> None:
    if cache is None:
        return
    try:
        await cache.setex(
            geocode_provider_cooldown_key(provider),
            ttl,
            json.dumps({"status": "cooldown", "provider": provider}, ensure_ascii=False),
        )
    except Exception:
        pass


async def iter_cached_geocode_records(cache: Redis | None):
    if cache is None:
        return

    async for key in cache.scan_iter(match=f"{CACHE_VERSION}:geocode:address:*"):
        normalized_key = key.decode() if isinstance(key, bytes) else str(key)
        record = await get_cached_geocode_record(cache, normalized_key.split(":address:", 1)[-1])
        if record is None:
            continue
        yield normalized_key, record
