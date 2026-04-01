from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AIConversation, AIMessage, SearchHistoryEntry
from app.schemas import (
    AIChatResponse,
    AIConversationItemPayload,
    AIConversationMeta,
    AIHistoryResponse,
    AIConversationPayload,
    SearchHistoryItem,
    SearchHistoryResponse,
)


async def add_search_history(
    session: AsyncSession,
    *,
    user_id: str,
    query: str,
    metadata: dict | None = None,
) -> None:
    session.add(
        SearchHistoryEntry(
            user_id=user_id,
            query=query,
            metadata_json=metadata or {},
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


async def merge_search_history(
    session: AsyncSession,
    *,
    user_id: str,
    items: list[SearchHistoryItem],
) -> None:
    for item in items:
        await add_search_history(session, user_id=user_id, query=item.query, metadata=item.metadata)


async def list_search_history(session: AsyncSession, *, user_id: str, limit: int = 20) -> SearchHistoryResponse:
    result = await session.execute(
        select(SearchHistoryEntry)
        .where(SearchHistoryEntry.user_id == user_id)
        .order_by(SearchHistoryEntry.created_at.desc(), SearchHistoryEntry.id.desc())
        .limit(limit)
    )
    return SearchHistoryResponse(
        items=[
            SearchHistoryItem(
                query=item.query,
                created_at=item.created_at.isoformat(),
                metadata=item.metadata_json or {},
            )
            for item in result.scalars().all()
        ]
    )


async def replace_latest_ai_conversation(
    session: AsyncSession,
    *,
    user_id: str,
    items: list[AIConversationItemPayload],
) -> None:
    if not items:
        return

    result = await session.execute(
        select(AIConversation)
        .where(AIConversation.user_id == user_id)
        .order_by(AIConversation.updated_at.desc(), AIConversation.id.desc())
    )
    conversation = result.scalars().first()
    now = datetime.now(UTC)
    title = next((item.content[:120] for item in items if item.role == "user"), items[0].content[:120])

    if conversation is None:
        conversation = AIConversation(
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now,
        )
        session.add(conversation)
        await session.flush()
    else:
        conversation.title = title
        conversation.updated_at = now
        await session.execute(delete(AIMessage).where(AIMessage.conversation_id == conversation.id))

    for index, item in enumerate(items):
        session.add(
            AIMessage(
                conversation_id=conversation.id,
                order_index=index,
                role=item.role,
                content=item.content,
                meta_json=item.meta.model_dump() if item.meta is not None else None,
                created_at=now,
            )
        )

    await session.commit()


async def merge_guest_ai_conversation(
    session: AsyncSession,
    *,
    user_id: str,
    items: list[AIConversationItemPayload],
) -> None:
    await replace_latest_ai_conversation(session, user_id=user_id, items=items)


async def sync_ai_chat_history(
    session: AsyncSession,
    *,
    user_id: str,
    request_messages,
    response: AIChatResponse,
) -> None:
    assistant_meta = AIConversationMeta(
        scope_status=response.scope_status,
        warnings=response.warnings,
        recommended_otc_drugs=response.recommended_otc_drugs,
        handoff_cta=response.handoff_cta,
    )
    items = [
        AIConversationItemPayload(role=message.role, content=message.content)
        for message in request_messages
    ]
    items.append(
        AIConversationItemPayload(
            role="assistant",
            content=response.message,
            meta=assistant_meta,
        )
    )
    await replace_latest_ai_conversation(session, user_id=user_id, items=items)


async def list_ai_history(session: AsyncSession, *, user_id: str, limit: int = 10) -> AIHistoryResponse:
    result = await session.execute(
        select(AIConversation)
        .where(AIConversation.user_id == user_id)
        .order_by(AIConversation.updated_at.desc(), AIConversation.id.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()
    items: list[AIConversationPayload] = []
    for conversation in conversations:
        messages_result = await session.execute(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.order_index.asc(), AIMessage.id.asc())
        )
        items.append(
            AIConversationPayload(
                id=conversation.id,
                created_at=conversation.created_at.isoformat(),
                messages=[
                    AIConversationItemPayload(
                        role=message.role,
                        content=message.content,
                        meta=AIConversationMeta.model_validate(message.meta_json)
                        if message.meta_json
                        else None,
                    )
                    for message in messages_result.scalars().all()
                ],
            )
        )
    return AIHistoryResponse(items=items)
