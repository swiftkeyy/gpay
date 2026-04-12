from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings import BotSettingRepository


class SettingsService:
    def __init__(self, repo: BotSettingRepository | None = None) -> None:
        self.repo = repo or BotSettingRepository()

    async def get(
        self,
        session: AsyncSession,
        key: str,
        default: str | None = None,
    ) -> str | None:
        setting = await self.repo.get_by_key(session, key)
        if setting is None:
            return default
        return setting.value

    async def set(
        self,
        session: AsyncSession,
        *,
        key: str,
        value: str,
        description: str | None = None,
        is_public: bool = False,
    ) -> str:
        setting = await self.repo.set_value(
            session,
            key=key,
            value=value,
            description=description,
            is_public=is_public,
        )
        return setting.value
