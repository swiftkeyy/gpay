from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, interval_seconds: float = 0.7) -> None:
        self.interval_seconds = interval_seconds
        self._storage: dict[tuple[int, str], float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        event_from_user = data.get("event_from_user") or getattr(event, "from_user", None)
        if event_from_user is None or getattr(event_from_user, "id", None) is None:
            return await handler(event, data)

        callback_data = ""
        if isinstance(event, CallbackQuery):
            callback_data = event.data or ""

        handler_name = getattr(handler, "__name__", handler.__class__.__name__)
        key = (int(event_from_user.id), f"{handler_name}:{callback_data}")

        now = time.monotonic()
        prev = self._storage.get(key)
        if prev is not None and now - prev < self.interval_seconds:
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("Слишком быстро. Попробуйте ещё раз через секунду.", show_alert=False)
                except Exception:
                    pass
                return None

            if isinstance(event, Message):
                return None

        self._storage[key] = now

        if len(self._storage) > 10000:
            threshold = now - max(self.interval_seconds * 3, 5)
            self._storage = {k: ts for k, ts in self._storage.items() if ts >= threshold}

        return await handler(event, data)
