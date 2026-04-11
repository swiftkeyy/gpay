from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings import BotSettingRepository


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BotSettingRepository(session)

    async def get(self, key: str, default: Any = None) -> Any:
        setting = await self.repo.get_by_key(key)
        return default if setting is None else setting.value

    async def set(self, key: str, value: Any, description: str | None = None) -> None:
        setting = await self.repo.get_by_key(key)
        if setting:
            setting.value = value
            if description is not None:
                setting.description = description
        else:
            await self.repo.create(key=key, value=value, description=description)
        await self.session.flush()

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for key in keys:
            values[key] = await self.get(key)
        return values
