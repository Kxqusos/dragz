from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.dependencies import get_db_session
from app.schemas import AuthMessageResponse, MergeGuestStateRequest
from app.services.cart import merge_cart_items
from app.services.history import merge_guest_ai_conversation, merge_search_history


router = APIRouter(tags=["state"])


@router.post("/api/state/merge-guest", response_model=AuthMessageResponse)
async def merge_guest_state(
    payload: MergeGuestStateRequest,
    current_user=Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> AuthMessageResponse:
    await merge_cart_items(db_session, user_id=current_user.id, items=payload.cart_items)
    await merge_search_history(db_session, user_id=current_user.id, items=payload.search_history)
    await merge_guest_ai_conversation(db_session, user_id=current_user.id, items=payload.ai_conversation)
    return AuthMessageResponse(message="guest state merged")
