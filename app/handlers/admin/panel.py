from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.admin import admin_main_kb
from app.models import Admin

router = Router(name="admin_panel")


def admin_panel_text() -> str:
    return (
        "👮 <b>Админ-панель</b>\n\n"
        "Выберите раздел управления:"
    )


@router.message(Command("admin"))
async def admin_panel_command(
    message: Message,
    admin: Admin | None = None,
    session: AsyncSession | None = None,
) -> None:
    if admin is None:
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        admin_panel_text(),
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )
