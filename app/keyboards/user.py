from __future__ import annotations

from collections.abc import Iterable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import CartCb, NavCb


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="🎮 Игры", callback_data=NavCb(target="games").pack())
    builder.button(text="🛒 Корзина", callback_data=NavCb(target="cart").pack())
    builder.button(text="📦 Мои заказы", callback_data=NavCb(target="orders").pack())
    builder.button(text="🕘 История заказов", callback_data=NavCb(target="history").pack())
    builder.button(text="🎁 Промокод", callback_data=NavCb(target="promo").pack())
    builder.button(text="⭐ Отзывы", callback_data=NavCb(target="reviews").pack())
    builder.button(text="👤 Профиль", callback_data=NavCb(target="profile").pack())
    builder.button(text="🤝 Реферальная система", callback_data=NavCb(target="referrals").pack())
    builder.button(text="🆘 Поддержка", callback_data=NavCb(target="support").pack())
    builder.button(text="ℹ️ Информация / Правила", callback_data=NavCb(target="info").pack())

    builder.adjust(2, 2, 2, 2, 1, 1)
    return builder.as_markup()


def _extract_cart_items(cart_or_items) -> list:
    if cart_or_items is None:
        return []

    if isinstance(cart_or_items, list):
        return cart_or_items

    items = getattr(cart_or_items, "items", None)
    if items is None:
        return []

    if isinstance(items, list):
        return items

    return list(items)


def cart_kb(cart_or_items=None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    items = _extract_cart_items(cart_or_items)

    for item in items:
        item_id = getattr(item, "id", None)
        if item_id is None:
            continue

        builder.button(text="➕", callback_data=CartCb(action="inc", item_id=item_id).pack())
        builder.button(text="➖", callback_data=CartCb(action="dec", item_id=item_id).pack())
        builder.button(text="❌ Удалить", callback_data=CartCb(action="del", item_id=item_id).pack())

    if items:
        builder.adjust(*([3] * len(items)))

    builder.button(text="🗑 Очистить", callback_data=CartCb(action="clear", item_id=0).pack())
    builder.button(text="🎁 Применить промокод", callback_data=NavCb(target="promo").pack())
    builder.button(text="✅ Оформить заказ", callback_data=NavCb(target="checkout").pack())
    builder.button(text="🔙 Назад", callback_data=NavCb(target="home").pack())

    builder.adjust(3, 1, 1, 1, 1)
    return builder.as_markup()


def back_home_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 В меню", callback_data=NavCb(target="home").pack())
    return builder.as_markup()
