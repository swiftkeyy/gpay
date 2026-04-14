from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Cart, CartItem
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    model = Cart
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_or_create_active(self, user_id: int) -> Cart:
        result = await self.session.execute(
            select(Cart).where(Cart.user_id == user_id)
        )
        cart = result.scalar_one_or_none()
        if cart:
            return cart

        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.flush()
        return cart

    async def get_with_items(self, user_id: int) -> Cart | None:
        result = await self.session.execute(
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product),
            )
            .where(Cart.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def clear(self, user_id: int) -> None:
        cart = await self.get_with_items(user_id)
        if not cart:
            return

        for item in list(cart.items):
            await self.session.delete(item)

        await self.session.flush()


class CartItemRepository(BaseRepository[CartItem]):
    model = CartItem
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_cart_and_product(self, cart_id: int, product_id: int) -> CartItem | None:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, item_id: int) -> CartItem | None:
        result = await self.session.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.id == item_id)
        )
        return result.scalar_one_or_none()
