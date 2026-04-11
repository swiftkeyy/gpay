from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, BotSetting, Broadcast, Referral, ReferralReward, Review
from app.repositories.base import BaseRepository


class BotSettingRepository(BaseRepository[BotSetting]):
    model = BotSetting

    async def get_by_key(self, session: AsyncSession, key: str) -> BotSetting | None:
        result = await session.execute(
            select(BotSetting).where(BotSetting.key == key)
        )
        return result.scalar_one_or_none()

    async def set_value(
        self,
        session: AsyncSession,
        *,
        key: str,
        value: str,
        description: str | None = None,
        is_public: bool = False,
    ) -> BotSetting:
        setting = await self.get_by_key(session, key)
        if setting:
            setting.value = value
            if description is not None:
                setting.description = description
            setting.is_public = is_public
            await session.flush()
            return setting

        setting = BotSetting(
            key=key,
            value=value,
            description=description,
            is_public=is_public,
        )
        session.add(setting)
        await session.flush()
        return setting


class SettingsRepository(BotSettingRepository):
    pass


class BroadcastRepository(BaseRepository[Broadcast]):
    model = Broadcast

    async def get_by_id(self, session: AsyncSession, broadcast_id: int) -> Broadcast | None:
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        return result.scalar_one_or_none()


class ReviewRepository(BaseRepository[Review]):
    model = Review


class ReferralRepository(BaseRepository[Referral]):
    model = Referral


class ReferralRewardRepository(BaseRepository[ReferralReward]):
    model = ReferralReward


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog
