from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.dependencies import get_db_session
from app.schemas import AuthMessageResponse, CartResponse, MergeGuestStateRequest
from app.services.cart import list_cart_items, merge_cart_items


router = APIRouter(tags=["cart"])


@router.get("/api/cart", response_model=CartResponse)
async def get_cart(current_user=Depends(get_current_user), db_session: AsyncSession = Depends(get_db_session)) -> CartResponse:
    return await list_cart_items(db_session, user_id=current_user.id)


@router.put("/api/cart", response_model=AuthMessageResponse)
async def put_cart(
    payload: MergeGuestStateRequest,
    current_user=Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> AuthMessageResponse:
    await merge_cart_items(db_session, user_id=current_user.id, items=payload.cart_items)
    return AuthMessageResponse(message="cart updated")
