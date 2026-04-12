from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.core.config import get_settings
from app.keyboards.admin import admin_main_kb, back_kb
from app.models import Admin
from app.utils.callbacks import NavCb

router = Router(name="admin_panel")
settings = get_settings()


def _has_access(admin: Admin | None, user_id: int) -> bool:
    return admin is not None or user_id in {
        settings.super_admin_tg_id,
        settings.second_admin_tg_id,
    }


def _panel_text() -> str:
    return "👮 <b>Админ-панель</b>\n\nВыберите раздел:"


def _section_text(title: str) -> str:
    return f"👮 <b>{title}</b>\n\nРаздел открыт."


@router.message(Command("admin"))
async def admin_command(message: Message, admin: Admin | None = None) -> None:
    user_id = message.from_user.id if message.from_user else 0

    if not _has_access(admin, user_id):
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        _panel_text(),
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


@router.callback_query(NavCb.filter(F.target == "admin_panel"))
async def admin_panel(callback: CallbackQuery, admin: Admin | None = None) -> None:
    user_id = callback.from_user.id if callback.from_user else 0

    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback.message:
        await callback.message.edit_text(
            _panel_text(),
            reply_markup=admin_main_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_orders"))
async def admin_orders(callback: CallbackQuery, admin: Admin | None = None) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("📦 Заказы"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_games"))
async def admin_games(callback: CallbackQuery, admin: Admin | None = None) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("🎮 Игры"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_categories"))
async def admin_categories(callback: CallbackQuery, admin: Admin | None = None) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("🗂 Категории"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_products"))
async def admin_products(callback: CallbackQuery, admin: Admin | None = None) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("🛍 Товары"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_prices"))
async def admin_prices(callback: CallbackQuery, admin: Admin | None = None) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("💸 Цены"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()
