from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import get_settings
from app.keyboards.admin import admin_main_kb
from app.models import Admin

router = Router(name="admin_panel")
settings = get_settings()


def admin_panel_text() -> str:
    return (
        "👮 <b>Админ-панель</b>\n\n"
        "Выберите раздел управления:"
    )


@router.message(Command("admin"))
async def admin_panel_command(
    message: Message,
    admin: Admin | None = None,
) -> None:
    user_id = message.from_user.id if message.from_user else 0

    has_access = admin is not None or user_id in {
        settings.super_admin_tg_id,
        settings.second_admin_tg_id,
    }

    if not has_access:
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        admin_panel_text(),
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )
