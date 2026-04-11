from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Cart, CartItem
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    model = Cart

    async def get_or_create_active(self, user_id: int) -> Cart:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id, Cart.is_active.is_(True))
            .options(joinedload(Cart.items).joinedload(CartItem.product))
            .with_for_update()
        )
        cart = await self.session.scalar(stmt)
        if cart:
            return cart
        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.flush()
        return cart

    async def get_full_active(self, user_id: int) -> Cart | None:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id, Cart.is_active.is_(True))
            .options(joinedload(Cart.items).joinedload(CartItem.product))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()


class CartItemRepository(BaseRepository[CartItem]):
    model = CartItem
