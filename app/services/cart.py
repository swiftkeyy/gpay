from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cart, CartItem, Product, User
from app.repositories.cart import CartItemRepository, CartRepository
from app.services.pricing import PricingService


@dataclass(slots=True)
class CartTotals:
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    currency_code: str


class CartService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cart_repo = CartRepository(session)
        self.item_repo = CartItemRepository(session)
        self.pricing = PricingService(session)

    async def get_cart(self, user_id: int) -> Cart:
        return await self.cart_repo.get_or_create_active(user_id)

    async def add_item(self, user_id: int, product: Product, quantity: int = 1) -> Cart:
        cart = await self.cart_repo.get_or_create_active(user_id)
        for item in cart.items:
            if item.product_id == product.id:
                item.quantity += quantity
                cart.version += 1
                await self.session.flush()
                return cart
        self.session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity))
        cart.version += 1
        await self.session.flush()
        return cart

    async def change_quantity(self, user_id: int, product_id: int, delta: int) -> Cart:
        cart = await self.cart_repo.get_or_create_active(user_id)
        target = next((item for item in cart.items if item.product_id == product_id), None)
        if not target:
            return cart
        target.quantity += delta
        if target.quantity <= 0:
            await self.session.delete(target)
        cart.version += 1
        await self.session.flush()
        return cart

    async def remove_item(self, user_id: int, product_id: int) -> Cart:
        cart = await self.cart_repo.get_or_create_active(user_id)
        target = next((item for item in cart.items if item.product_id == product_id), None)
        if target:
            await self.session.delete(target)
            cart.version += 1
            await self.session.flush()
        return cart

    async def clear(self, user_id: int) -> Cart:
        cart = await self.cart_repo.get_or_create_active(user_id)
        for item in list(cart.items):
            await self.session.delete(item)
        cart.version += 1
        await self.session.flush()
        return cart

    async def compute_totals(self, cart: Cart, user: User, promo=None) -> CartTotals:
        subtotal = Decimal('0.00')
        total = Decimal('0.00')
        currency_code = 'RUB'
        for item in cart.items:
            quote = await self.pricing.get_product_price(item.product, user=user, promo=promo)
            subtotal += quote.base_price * item.quantity
            total += quote.final_price * item.quantity
            currency_code = quote.currency_code
        discount = subtotal - total
        return CartTotals(subtotal=subtotal, discount=discount, total=total, currency_code=currency_code)
