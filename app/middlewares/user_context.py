from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select

from app.models import Admin, User


class UserContextMiddleware(BaseMiddleware):
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
        db_user = result.scalar_one_or_none()

        if db_user is not None:
            data["db_user"] = db_user

            admin_result = await session.execute(
                select(Admin).where(
                    Admin.user_id == db_user.id,
                    Admin.is_active.is_(True),
                )
            )
            admin = admin_result.scalar_one_or_none()
            data["admin"] = admin
        else:
            data["db_user"] = None
            data["admin"] = None

        return await handler(event, data)
