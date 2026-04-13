from __future__ import annotations

from decimal import Decimal

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import AdminCb, NavCb


def admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📦 Заказы", callback_data=AdminCb(section="orders", action="list").pack())
    b.button(text="🎮 Игры", callback_data=AdminCb(section="games", action="list").pack())
    b.button(text="🗂 Категории", callback_data=AdminCb(section="categories", action="list").pack())
    b.button(text="🛍 Товары", callback_data=AdminCb(section="products", action="list").pack())
    b.button(text="💸 Цены", callback_data=AdminCb(section="prices", action="list").pack())
    b.button(text="🎁 Промокоды", callback_data=AdminCb(section="promos", action="list").pack())
    b.button(text="📢 Рассылки", callback_data=AdminCb(section="broadcasts", action="list").pack())
    b.button(text="⚙️ Настройки", callback_data=AdminCb(section="settings", action="list").pack())
    b.button(text="👥 Пользователи", callback_data=AdminCb(section="users", action="list").pack())
    b.button(text="📊 Статистика", callback_data=AdminCb(section="stats", action="list").pack())
    b.button(text="🧾 Логи", callback_data=AdminCb(section="logs", action="list").pack())
    b.button(text="🏠 В меню", callback_data=NavCb(target="home").pack())
    b.adjust(2, 2, 2, 2, 2, 1, 1)
    return b.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    return b.as_markup()


def _status_mark(active: bool) -> str:
    return "🟢" if active else "⚪️"


def games_admin_kb(games: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for game in games:
        b.button(
            text=f"{_status_mark(game.is_active)} {game.title}",
            callback_data=AdminCb(section="games", action="view", entity_id=game.id).pack(),
        )
    b.button(text="➕ Добавить игру", callback_data=AdminCb(section="games", action="create").pack())
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(1)
    return b.as_markup()


def game_actions_kb(game_id: int, is_active: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Переименовать", callback_data=AdminCb(section="games", action="edit", entity_id=game_id).pack())
    b.button(text="🗂 Категории", callback_data=AdminCb(section="categories", action="list", entity_id=game_id).pack())
    b.button(text="🔄 Вкл/выкл", callback_data=AdminCb(section="games", action="toggle", entity_id=game_id).pack())
    b.button(text="🗑 Удалить", callback_data=AdminCb(section="games", action="delete_confirm", entity_id=game_id).pack())
    b.button(text="🔙 К играм", callback_data=AdminCb(section="games", action="list").pack())
    b.adjust(1)
    return b.as_markup()


def categories_admin_kb(categories: list, *, game_id: int | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for category in categories:
        game_title = getattr(getattr(category, "game", None), "title", f"game:{category.game_id}")
        b.button(
            text=f"{_status_mark(category.is_active)} {category.title} · {game_title}",
            callback_data=AdminCb(section="categories", action="view", entity_id=category.id).pack(),
        )
    b.button(
        text="➕ Добавить категорию",
        callback_data=AdminCb(section="categories", action="create", entity_id=game_id).pack(),
    )
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(1)
    return b.as_markup()


def category_actions_kb(category_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Переименовать", callback_data=AdminCb(section="categories", action="edit", entity_id=category_id).pack())
    b.button(text="🛍 Товары", callback_data=AdminCb(section="products", action="list", entity_id=category_id).pack())
    b.button(text="🔄 Вкл/выкл", callback_data=AdminCb(section="categories", action="toggle", entity_id=category_id).pack())
    b.button(text="🗑 Удалить", callback_data=AdminCb(section="categories", action="delete_confirm", entity_id=category_id).pack())
    b.button(text="🔙 К категориям", callback_data=AdminCb(section="categories", action="list").pack())
    b.adjust(1)
    return b.as_markup()


def products_admin_kb(products: list, *, category_id: int | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for product in products:
        category_title = getattr(getattr(product, "category", None), "title", f"cat:{product.category_id}")
        b.button(
            text=f"{_status_mark(product.is_active)} {product.title} · {category_title}",
            callback_data=AdminCb(section="products", action="view", entity_id=product.id).pack(),
        )
    b.button(
        text="➕ Добавить товар",
        callback_data=AdminCb(section="products", action="create", entity_id=category_id).pack(),
    )
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(1)
    return b.as_markup()


def product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Переименовать", callback_data=AdminCb(section="products", action="edit", entity_id=product_id).pack())
    b.button(text="💸 Цена", callback_data=AdminCb(section="prices", action="set", entity_id=product_id).pack())
    b.button(text="🔄 Вкл/выкл", callback_data=AdminCb(section="products", action="toggle", entity_id=product_id).pack())
    b.button(text="🗑 Удалить", callback_data=AdminCb(section="products", action="delete_confirm", entity_id=product_id).pack())
    b.button(text="🔙 К товарам", callback_data=AdminCb(section="products", action="list").pack())
    b.adjust(1)
    return b.as_markup()


def prices_admin_kb(rows: list[tuple]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for product, price in rows:
        amount = "-"
        if price is not None:
            amount = f"{Decimal(price.base_price):.2f} {price.currency_code}"
        b.button(
            text=f"💸 {product.title} · {amount}",
            callback_data=AdminCb(section="prices", action="set", entity_id=product.id).pack(),
        )
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(1)
    return b.as_markup()


def orders_admin_kb(orders: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for order in orders:
        b.button(
            text=f"📦 {order.order_number} · {order.status}",
            callback_data=AdminCb(section="orders", action="view", entity_id=order.id).pack(),
        )
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(1)
    return b.as_markup()


def order_admin_actions_kb(order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for action, label in [
        ("waiting_payment", "⏳ Ожидает оплату"),
        ("paid", "✅ Оплачен"),
        ("processing", "🛠 В обработке"),
        ("fulfilled", "📬 Выдан"),
        ("completed", "🏁 Завершён"),
        ("canceled", "❌ Отменён"),
    ]:
        b.button(text=label, callback_data=AdminCb(section="orders", action=action, entity_id=order_id).pack())
    b.button(text="🔙 К заказам", callback_data=AdminCb(section="orders", action="list").pack())
    b.adjust(1)
    return b.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    return admin_main_kb()


def back_kb() -> InlineKeyboardMarkup:
    return admin_back_kb()
