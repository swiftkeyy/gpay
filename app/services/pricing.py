from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Price, Product, PromoCode, PromoType, User


@dataclass(slots=True)
class PriceCalculationResult:
    base_price: Decimal
    product_discount_amount: Decimal
    promo_discount_amount: Decimal
    personal_discount_amount: Decimal
    final_price: Decimal
    currency_code: str
    applied_promo_code: str | None = None
    details: dict[str, Any] | None = None


class PricingService:
    async def get_active_price(
        self,
        session: AsyncSession,
        product_id: int,
    ) -> Price | None:
        result = await session.execute(
            select(Price)
            .where(
                Price.product_id == product_id,
                Price.is_active.is_(True),
            )
            .order_by(Price.id.desc())
        )
        return result.scalars().first()

    async def calculate_product_price(
        self,
        session: AsyncSession,
        *,
        product: Product,
        user: User | None = None,
        promo_code: PromoCode | None = None,
        quantity: int = 1,
    ) -> PriceCalculationResult:
        if quantity < 1:
            quantity = 1

        active_price = await self.get_active_price(session, product.id)
        if active_price is None:
            raise ValueError("Active price for product not found")

        base_unit_price = Decimal(active_price.base_price)
        currency_code = active_price.currency_code

        discounted_unit_price = (
            Decimal(active_price.discounted_price)
            if active_price.discounted_price is not None
            else base_unit_price
        )

        product_discount_amount = (base_unit_price - discounted_unit_price) * quantity
        subtotal_after_product_discount = discounted_unit_price * quantity

        personal_discount_amount = Decimal("0.00")
        if user and getattr(user, "personal_discount_percent", 0):
            percent = Decimal(user.personal_discount_percent) / Decimal("100")
            personal_discount_amount = (subtotal_after_product_discount * percent).quantize(Decimal("0.01"))

        subtotal_after_personal = subtotal_after_product_discount - personal_discount_amount
        if subtotal_after_personal < Decimal("0.00"):
            subtotal_after_personal = Decimal("0.00")

        promo_discount_amount = Decimal("0.00")
        applied_promo_code: str | None = None

        if promo_code and getattr(promo_code, "is_active", False):
            if promo_code.promo_type == PromoType.PERCENT:
                percent = Decimal(promo_code.value) / Decimal("100")
                promo_discount_amount = (subtotal_after_personal * percent).quantize(Decimal("0.01"))
            elif promo_code.promo_type == PromoType.FIXED:
                promo_discount_amount = Decimal(promo_code.value).quantize(Decimal("0.01"))

            if promo_discount_amount > subtotal_after_personal:
                promo_discount_amount = subtotal_after_personal

            applied_promo_code = promo_code.code

        final_price = subtotal_after_personal - promo_discount_amount
        if final_price < Decimal("0.00"):
            final_price = Decimal("0.00")

        return PriceCalculationResult(
            base_price=(base_unit_price * quantity).quantize(Decimal("0.01")),
            product_discount_amount=product_discount_amount.quantize(Decimal("0.01")),
            promo_discount_amount=promo_discount_amount.quantize(Decimal("0.01")),
            personal_discount_amount=personal_discount_amount.quantize(Decimal("0.01")),
            final_price=final_price.quantize(Decimal("0.01")),
            currency_code=currency_code,
            applied_promo_code=applied_promo_code,
            details={
                "product_id": product.id,
                "quantity": quantity,
                "base_unit_price": str(base_unit_price),
                "discounted_unit_price": str(discounted_unit_price),
            },
        )

    async def calculate_cart_item_price(
        self,
        session: AsyncSession,
        *,
        product: Product,
        quantity: int,
        user: User | None = None,
        promo_code: PromoCode | None = None,
    ) -> PriceCalculationResult:
        return await self.calculate_product_price(
            session,
            product=product,
            user=user,
            promo_code=promo_code,
            quantity=quantity,
        )
