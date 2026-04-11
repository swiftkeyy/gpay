from __future__ import annotations

from sqlalchemy import select

from app.models import BotSetting, Broadcast, DiscountRule, Review, Referral, ReferralReward, AuditLog
from app.repositories.base import BaseRepository


class BotSettingRepository(BaseRepository[BotSetting]):
    model = BotSetting

    async def get_by_key(self, key: str) -> BotSetting | None:
        stmt = select(BotSetting).where(BotSetting.key == key)
        return await self.session.scalar(stmt)


class DiscountRuleRepository(BaseRepository[DiscountRule]):
    model = DiscountRule


class ReviewRepository(BaseRepository[Review]):
    model = Review


class ReferralRepository(BaseRepository[Referral]):
    model = Referral


class ReferralRewardRepository(BaseRepository[ReferralReward]):
    model = ReferralReward


class BroadcastRepository(BaseRepository[Broadcast]):
    model = Broadcast


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog
