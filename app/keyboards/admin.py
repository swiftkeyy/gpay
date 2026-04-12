from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import NavCb


def admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    b.button(text="📦 Заказы", callback_data=NavCb(target="admin_orders").pack())
    b.button(text="🎮 Игры", callback_data=NavCb(target="admin_games").pack())
    b.button(text="🗂 Категории", callback_data=NavCb(target="admin_categories").pack())
    b.button(text="🛍 Товары", callback_data=NavCb(target="admin_products").pack())
    b.button(text="💸 Цены", callback_data=NavCb(target="admin_prices").pack())

    b.adjust(1)
    return b.as_markup()


def back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=NavCb(target="admin_panel").pack())
    return b.as_markup()
