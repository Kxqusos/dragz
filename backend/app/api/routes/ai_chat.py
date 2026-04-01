from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_current_user
from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.db.models import User
from app.schemas import AIChatRequest, AIChatResponse
from app.services.history import sync_ai_chat_history
from app.services.ai_chat import run_otc_chat


router = APIRouter(prefix="/api/ai-chat", tags=["ai-chat"])
settings = Settings()
logger = logging.getLogger(__name__)


@router.post("", response_model=AIChatResponse)
async def ai_chat(
    payload: AIChatRequest,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> AIChatResponse:
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages are required")

    logger.info("ai_chat_request message_count=%d", len(payload.messages))
    response = AIChatResponse.model_validate(await run_otc_chat(payload.messages, settings))
    if current_user is not None:
        await sync_ai_chat_history(
            db_session,
            user_id=current_user.id,
            request_messages=payload.messages,
            response=response,
        )
    logger.info("ai_chat_response scope_status=%s warnings=%s", response.scope_status, response.warnings)
    return response
