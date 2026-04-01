from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Cookie, Depends, HTTPException, Request, status
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.db.models import User
from app.services.auth import ACCESS_COOKIE_NAME, decode_token, ensure_utc, get_auth_session
from app.services.debug_events import hash_ip_address
from app.services.users import get_user_by_id


settings = Settings()


async def get_optional_current_user(
    db_session: AsyncSession = Depends(get_db_session),
    access_token: str | None = Cookie(default=None, alias=ACCESS_COOKIE_NAME),
) -> User | None:
    if not access_token:
        return None
    try:
        payload = decode_token(access_token, settings, expected_type="access")
    except jwt.InvalidTokenError:
        return None

    auth_session = await get_auth_session(db_session, payload["session_id"])
    if auth_session is None or auth_session.revoked_at is not None or ensure_utc(auth_session.expires_at) < datetime.now(UTC):
        return None

    user = await get_user_by_id(db_session, payload["sub"])
    if user is None or user.is_blocked:
        return None
    return user


async def get_current_user(user: User | None = Depends(get_optional_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")
    return user


def get_request_ip_hash(request: Request) -> str | None:
    client_host = request.client.host if request.client else None
    return hash_ip_address(client_host, salt=settings.debug_hash_salt)
