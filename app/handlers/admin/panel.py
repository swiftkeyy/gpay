from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.core.config import get_settings
from app.keyboards.admin import admin_main_kb
from app.models import Admin
from app.utils.callbacks import NavCb

router = Router(name="admin_panel")
settings = get_settings()


def _has_access(user_id: int, admin: Admin | None) -> bool:
    return admin is not None or user_id in {settings.super_admin_tg_id, settings.second_admin_tg_id}


def admin_panel_text() -> str:
    return "👮 <b>Админ-панель</b>\n\nВыберите раздел управления."


@router.message(Command("admin"))
async def admin_panel_command(message: Message, admin: Admin | None = None) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not _has_access(user_id, admin):
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        admin_panel_text(),
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


@router.callback_query(NavCb.filter(F.target == "admin_panel"))
async def admin_panel_callback(callback: CallbackQuery, admin: Admin | None = None) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(user_id, admin):
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback.message:
        await callback.message.edit_text(
            admin_panel_text(),
            reply_markup=admin_main_kb(),
            parse_mode="HTML",
        )
    await callback.answer()
