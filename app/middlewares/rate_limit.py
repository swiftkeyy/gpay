from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, interval_seconds: float = 0.7):
        self.interval_seconds = interval_seconds
        self._storage: dict[tuple[int, str], float] = {}

    async def __call__(self, handler: Callable[[Any, dict[str, Any]], Awaitable[Any]], event: Any, data: dict[str, Any]) -> Any:
        event_from_user = data.get('event_from_user')
        if event_from_user is None:
            return await handler(event, data)
        key = (event_from_user.id, getattr(handler, '__name__', 'handler'))
        now = time.monotonic()
        prev = self._storage.get(key, 0)
        if now - prev < self.interval_seconds:
            if isinstance(event, CallbackQuery):
                await event.answer('Слишком быстро. Попробуйте ещё раз через секунду.', show_alert=False)
                return None
            if isinstance(event, Message):
                return None
        self._storage[key] = now
        return await handler(event, data)
