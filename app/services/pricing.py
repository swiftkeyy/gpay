from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiscountRule, Price, Product, PromoCode, User
from app.models.enums import DiscountScope, PromoType
from app.repositories.catalog import PriceRepository


@dataclass(slots=True)
class PriceQuote:
    base_price: Decimal
    discount_amount: Decimal
    final_price: Decimal
    currency_code: str
    applied_rules: list[str]


class PricingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.price_repo = PriceRepository(session)

    async def get_product_price(self, product: Product, user: User | None = None, promo: PromoCode | None = None) -> PriceQuote:
        price = await self.price_repo.get_current_for_product(product.id)
        if price is None:
            base = Decimal('0.00')
            currency = 'RUB'
        else:
            base = Decimal(price.discounted_price or price.base_price)
            currency = price.currency_code

        applied_rules: list[str] = []
        discount_amount = Decimal('0.00')
        discount_amount += await self._apply_discount_rules(product, base, applied_rules, user)

        if user and user.personal_discount_percent > 0:
            personal_discount = (base * Decimal(user.personal_discount_percent) / Decimal('100')).quantize(Decimal('0.01'))
            if personal_discount > discount_amount:
                discount_amount = personal_discount
                applied_rules.append(f'personal:{user.personal_discount_percent}%')

        if promo:
            promo_discount = self._promo_discount(base, promo)
            if promo_discount > discount_amount:
                discount_amount = promo_discount
                applied_rules.append(f'promo:{promo.code}')

        final_price = max(Decimal('0.00'), base - discount_amount)
        return PriceQuote(base_price=base, discount_amount=discount_amount, final_price=final_price, currency_code=currency, applied_rules=applied_rules)

    async def _apply_discount_rules(self, product: Product, base: Decimal, applied: list[str], user: User | None) -> Decimal:
        now = datetime.now(timezone.utc)
        stmt = (
            select(DiscountRule)
            .where(DiscountRule.is_deleted.is_(False), DiscountRule.is_active.is_(True))
            .order_by(DiscountRule.priority.asc(), DiscountRule.id.asc())
        )
        rules = list(await self.session.scalars(stmt))
        best = Decimal('0.00')
        for rule in rules:
            if rule.starts_at and rule.starts_at > now:
                continue
            if rule.ends_at and rule.ends_at < now:
                continue
            if rule.scope == DiscountScope.GLOBAL:
                pass
            elif rule.scope == DiscountScope.GAME and rule.game_id != product.game_id:
                continue
            elif rule.scope == DiscountScope.PRODUCT and rule.product_id != product.id:
                continue
            elif rule.scope == DiscountScope.PERSONAL and (user is None or rule.user_id != user.id):
                continue
            elif rule.scope == DiscountScope.ACCUMULATIVE and (user is None):
                continue
            candidate = Decimal('0.00')
            if rule.percent:
                candidate = (base * Decimal(rule.percent) / Decimal('100')).quantize(Decimal('0.01'))
            elif rule.fixed_amount:
                candidate = Decimal(rule.fixed_amount)
            if candidate > best:
                best = candidate
                applied.append(f'rule:{rule.title}')
        return best

    def _promo_discount(self, base: Decimal, promo: PromoCode) -> Decimal:
        if promo.promo_type == PromoType.PERCENT:
            return (base * Decimal(promo.value) / Decimal('100')).quantize(Decimal('0.01'))
        return min(base, Decimal(promo.value))
