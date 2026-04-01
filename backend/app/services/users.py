from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.schemas import UserResponse
from app.services.auth import hash_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    normalized = normalize_email(email)
    result = await session.execute(select(User).where(User.email == normalized))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    is_email_verified: bool = False,
    role: str = "user",
    accepted_terms: bool = False,
) -> User:
    now = datetime.now(UTC)
    user = User(
        email=normalize_email(email),
        password_hash=hash_password(password),
        role=role,
        is_blocked=False,
        accepted_terms_at=now if accepted_terms else None,
        email_verified_at=now if is_email_verified else None,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_password(session: AsyncSession, user: User, password: str) -> User:
    user.password_hash = hash_password(password)
    user.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(user)
    return user


async def accept_terms(session: AsyncSession, user: User) -> User:
    now = datetime.now(UTC)
    user.accepted_terms_at = now
    user.updated_at = now
    await session.commit()
    await session.refresh(user)
    return user


async def mark_email_verified(session: AsyncSession, user: User, *, make_admin: bool = False) -> User:
    now = datetime.now(UTC)
    user.email_verified_at = now
    user.updated_at = now
    if make_admin:
        user.role = "admin"
    await session.commit()
    await session.refresh(user)
    return user


async def update_last_login(session: AsyncSession, user: User) -> User:
    user.last_login_at = datetime.now(UTC)
    user.updated_at = user.last_login_at
    await session.commit()
    await session.refresh(user)
    return user


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_blocked=user.is_blocked,
        is_email_verified=user.email_verified_at is not None,
        created_at=user.created_at.isoformat(),
    )
