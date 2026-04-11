from __future__ import annotations

from decimal import Decimal
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Referral, ReferralReward, User
from app.repositories.settings import ReferralRepository, ReferralRewardRepository
from app.services.settings import SettingsService


class ReferralService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ReferralRepository(session)
        self.reward_repo = ReferralRewardRepository(session)
        self.settings_service = SettingsService(session)

    def generate_ref_code(self) -> str:
        return secrets.token_hex(4).upper()

    async def get_or_create_user_ref_code(self, user: User) -> str:
        stmt = select(Referral.referral_code).where(Referral.referrer_user_id == user.id).limit(1)
        existing = await self.session.scalar(stmt)
        return existing or f'GP{user.id:06d}'

    async def register_referral(self, referrer: User, referred: User) -> None:
        count = await self.session.scalar(select(func.count()).select_from(Referral).where(Referral.referred_user_id == referred.id))
        if int(count or 0) > 0 or referrer.id == referred.id:
            return
        await self.repo.create(
            referrer_user_id=referrer.id,
            referred_user_id=referred.id,
            referral_code=await self.get_or_create_user_ref_code(referrer),
        )

    async def reward_first_purchase(self, referred_user_id: int, order_id: int, order_total: Decimal) -> None:
        stmt = select(Referral).where(Referral.referred_user_id == referred_user_id, Referral.is_rewarded.is_(False)).limit(1)
        referral = await self.session.scalar(stmt)
        if referral is None:
            return
        percent = Decimal(await self.settings_service.get('referral_reward_percent', 5))
        amount = (order_total * percent / Decimal('100')).quantize(Decimal('0.01'))
        await self.reward_repo.create(
            referral_id=referral.id,
            referrer_user_id=referral.referrer_user_id,
            referred_user_id=referred_user_id,
            order_id=order_id,
            amount=amount,
            description='Reward for first purchase of invited user.',
        )
        referral.first_order_id = order_id
        referral.is_rewarded = True
        await self.session.flush()
