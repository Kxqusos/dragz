from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.dependencies import get_db_session
from app.schemas import AIHistoryResponse, SearchHistoryResponse
from app.services.history import list_ai_history, list_search_history


router = APIRouter(tags=["history"])


@router.get("/api/history/search", response_model=SearchHistoryResponse)
async def get_search_history(
    current_user=Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SearchHistoryResponse:
    return await list_search_history(db_session, user_id=current_user.id)


@router.get("/api/history/ai", response_model=AIHistoryResponse)
async def get_ai_history(
    current_user=Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> AIHistoryResponse:
    return await list_ai_history(db_session, user_id=current_user.id)
