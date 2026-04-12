from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import CartCb, NavCb


def _safe_id(obj) -> int:
    return int(getattr(obj, "id", 0) or 0)


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


def games_kb(games: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    games = games or []

    for game in games:
        game_id = _safe_id(game)
        title = getattr(game, "title", f"Игра #{game_id}")
        builder.button(text=title, callback_data=f"game:{game_id}")

    if games:
        builder.adjust(1)

    builder.button(text="🔙 В меню", callback_data=NavCb(target="home").pack())
    builder.adjust(1)
    return builder.as_markup()


def categories_kb(game_id: int, categories: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    categories = categories or []

    for category in categories:
        category_id = _safe_id(category)
        title = getattr(category, "title", f"Категория #{category_id}")
        builder.button(text=title, callback_data=f"cat:{game_id}:{category_id}")

    if categories:
        builder.adjust(1)

    builder.button(text="🔙 К играм", callback_data=NavCb(target="games").pack())
    builder.button(text="🏠 В меню", callback_data=NavCb(target="home").pack())
    builder.adjust(1, 1)
    return builder.as_markup()


def products_kb(
    game_id: int,
    category_id: int,
    products: list | None = None,
    page: int = 1,
    has_prev: bool = False,
    has_next: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    products = products or []

    for product in products:
        product_id = _safe_id(product)
        title = getattr(product, "title", f"Товар #{product_id}")
        builder.button(text=title, callback_data=f"prod:{product_id}")

    if products:
        builder.adjust(1)

    if has_prev:
        builder.button(text="⬅️", callback_data=f"prodpage:{game_id}:{category_id}:{page - 1}")
    if has_next:
        builder.button(text="➡️", callback_data=f"prodpage:{game_id}:{category_id}:{page + 1}")

    if has_prev or has_next:
        builder.adjust(int(has_prev) + int(has_next))

    builder.button(text="🔙 К категориям", callback_data=f"game:{game_id}")
    builder.button(text="🏠 В меню", callback_data=NavCb(target="home").pack())
    builder.adjust(1, 1)
    return builder.as_markup()


def product_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="➕ Добавить в корзину", callback_data=f"buy:add:{product_id}")
    builder.button(text="⚡ Купить сразу", callback_data=f"buy:now:{product_id}")
    builder.button(text="🛒 Корзина", callback_data=NavCb(target="cart").pack())
    builder.button(text="🔙 Назад", callback_data=NavCb(target="games").pack())

    builder.adjust(1, 1, 2)
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

    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def back_home_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 В меню", callback_data=NavCb(target="home").pack())
    return builder.as_markup()
