from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import SiteSetting
from app.schemas import SiteSettingItem, SiteSettingsResponse


def default_site_settings(settings: Settings) -> dict[str, object]:
    return {
        "site_name": settings.site_name,
        "site_support_email": settings.site_support_email,
        "site_support_url": settings.site_support_url,
        "feature_registration_enabled": settings.feature_registration_enabled,
        "feature_ai_consult_enabled": settings.feature_ai_consult_enabled,
        "auth_access_token_ttl_minutes": settings.auth_access_token_ttl_minutes,
        "auth_refresh_token_ttl_days": settings.auth_refresh_token_ttl_days,
        "debug_retention_days": settings.debug_retention_days,
        "history_retention_days": settings.history_retention_days,
    }


async def get_site_settings(session: AsyncSession, settings: Settings) -> SiteSettingsResponse:
    defaults = default_site_settings(settings)
    result = await session.execute(select(SiteSetting).order_by(SiteSetting.key.asc()))
    overrides = {item.key: item.value_json for item in result.scalars().all()}
    merged = {**defaults, **overrides}
    return SiteSettingsResponse(
        items=[SiteSettingItem(key=key, value=value) for key, value in merged.items()]
    )


async def update_site_settings(
    session: AsyncSession,
    *,
    items: list[SiteSettingItem],
    settings: Settings,
) -> SiteSettingsResponse:
    allowed_keys = set(default_site_settings(settings).keys())
    now = datetime.now(UTC)
    for item in items:
        if item.key not in allowed_keys:
            continue
        result = await session.execute(select(SiteSetting).where(SiteSetting.key == item.key))
        record = result.scalar_one_or_none()
        if record is None:
            session.add(SiteSetting(key=item.key, value_json=item.value, updated_at=now))
        else:
            record.value_json = item.value
            record.updated_at = now
    await session.commit()
    return await get_site_settings(session, settings)
