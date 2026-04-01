from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.db.models import User
from app.schemas import (
    AdminUserPatchRequest,
    AdminUsersResponse,
    DebugEventsResponse,
    SiteSettingsResponse,
    SiteSettingsUpdateRequest,
)
from app.services.debug_events import list_debug_events
from app.services.site_settings import get_site_settings, update_site_settings
from app.services.users import serialize_user


router = APIRouter(tags=["admin"])
settings = Settings()


@router.get("/api/admin/users", response_model=AdminUsersResponse)
async def get_admin_users(
    _admin=Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
) -> AdminUsersResponse:
    result = await db_session.execute(select(User).order_by(User.created_at.asc(), User.email.asc()))
    return AdminUsersResponse(items=[serialize_user(user) for user in result.scalars().all()])


@router.patch("/api/admin/users/{user_id}", response_model=AdminUsersResponse)
async def patch_admin_user(
    user_id: str,
    payload: AdminUserPatchRequest,
    _admin=Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
) -> AdminUsersResponse:
    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    if payload.role is not None:
        user.role = payload.role
    if payload.is_blocked is not None:
        user.is_blocked = payload.is_blocked
    await db_session.commit()
    result = await db_session.execute(select(User).order_by(User.created_at.asc(), User.email.asc()))
    return AdminUsersResponse(items=[serialize_user(item) for item in result.scalars().all()])


@router.get("/api/admin/settings", response_model=SiteSettingsResponse)
async def get_admin_settings(
    _admin=Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
) -> SiteSettingsResponse:
    return await get_site_settings(db_session, settings)


@router.put("/api/admin/settings", response_model=SiteSettingsResponse)
async def put_admin_settings(
    payload: SiteSettingsUpdateRequest,
    _admin=Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
) -> SiteSettingsResponse:
    return await update_site_settings(db_session, items=payload.items, settings=settings)


@router.get("/api/admin/debug-events", response_model=DebugEventsResponse)
async def get_admin_debug_events(
    _admin=Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
) -> DebugEventsResponse:
    return await list_debug_events(db_session)
