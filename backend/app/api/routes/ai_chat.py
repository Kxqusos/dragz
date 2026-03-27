from fastapi import APIRouter, HTTPException
import logging

from app.core.config import Settings
from app.schemas import AIChatRequest, AIChatResponse
from app.services.ai_chat import run_otc_chat


router = APIRouter(prefix="/api/ai-chat", tags=["ai-chat"])
settings = Settings()
logger = logging.getLogger(__name__)


@router.post("", response_model=AIChatResponse)
async def ai_chat(payload: AIChatRequest) -> AIChatResponse:
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages are required")

    logger.info("ai_chat_request message_count=%d", len(payload.messages))
    response = AIChatResponse.model_validate(await run_otc_chat(payload.messages, settings))
    logger.info("ai_chat_response scope_status=%s warnings=%s", response.scope_status, response.warnings)
    return response
