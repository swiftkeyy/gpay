from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import NavCb


def _safe_id(obj) -> int:
    return int(getattr(obj, "id", 0) or 0)


def admin_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="📦 Заказы", callback_data=NavCb(target="admin_orders").pack())
    builder.button(text="🛍 Товары", callback_data=NavCb(target="admin_products").pack())
    builder.button(text="🎮 Игры", callback_data=NavCb(target="admin_games").pack())
    builder.button(text="🗂 Категории", callback_data=NavCb(target="admin_categories").pack())
    builder.button(text="💸 Цены", callback_data=NavCb(target="admin_prices").pack())
    builder.button(text="🖼 Картинки", callback_data=NavCb(target="admin_media").pack())
    builder.button(text="👥 Пользователи", callback_data=NavCb(target="admin_users").pack())
    builder.button(text="🚫 Блокировки", callback_data=NavCb(target="admin_blocks").pack())
    builder.button(text="🎁 Промокоды", callback_data=NavCb(target="admin_promos").pack())
    builder.button(text="⭐ Отзывы", callback_data=NavCb(target="admin_reviews").pack())
    builder.button(text="🤝 Рефералка", callback_data=NavCb(target="admin_referrals").pack())
    builder.button(text="📢 Рассылка", callback_data=NavCb(target="admin_broadcasts").pack())
    builder.button(text="📊 Статистика", callback_data=NavCb(target="admin_stats").pack())
    builder.button(text="⚙️ Настройки", callback_data=NavCb(target="admin_settings").pack())
    builder.button(text="🧾 Логи", callback_data=NavCb(target="admin_logs").pack())
    builder.button(text="👮 Админы", callback_data=NavCb(target="admin_admins").pack())
    builder.button(text="🏠 В меню", callback_data=NavCb(target="home").pack())

    builder.adjust(2, 2, 2, 2, 2, 2, 2, 2, 1)
    return builder.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    return builder.as_markup()


def admin_yes_no_kb(yes_target: str, no_target: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=NavCb(target=yes_target).pack())
    builder.button(text="❌ Нет", callback_data=NavCb(target=no_target).pack())
    builder.adjust(2)
    return builder.as_markup()


def games_admin_kb(games: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    games = games or []

    for game in games:
        game_id = _safe_id(game)
        title = getattr(game, "title", f"Игра #{game_id}")
        builder.button(text=title, callback_data=f"adm:game:{game_id}")
        builder.button(text="✏️", callback_data=f"adm:game_edit:{game_id}")
        builder.button(text="🗑", callback_data=f"adm:game_del:{game_id}")

    if games:
        builder.adjust(*([3] * len(games)))

    builder.button(text="➕ Добавить игру", callback_data="adm:game_add")
    builder.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    builder.adjust(1, 1)
    return builder.as_markup()


def game_actions_kb(game_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"adm:game_edit:{game_id}")
    builder.button(text="🗂 Категории", callback_data=f"adm:game_categories:{game_id}")
    builder.button(text="🛍 Товары", callback_data=f"adm:game_products:{game_id}")
    builder.button(text="🗑 Удалить", callback_data=f"adm:game_del:{game_id}")
    builder.button(text="🔙 К играм", callback_data=NavCb(target="admin_games").pack())
    builder.adjust(1)
    return builder.as_markup()


def categories_admin_kb(categories: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    categories = categories or []

    for category in categories:
        category_id = _safe_id(category)
        title = getattr(category, "title", f"Категория #{category_id}")
        builder.button(text=title, callback_data=f"adm:cat:{category_id}")
        builder.button(text="✏️", callback_data=f"adm:cat_edit:{category_id}")
        builder.button(text="🗑", callback_data=f"adm:cat_del:{category_id}")

    if categories:
        builder.adjust(*([3] * len(categories)))

    builder.button(text="➕ Добавить категорию", callback_data="adm:cat_add")
    builder.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    builder.adjust(1, 1)
    return builder.as_markup()


def category_actions_kb(category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"adm:cat_edit:{category_id}")
    builder.button(text="🛍 Товары", callback_data=f"adm:cat_products:{category_id}")
    builder.button(text="🗑 Удалить", callback_data=f"adm:cat_del:{category_id}")
    builder.button(text="🔙 К категориям", callback_data=NavCb(target="admin_categories").pack())
    builder.adjust(1)
    return builder.as_markup()


def products_admin_kb(products: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    products = products or []

    for product in products:
        product_id = _safe_id(product)
        title = getattr(product, "title", f"Товар #{product_id}")
        builder.button(text=title, callback_data=f"adm:prod:{product_id}")
        builder.button(text="✏️", callback_data=f"adm:prod_edit:{product_id}")
        builder.button(text="🗑", callback_data=f"adm:prod_del:{product_id}")

    if products:
        builder.adjust(*([3] * len(products)))

    builder.button(text="➕ Добавить товар", callback_data="adm:prod_add")
    builder.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    builder.adjust(1, 1)
    return builder.as_markup()


def product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"adm:prod_edit:{product_id}")
    builder.button(text="💸 Цена", callback_data=f"adm:price:{product_id}")
    builder.button(text="🖼 Картинка", callback_data=f"adm:prod_media:{product_id}")
    builder.button(text="🗑 Удалить", callback_data=f"adm:prod_del:{product_id}")
    builder.button(text="🔙 К товарам", callback_data=NavCb(target="admin_products").pack())
    builder.adjust(1)
    return builder.as_markup()


def prices_admin_kb(products: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    products = products or []

    for product in products:
        product_id = _safe_id(product)
        title = getattr(product, "title", f"Товар #{product_id}")
        builder.button(text=f"💸 {title}", callback_data=f"adm:price:{product_id}")

    if products:
        builder.adjust(1)

    builder.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    builder.adjust(1)
    return builder.as_markup()


def price_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить цену", callback_data=f"adm:price_edit:{product_id}")
    builder.button(text="🔙 К ценам", callback_data=NavCb(target="admin_prices").pack())
    builder.adjust(1)
    return builder.as_markup()


def promos_admin_kb(promos: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    promos = promos or []

    for promo in promos:
        promo_id = _safe_id(promo)
        code = getattr(promo, "code", f"PROMO-{promo_id}")
        builder.button(text=code, callback_data=f"adm:promo:{promo_id}")
        builder.button(text="✏️", callback_data=f"adm:promo_edit:{promo_id}")
        builder.button(text="🗑", callback_data=f"adm:promo_del:{promo_id}")

    if promos:
        builder.adjust(*([3] * len(promos)))

    builder.button(text="➕ Добавить промокод", callback_data="adm:promo_add")
    builder.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    builder.adjust(1, 1)
    return builder.as_markup()


def promo_actions_kb(promo_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"adm:promo_edit:{promo_id}")
    builder.button(text="🗑 Удалить", callback_data=f"adm:promo_del:{promo_id}")
    builder.button(text="🔙 К промокодам", callback_data=NavCb(target="admin_promos").pack())
    builder.adjust(1)
    return builder.as_markup()


def orders_admin_kb(orders: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    orders = orders or []

    for order in orders:
        order_id = _safe_id(order)
        order_number = getattr(order, "order_number", f"#{order_id}")
        builder.button(text=f"📦 {order_number}", callback_data=f"adm:order:{order_id}")

    if orders:
        builder.adjust(1)

    builder.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    builder.adjust(1)
    return builder.as_markup()


def order_actions_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Paid", callback_data=f"adm:order_status:{order_id}:paid")
    builder.button(text="⚙️ Processing", callback_data=f"adm:order_status:{order_id}:processing")
    builder.button(text="📦 Fulfilled", callback_data=f"adm:order_status:{order_id}:fulfilled")
    builder.button(text="✔️ Completed", callback_data=f"adm:order_status:{order_id}:completed")
    builder.button(text="❌ Canceled", callback_data=f"adm:order_status:{order_id}:canceled")
    builder.button(text="🔙 К заказам", callback_data=NavCb(target="admin_orders").pack())
    builder.adjust(1)
    return builder.as_markup()


def admin_pagination_kb(
    prev_target: str | None = None,
    next_target: str | None = None,
    back_target: str = "admin_panel",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if prev_target:
        builder.button(text="⬅️", callback_data=NavCb(target=prev_target).pack())
    if next_target:
        builder.button(text="➡️", callback_data=NavCb(target=next_target).pack())

    if prev_target or next_target:
        count = int(bool(prev_target)) + int(bool(next_target))
        builder.adjust(count)

    builder.button(text="🔙 Назад", callback_data=NavCb(target=back_target).pack())
    builder.adjust(1)
    return builder.as_markup()

def admin_menu_kb() -> InlineKeyboardMarkup:
    return admin_main_kb()
