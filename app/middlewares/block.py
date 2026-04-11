from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class BlockCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Any, dict[str, Any]], Awaitable[Any]], event: Any, data: dict[str, Any]) -> Any:
        user = data.get('db_user')
        if user and user.is_blocked:
            text = '⛔ Ваш доступ ограничен. Обратитесь в поддержку.'
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
                return None
            if isinstance(event, Message):
                await event.answer(text)
                return None
        return await handler(event, data)
