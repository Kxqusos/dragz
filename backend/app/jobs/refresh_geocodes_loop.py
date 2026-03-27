import asyncio
import logging

from app.cache.redis import create_redis_client
from app.core.config import Settings
from app.jobs.refresh_geocodes import refresh_passive_geocodes

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = Settings()
    cache = create_redis_client(settings.redis_url)

    while True:
        await refresh_passive_geocodes(cache, settings)
        logger.info("refresh_geocode_loop_sleep seconds=%d", settings.geocode_refresh_loop_interval_seconds)
        await asyncio.sleep(settings.geocode_refresh_loop_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
