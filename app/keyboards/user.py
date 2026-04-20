from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import CartCb, NavCb


def _safe_id(obj) -> int:
    return int(getattr(obj, "id", 0) or 0)


def main_menu_kb(*, is_admin: bool = False, webapp_url: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # WebApp button - first and most prominent
    if webapp_url:
        from aiogram.types import WebAppInfo
        builder.button(
            text="🛍️ Открыть магазин",
            web_app=WebAppInfo(url=webapp_url)
        )

    builder.button(text="🎮 Игры", callback_data=NavCb(target="games").pack())
    builder.button(text="🛒 Корзина", callback_data=NavCb(target="cart").pack())
    builder.button(text="📦 Мои заказы", callback_data=NavCb(target="orders_current").pack())
    builder.button(text="🕘 История заказов", callback_data=NavCb(target="orders_history").pack())
    builder.button(text="🏪 Продавать", callback_data=NavCb(target="seller").pack())
    builder.button(text="💼 Мои сделки", callback_data=NavCb(target="deals").pack())
    builder.button(text="🎁 Промокод", callback_data=NavCb(target="promo").pack())
    builder.button(text="⭐ Отзывы", callback_data=NavCb(target="reviews").pack())
    builder.button(text="👤 Профиль", callback_data=NavCb(target="profile").pack())
    builder.button(text="🤝 Реферальная система", callback_data=NavCb(target="ref").pack())
    builder.button(text="🆘 Поддержка", callback_data=NavCb(target="support").pack())
    builder.button(text="ℹ️ Информация / Правила", callback_data=NavCb(target="info").pack())

    if is_admin:
        builder.button(text="👮 Админка", callback_data=NavCb(target="admin_panel").pack())
        if webapp_url:
            builder.adjust(1, 2, 2, 2, 2, 2, 1, 1, 1)  # WebApp button on its own row
        else:
            builder.adjust(2, 2, 2, 2, 2, 1, 1, 1)
    else:
        if webapp_url:
            builder.adjust(1, 2, 2, 2, 2, 2, 1, 1)  # WebApp button on its own row
        else:
            builder.adjust(2, 2, 2, 2, 2, 1, 1)
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


def orders_kb(orders: list | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    orders = orders or []

    for order in orders:
        order_id = _safe_id(order)
        order_number = getattr(order, "order_number", f"#{order_id}")
        builder.button(text=f"📦 {order_number}", callback_data=f"order:{order_id}")

    if orders:
        builder.adjust(1)

    builder.button(text="🔙 В меню", callback_data=NavCb(target="home").pack())
    builder.adjust(1)
    return builder.as_markup()


def order_actions_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Повторить заказ", callback_data=f"order:repeat:{order_id}")
    builder.button(text="🕘 История статусов", callback_data=f"order:history:{order_id}")
    builder.button(text="🔙 К заказам", callback_data=NavCb(target="orders_current").pack())
    builder.adjust(1)
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

    builder.button(text="🗑 Очистить", callback_data=CartCb(action="clear").pack())
    builder.button(text="🎁 Применить промокод", callback_data=NavCb(target="promo").pack())
    builder.button(text="✅ Оформить заказ", callback_data=NavCb(target="checkout").pack())
    builder.button(text="🔙 Назад", callback_data=NavCb(target="home").pack())

    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def back_home_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 В меню", callback_data=NavCb(target="home").pack())
    return builder.as_markup()



def get_seller_menu_kb() -> InlineKeyboardMarkup:
    """Seller menu keyboard"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Мои лоты", callback_data="seller:my_lots")
    builder.button(text="➕ Добавить лот", callback_data="seller:add_lot")
    builder.button(text="💰 Баланс", callback_data="seller:balance")
    builder.button(text="💸 Вывести средства", callback_data="seller:withdraw")
    builder.button(text="📊 Статистика", callback_data="seller:stats")
    builder.button(text="💼 Мои продажи", callback_data="seller:sales")
    builder.button(text="🔙 В меню", callback_data=NavCb(target="home").pack())
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_seller_lots_kb(lots: list) -> InlineKeyboardMarkup:
    """Seller lots list keyboard"""
    builder = InlineKeyboardBuilder()
    
    for lot in lots:
        status_emoji = {
            "draft": "📝",
            "active": "✅",
            "paused": "⏸",
            "out_of_stock": "❌"
        }
        emoji = status_emoji.get(lot.status.value, "📦")
        builder.button(
            text=f"{emoji} {lot.title} - {lot.price} ₽",
            callback_data=f"seller:lot:{lot.id}"
        )
    
    builder.adjust(1)
    builder.button(text="➕ Добавить лот", callback_data="seller:add_lot")
    builder.button(text="🔙 Назад", callback_data="seller:my_lots")
    builder.adjust(1, 1)
    return builder.as_markup()


def get_lot_actions_kb(lot_id: int, status: str) -> InlineKeyboardMarkup:
    """Lot actions keyboard"""
    builder = InlineKeyboardBuilder()
    
    if status == "draft":
        builder.button(text="✅ Активировать", callback_data=f"seller:lot_action:activate:{lot_id}")
    elif status == "active":
        builder.button(text="⏸ Приостановить", callback_data=f"seller:lot_action:pause:{lot_id}")
    elif status == "paused":
        builder.button(text="✅ Активировать", callback_data=f"seller:lot_action:activate:{lot_id}")
    
    builder.button(text="✏️ Редактировать", callback_data=f"seller:lot_action:edit:{lot_id}")
    builder.button(text="📦 Добавить товар", callback_data=f"seller:lot_action:add_stock:{lot_id}")
    builder.button(text="🗑 Удалить", callback_data=f"seller:lot_action:delete:{lot_id}")
    builder.button(text="🔙 К лотам", callback_data="seller:my_lots")
    
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def get_deals_list_kb(buyer_deals: list, seller_deals: list) -> InlineKeyboardMarkup:
    """Deals list keyboard"""
    builder = InlineKeyboardBuilder()
    
    if buyer_deals:
        builder.button(text="🛒 Мои покупки", callback_data="deals:buyer")
    
    if seller_deals:
        builder.button(text="💼 Мои продажи", callback_data="deals:seller")
    
    # Show first few deals
    for deal in (buyer_deals + seller_deals)[:10]:
        status_emoji = {
            "created": "🆕",
            "paid": "💳",
            "in_progress": "⏳",
            "waiting_confirmation": "⏰",
            "completed": "✅",
            "canceled": "❌",
            "dispute": "⚠️"
        }
        emoji = status_emoji.get(deal.status.value, "📦")
        builder.button(
            text=f"{emoji} Заказ #{deal.order_id}",
            callback_data=f"deal:{deal.id}"
        )
    
    builder.adjust(2)
    builder.button(text="🔙 В меню", callback_data=NavCb(target="home").pack())
    builder.adjust(1)
    return builder.as_markup()


def get_deal_kb(deal_id: int, status: str, is_buyer: bool) -> InlineKeyboardMarkup:
    """Deal actions keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💬 Чат", callback_data=f"deal_chat:{deal_id}")
    
    if is_buyer and status == "waiting_confirmation":
        builder.button(text="✅ Подтвердить получение", callback_data=f"deal_confirm:{deal_id}")
        builder.button(text="⚠️ Открыть спор", callback_data=f"deal_dispute:{deal_id}")
    
    if not is_buyer and status == "in_progress":
        builder.button(text="📦 Доставить товар", callback_data=f"deal_deliver:{deal_id}")
    
    if status in ["created", "paid", "in_progress", "waiting_confirmation"]:
        builder.button(text="❌ Отменить", callback_data=f"deal_cancel:{deal_id}")
    
    builder.button(text="🔙 К сделкам", callback_data="deals:list")
    
    builder.adjust(1)
    return builder.as_markup()


def get_deal_chat_kb(deal_id: int) -> InlineKeyboardMarkup:
    """Deal chat keyboard"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 К сделке", callback_data=f"deal:{deal_id}")
    return builder.as_markup()


def get_lots_by_product_kb(product_id: int, lots: list) -> InlineKeyboardMarkup:
    """Lots selection keyboard for product"""
    builder = InlineKeyboardBuilder()
    
    for lot in lots:
        seller_name = lot.seller.shop_name if hasattr(lot, 'seller') else "Продавец"
        rating = f"{float(lot.seller.rating):.1f}⭐" if hasattr(lot, 'seller') else ""
        builder.button(
            text=f"{seller_name} - {lot.price} ₽ {rating}",
            callback_data=f"lot:buy:{lot.id}"
        )
    
    builder.adjust(1)
    builder.button(text="🔙 Назад", callback_data=f"prod:{product_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_lot_detail_kb(lot_id: int, seller_id: int) -> InlineKeyboardMarkup:
    """Lot detail keyboard"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Купить", callback_data=f"lot:purchase:{lot_id}")
    builder.button(text="⭐ Продавец", callback_data=f"seller:view:{seller_id}")
    builder.button(text="❤️ В избранное", callback_data=f"lot:favorite:{lot_id}")
    builder.button(text="🔙 Назад", callback_data="lots:list")
    builder.adjust(1, 2, 1)
    return builder.as_markup()
