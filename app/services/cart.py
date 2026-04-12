from __future__ import annotations

from decimal import Decimal

from app.models import CartItem, Product, User
from app.repositories.cart import CartItemRepository, CartRepository
from app.services.pricing import PricingService


class CartService:
    def __init__(self, session) -> None:
        self.session = session
        self.cart_repo = CartRepository(session)
        self.cart_item_repo = CartItemRepository(session)
        self.pricing_service = PricingService(session)

    async def get_cart(self, user_id: int | None):
        if not user_id:
            return None
        return await self.cart_repo.get_with_items(user_id)

    async def add_item(self, user_id: int, product: Product, quantity: int = 1) -> CartItem:
        if quantity < 1:
            quantity = 1

        cart = await self.cart_repo.get_or_create_active(user_id)
        item = await self.cart_item_repo.get_by_cart_and_product(cart.id, product.id)

        if item:
            item.quantity += quantity
            await self.session.flush()
            return item

        item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=quantity,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def change_quantity(self, item_id: int, delta: int) -> CartItem | None:
        item = await self.cart_item_repo.get_by_id(item_id)
        if not item:
            return None

        item.quantity += delta
        if item.quantity <= 0:
            await self.session.delete(item)
            await self.session.flush()
            return None

        await self.session.flush()
        return item

    async def set_quantity(self, item_id: int, quantity: int) -> CartItem | None:
        item = await self.cart_item_repo.get_by_id(item_id)
        if not item:
            return None

        if quantity <= 0:
            await self.session.delete(item)
            await self.session.flush()
            return None

        item.quantity = quantity
        await self.session.flush()
        return item

    async def remove_item(self, item_id: int) -> bool:
        item = await self.cart_item_repo.get_by_id(item_id)
        if not item:
            return False

        await self.session.delete(item)
        await self.session.flush()
        return True

    async def clear_cart(self, user_id: int | None) -> None:
        if not user_id:
            return
        await self.cart_repo.clear(user_id)

    async def clear(self, user_id: int | None) -> None:
        await self.clear_cart(user_id)

    async def get_cart_totals(
        self,
        user: User | None,
        promo_code=None,
    ) -> dict:
        if user is None or getattr(user, "id", None) is None:
            return {
                "items": [],
                "subtotal": Decimal("0.00"),
                "discount": Decimal("0.00"),
                "total": Decimal("0.00"),
                "currency_code": "RUB",
            }

        cart = await self.cart_repo.get_with_items(user.id)
        if not cart or not cart.items:
            return {
                "items": [],
                "subtotal": Decimal("0.00"),
                "discount": Decimal("0.00"),
                "total": Decimal("0.00"),
                "currency_code": "RUB",
            }

        items_data = []
        subtotal = Decimal("0.00")
        total = Decimal("0.00")
        currency_code = "RUB"

        for item in cart.items:
            if not item.product:
                continue

            quote = await self.pricing_service.calculate_cart_item_price(
                product=item.product,
                quantity=item.quantity,
                user=user,
                promo_code=promo_code,
            )

            items_data.append(
                {
                    "item": item,
                    "product": item.product,
                    "quote": quote,
                }
            )

            subtotal += quote.base_price
            total += quote.final_price
            currency_code = quote.currency_code

        discount = subtotal - total
        if discount < Decimal("0.00"):
            discount = Decimal("0.00")

        return {
            "items": items_data,
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "currency_code": currency_code,
        }
