from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, PromoCode, User
from app.repositories.promo import PromoCodeRepository, PromoCodeUsageRepository


class PromoValidationError(ValueError):
    pass


class PromoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PromoCodeRepository(session)
        self.usage_repo = PromoCodeUsageRepository(session)

    async def validate_code(self, code: str, *, user: User, product_ids: list[int], game_ids: list[int]) -> PromoCode:
        promo = await self.repo.get_by_code(code)
        if promo is None or not promo.is_enabled:
            raise PromoValidationError('Промокод не найден или отключён.')

        now = datetime.now(timezone.utc)
        if promo.starts_at and promo.starts_at > now:
            raise PromoValidationError('Промокод ещё не активен.')
        if promo.ends_at and promo.ends_at < now:
            raise PromoValidationError('Срок действия промокода истёк.')
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            raise PromoValidationError('Лимит использования промокода исчерпан.')
        if promo.game_id and promo.game_id not in game_ids:
            raise PromoValidationError('Промокод не подходит для выбранной игры.')
        if promo.product_id and promo.product_id not in product_ids:
            raise PromoValidationError('Промокод не подходит для выбранного товара.')
        if promo.only_new_users:
            orders_count = await self.session.scalar(select(func.count()).select_from(Order).where(Order.user_id == user.id))
            if int(orders_count or 0) > 0:
                raise PromoValidationError('Промокод только для новых пользователей.')
        return promo

    async def mark_used(self, promo_code_id: int, user_id: int, order_id: int) -> None:
        promo = await self.repo.get(promo_code_id)
        if promo is None:
            return
        promo.used_count += 1
        await self.usage_repo.create(promo_code_id=promo_code_id, user_id=user_id, order_id=order_id)
