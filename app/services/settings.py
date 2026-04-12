from __future__ import annotations

from app.repositories.settings import BotSettingRepository


class SettingsService:
    def __init__(self, session) -> None:
        self.repo = BotSettingRepository(session)

    async def get(
        self,
        key: str,
        default: str | None = None,
    ) -> str | None:
        setting = await self.repo.get_by_key(key)
        if setting is None:
            return default
        return setting.value

    async def set(
        self,
        *,
        key: str,
        value: str,
        description: str | None = None,
        is_public: bool = False,
    ) -> str:
        setting = await self.repo.set_value(
            key=key,
            value=value,
            description=description,
            is_public=is_public,
        )
        return setting.value
