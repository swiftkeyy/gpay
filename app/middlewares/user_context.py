from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
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

        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user
        else:
            tg_user = getattr(event, "from_user", None)

        if session is None or tg_user is None:
            data["db_user"] = None
            data["admin"] = None
            return await handler(event, data)

        result = await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
        db_user = result.scalar_one_or_none()

        if db_user is None:
            db_user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                is_blocked=False,
                block_reason=None,
                personal_discount_percent=0,
                referral_code=f"REF{tg_user.id}",
            )
            session.add(db_user)
            await session.flush()
        else:
            changed = False
            if db_user.username != tg_user.username:
                db_user.username = tg_user.username
                changed = True
            if db_user.first_name != tg_user.first_name:
                db_user.first_name = tg_user.first_name
                changed = True
            if db_user.last_name != tg_user.last_name:
                db_user.last_name = tg_user.last_name
                changed = True
            if changed:
                await session.flush()

        data["db_user"] = db_user

        admin_result = await session.execute(
            select(Admin).where(
                Admin.user_id == db_user.id,
                Admin.is_active.is_(True),
            )
        )
        data["admin"] = admin_result.scalar_one_or_none()

        return await handler(event, data)
