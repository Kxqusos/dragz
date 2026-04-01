from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DebugEvent
from app.schemas import DebugEventRequest, DebugEventResponse, DebugEventsResponse


def hash_ip_address(ip_address: str | None, *, salt: str) -> str | None:
    if not ip_address:
        return None
    return hashlib.sha256(f"{salt}:{ip_address}".encode("utf-8")).hexdigest()


def generate_anonymous_id() -> str:
    return uuid.uuid4().hex


async def create_debug_event(
    session: AsyncSession,
    *,
    event: DebugEventRequest,
    anonymous_id: str | None,
    user_id: str | None,
    request_id: str | None,
    user_agent: str | None,
    ip_hash: str | None,
) -> DebugEvent:
    record = DebugEvent(
        user_id=user_id,
        anonymous_id=anonymous_id,
        event=event.event,
        route=event.route,
        request_id=request_id,
        user_agent=user_agent,
        ip_hash=ip_hash,
        metadata_json=event.metadata,
        created_at=datetime.now(UTC),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def list_debug_events(session: AsyncSession, *, limit: int = 100) -> DebugEventsResponse:
    result = await session.execute(
        select(DebugEvent)
        .order_by(DebugEvent.created_at.desc(), DebugEvent.id.desc())
        .limit(limit)
    )
    return DebugEventsResponse(
        items=[
            DebugEventResponse(
                id=item.id,
                event=item.event,
                route=item.route,
                request_id=item.request_id,
                user_agent=item.user_agent,
                ip_hash=item.ip_hash,
                anonymous_id=item.anonymous_id,
                metadata=item.metadata_json or {},
                created_at=item.created_at.isoformat(),
            )
            for item in result.scalars().all()
        ]
    )
