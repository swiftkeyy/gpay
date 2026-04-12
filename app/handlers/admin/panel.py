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


def admin_panel_text() -> str:
    return "👮 <b>Админ-панель</b>\n\nВыберите раздел управления:"


def _section_text(title: str) -> str:
    return (
        f"👮 <b>{title}</b>\n\n"
        "Раздел подключён.\n"
        "Дальше можно добавлять CRUD-логику и списки сущностей."
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


@router.callback_query(NavCb.filter(F.target == "admin_panel"))
async def admin_panel_callback(
    callback: CallbackQuery,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    has_access = admin is not None or user_id in {
        settings.super_admin_tg_id,
        settings.second_admin_tg_id,
    }

    if not has_access:
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback.message:
        await callback.message.edit_text(
            admin_panel_text(),
            reply_markup=admin_main_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_orders"))
async def admin_orders_section(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("📦 Заказы"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_games"))
async def admin_games_section(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("🎮 Игры"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_categories"))
async def admin_categories_section(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("🗂 Категории"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_products"))
async def admin_products_section(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("🛍 Товары"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "admin_prices"))
async def admin_prices_section(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text(
            _section_text("💸 Цены"),
            reply_markup=back_kb(),
            parse_mode="HTML",
        )
    await callback.answer()
