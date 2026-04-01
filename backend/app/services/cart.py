from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CartItem
from app.schemas import CartItemPayload, CartResponse


async def merge_cart_items(
    session: AsyncSession,
    *,
    user_id: str,
    items: list[CartItemPayload],
) -> None:
    now = datetime.now(UTC)
    for item in items:
        result = await session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.pharmacy_id == item.pharmacy_id,
                CartItem.matched_drug == item.matched_drug,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            session.add(
                CartItem(
                    user_id=user_id,
                    pharmacy_id=item.pharmacy_id,
                    pharmacy_name=item.pharmacy_name,
                    address=item.address,
                    lat=item.lat,
                    lon=item.lon,
                    price=item.price,
                    in_stock=item.in_stock,
                    quantity_label=item.quantity_label,
                    matched_drug=item.matched_drug,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            record.pharmacy_name = item.pharmacy_name
            record.address = item.address
            record.lat = item.lat
            record.lon = item.lon
            record.price = item.price
            record.in_stock = item.in_stock
            record.quantity_label = item.quantity_label
            record.updated_at = now
    await session.commit()


async def list_cart_items(session: AsyncSession, *, user_id: str) -> CartResponse:
    result = await session.execute(
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.updated_at.desc(), CartItem.id.desc())
    )
    return CartResponse(
        items=[
            CartItemPayload(
                pharmacy_id=item.pharmacy_id,
                pharmacy_name=item.pharmacy_name,
                address=item.address,
                lat=item.lat,
                lon=item.lon,
                price=item.price,
                in_stock=item.in_stock,
                quantity_label=item.quantity_label,
                matched_drug=item.matched_drug,
            )
            for item in result.scalars().all()
        ]
    )
