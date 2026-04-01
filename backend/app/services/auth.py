from __future__ import annotations

from datetime import UTC, datetime, timedelta
import secrets
import uuid

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from argon2.low_level import Type
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import AuthSession, EmailVerificationCode, PasswordResetCode, User


ACCESS_COOKIE_NAME = "tabletki_access_token"
REFRESH_COOKIE_NAME = "tabletki_refresh_token"
_PASSWORD_HASHER = PasswordHasher(type=Type.ID)


def hash_password(password: str) -> str:
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _PASSWORD_HASHER.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_code(code: str) -> str:
    return _PASSWORD_HASHER.hash(code)


def verify_code(code: str, code_hash: str) -> bool:
    try:
        return _PASSWORD_HASHER.verify(code_hash, code)
    except VerifyMismatchError:
        return False


def generate_numeric_code() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def _seconds_until_code_can_be_resent(
    session: AsyncSession,
    *,
    model,
    user_id: str,
    cooldown_seconds: int,
) -> int:
    result = await session.execute(
        select(model)
        .where(model.user_id == user_id)
        .order_by(model.id.desc())
    )
    record = result.scalars().first()
    if record is None:
        return 0
    elapsed_seconds = int((datetime.now(UTC) - ensure_utc(record.created_at)).total_seconds())
    return max(0, cooldown_seconds - elapsed_seconds)


def create_access_token(*, user: User, session_id: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user.id,
        "role": user.role,
        "session_id": session_id,
        "token_type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.auth_access_token_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, user: User, session_id: str, refresh_jti: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user.id,
        "role": user.role,
        "session_id": session_id,
        "jti": refresh_jti,
        "token_type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.auth_refresh_token_ttl_days)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings, *, expected_type: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("token_type") != expected_type:
        raise jwt.InvalidTokenError("unexpected token type")
    return payload


def set_auth_cookies(response, *, access_token: str, refresh_token: str, settings: Settings) -> None:
    common_kwargs = {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.auth_cookie_secure,
        "path": "/",
    }
    if settings.auth_cookie_domain:
        common_kwargs["domain"] = settings.auth_cookie_domain

    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access_token,
        max_age=settings.auth_access_token_ttl_minutes * 60,
        **common_kwargs,
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=settings.auth_refresh_token_ttl_days * 24 * 60 * 60,
        **common_kwargs,
    )


def clear_auth_cookies(response, settings: Settings) -> None:
    common_kwargs = {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.auth_cookie_secure,
        "path": "/",
    }
    if settings.auth_cookie_domain:
        common_kwargs["domain"] = settings.auth_cookie_domain

    response.delete_cookie(ACCESS_COOKIE_NAME, **common_kwargs)
    response.delete_cookie(REFRESH_COOKIE_NAME, **common_kwargs)


async def create_auth_session(
    session: AsyncSession,
    *,
    user_id: str,
    user_agent: str | None,
    ip_hash: str | None,
    settings: Settings,
) -> AuthSession:
    now = datetime.now(UTC)
    auth_session = AuthSession(
        user_id=user_id,
        refresh_jti=uuid.uuid4().hex,
        user_agent=user_agent,
        ip_hash=ip_hash,
        created_at=now,
        expires_at=now + timedelta(days=settings.auth_refresh_token_ttl_days),
    )
    session.add(auth_session)
    await session.commit()
    await session.refresh(auth_session)
    return auth_session


async def rotate_auth_session(
    session: AsyncSession,
    *,
    auth_session: AuthSession,
    settings: Settings,
) -> AuthSession:
    auth_session.refresh_jti = uuid.uuid4().hex
    auth_session.expires_at = datetime.now(UTC) + timedelta(days=settings.auth_refresh_token_ttl_days)
    await session.commit()
    await session.refresh(auth_session)
    return auth_session


async def revoke_auth_session(session: AsyncSession, auth_session: AuthSession) -> None:
    auth_session.revoked_at = datetime.now(UTC)
    await session.commit()


async def revoke_all_user_sessions(session: AsyncSession, user_id: str) -> None:
    result = await session.execute(select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)))
    for auth_session in result.scalars().all():
        auth_session.revoked_at = datetime.now(UTC)
    await session.commit()


async def get_auth_session(session: AsyncSession, session_id: str) -> AuthSession | None:
    result = await session.execute(select(AuthSession).where(AuthSession.id == session_id))
    return result.scalar_one_or_none()


async def create_email_verification_code(
    session: AsyncSession,
    *,
    user_id: str,
    settings: Settings,
) -> str:
    await session.execute(delete(EmailVerificationCode).where(EmailVerificationCode.user_id == user_id))
    code = generate_numeric_code()
    now = datetime.now(UTC)
    session.add(
        EmailVerificationCode(
            user_id=user_id,
            code_hash=hash_code(code),
            attempt_count=0,
            created_at=now,
            expires_at=now + timedelta(minutes=settings.auth_code_ttl_minutes),
        )
    )
    await session.commit()
    return code


async def seconds_until_verification_code_can_be_resent(
    session: AsyncSession,
    *,
    user_id: str,
    settings: Settings,
) -> int:
    return await _seconds_until_code_can_be_resent(
        session,
        model=EmailVerificationCode,
        user_id=user_id,
        cooldown_seconds=settings.auth_verification_code_resend_cooldown_seconds,
    )


async def create_password_reset_code(
    session: AsyncSession,
    *,
    user_id: str,
    settings: Settings,
) -> str:
    await session.execute(delete(PasswordResetCode).where(PasswordResetCode.user_id == user_id))
    code = generate_numeric_code()
    now = datetime.now(UTC)
    session.add(
        PasswordResetCode(
            user_id=user_id,
            code_hash=hash_code(code),
            attempt_count=0,
            created_at=now,
            expires_at=now + timedelta(minutes=settings.auth_code_ttl_minutes),
        )
    )
    await session.commit()
    return code


async def seconds_until_password_reset_code_can_be_resent(
    session: AsyncSession,
    *,
    user_id: str,
    settings: Settings,
) -> int:
    return await _seconds_until_code_can_be_resent(
        session,
        model=PasswordResetCode,
        user_id=user_id,
        cooldown_seconds=settings.auth_password_reset_code_cooldown_seconds,
    )


async def validate_email_verification_code(
    session: AsyncSession,
    *,
    user_id: str,
    code: str,
    settings: Settings,
) -> bool:
    result = await session.execute(
        select(EmailVerificationCode)
        .where(EmailVerificationCode.user_id == user_id)
        .order_by(EmailVerificationCode.id.desc())
    )
    record = result.scalars().first()
    if record is None:
        return False
    if record.consumed_at is not None or ensure_utc(record.expires_at) < datetime.now(UTC):
        return False
    if record.attempt_count >= settings.auth_code_max_attempts:
        return False
    if not verify_code(code, record.code_hash):
        record.attempt_count += 1
        await session.commit()
        return False
    record.consumed_at = datetime.now(UTC)
    await session.commit()
    return True


async def validate_password_reset_code(
    session: AsyncSession,
    *,
    user_id: str,
    code: str,
    settings: Settings,
) -> bool:
    result = await session.execute(
        select(PasswordResetCode)
        .where(PasswordResetCode.user_id == user_id)
        .order_by(PasswordResetCode.id.desc())
    )
    record = result.scalars().first()
    if record is None:
        return False
    if record.consumed_at is not None or ensure_utc(record.expires_at) < datetime.now(UTC):
        return False
    if record.attempt_count >= settings.auth_code_max_attempts:
        return False
    if not verify_code(code, record.code_hash):
        record.attempt_count += 1
        await session.commit()
        return False
    record.consumed_at = datetime.now(UTC)
    await session.commit()
    return True
