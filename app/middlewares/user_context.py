from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware

from app.repositories.users import UserRepository


class UserContextMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Any, dict[str, Any]], Awaitable[Any]], event: Any, data: dict[str, Any]) -> Any:
        session = data['session']
        event_from_user = data.get('event_from_user')
        if event_from_user:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(event_from_user.id)
            if user is None:
                user = await repo.create(
                    telegram_id=event_from_user.id,
                    username=event_from_user.username,
                    first_name=event_from_user.first_name,
                    last_name=event_from_user.last_name,
                )
            else:
                user.username = event_from_user.username
                user.first_name = event_from_user.first_name
                user.last_name = event_from_user.last_name
            data['db_user'] = user
        return await handler(event, data)
