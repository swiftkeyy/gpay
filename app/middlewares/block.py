from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select

from app.models import User


class BlockMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session = data.get("session")
        tg_user = getattr(event, "from_user", None)

        if session is None or tg_user is None:
            return await handler(event, data)

        result = await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
        user = result.scalar_one_or_none()

        if user and user.is_blocked:
            text = "🚫 Ваш аккаунт заблокирован."
            if user.block_reason:
                text += f"\nПричина: {user.block_reason}"

            if isinstance(event, Message):
                await event.answer(text)
                return None

            if isinstance(event, CallbackQuery):
                await event.answer("Аккаунт заблокирован", show_alert=True)
                try:
                    await event.message.answer(text)
                except Exception:
                    pass
                return None

        return await handler(event, data)
