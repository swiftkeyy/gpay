from __future__ import annotations

from decimal import Decimal

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import Order, Review, User
from app.models.enums import OrderStatus, ReviewStatus
from app.utils.callbacks import AdminCb, NavCb


STATUS_LABELS = {
    OrderStatus.NEW.value: "🆕 Новые",
    OrderStatus.WAITING_PAYMENT.value: "⏳ Ожидают оплату",
    OrderStatus.PAID.value: "✅ Оплачены",
    OrderStatus.PROCESSING.value: "🛠 В работе",
    OrderStatus.FULFILLED.value: "📬 Выданы",
    OrderStatus.COMPLETED.value: "🏁 Завершены",
    OrderStatus.CANCELED.value: "❌ Отменены",
    OrderStatus.DISPUTE.value: "⚠️ Споры",
    OrderStatus.FAILED.value: "🚫 Ошибки",
}


REVIEW_LABELS = {
    ReviewStatus.HIDDEN.value: "🙈 Скрыт",
    ReviewStatus.PUBLISHED.value: "✅ Опубликован",
    ReviewStatus.REJECTED.value: "❌ Отклонён",
}


def admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📦 Заказы", callback_data=AdminCb(section="orders", action="list").pack())
    b.button(text="🔎 Поиск заказа", callback_data=AdminCb(section="orders", action="search").pack())
    b.button(text="⚠️ Споры / возвраты", callback_data=AdminCb(section="claims", action="list").pack())
    b.button(text="⭐ Отзывы", callback_data=AdminCb(section="reviews", action="list").pack())
    b.button(text="👥 Пользователи", callback_data=AdminCb(section="users", action="list").pack())
    b.button(text="🔎 Поиск пользователя", callback_data=AdminCb(section="users", action="search").pack())
    b.button(text="🎮 Игры", callback_data=AdminCb(section="games", action="list").pack())
    b.button(text="🗂 Категории", callback_data=AdminCb(section="categories", action="list").pack())
    b.button(text="🛍 Товары", callback_data=AdminCb(section="products", action="list").pack())
    b.button(text="💸 Цены", callback_data=AdminCb(section="prices", action="list").pack())
    b.button(text="🎁 Промокоды", callback_data=AdminCb(section="promos", action="list").pack())
    b.button(text="📢 Рассылки", callback_data=AdminCb(section="broadcasts", action="list").pack())
    b.button(text="⚙️ Настройки", callback_data=AdminCb(section="settings", action="list").pack())
    b.button(text="📊 Статистика", callback_data=AdminCb(section="stats", action="list").pack())
    b.button(text="🧾 Логи", callback_data=AdminCb(section="logs", action="list").pack())
    b.button(text="👮 Админы", callback_data=AdminCb(section="admins", action="list").pack())
    b.button(text="🚫 Блокировки", callback_data=AdminCb(section="blocks", action="list").pack())
    b.button(text="🏠 В меню", callback_data=NavCb(target="home").pack())
    b.adjust(2, 2, 2, 2, 2, 2, 2, 2, 1)
    return b.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    return b.as_markup()


def orders_admin_kb(orders: list[Order], *, filter_status: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for order in orders:
        b.button(
            text=f"📦 {order.order_number} · {order.status}",
            callback_data=AdminCb(section="orders", action="view", entity_id=order.id).pack(),
        )

    b.button(text="🔎 Поиск заказа", callback_data=AdminCb(section="orders", action="search").pack())
    b.button(text="📋 Все", callback_data=AdminCb(section="orders", action="list").pack())
    b.button(text="⏳ Оплата", callback_data=AdminCb(section="orders", action="filter_waiting_payment").pack())
    b.button(text="✅ Оплачены", callback_data=AdminCb(section="orders", action="filter_paid").pack())
    b.button(text="🛠 В работе", callback_data=AdminCb(section="orders", action="filter_processing").pack())
    b.button(text="🏁 Завершены", callback_data=AdminCb(section="orders", action="filter_completed").pack())
    b.button(text="⚠️ Споры", callback_data=AdminCb(section="claims", action="list").pack())
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(*([1] * len(orders)), 2, 2, 2, 1, 1)
    return b.as_markup()


def order_admin_actions_kb(order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⏳ Ожидает оплату", callback_data=AdminCb(section="orders", action="waiting_payment", entity_id=order_id).pack())
    b.button(text="✅ Оплачен", callback_data=AdminCb(section="orders", action="paid", entity_id=order_id).pack())
    b.button(text="🛠 В обработке", callback_data=AdminCb(section="orders", action="processing", entity_id=order_id).pack())
    b.button(text="📬 Выдан", callback_data=AdminCb(section="orders", action="fulfilled", entity_id=order_id).pack())
    b.button(text="🏁 Завершён", callback_data=AdminCb(section="orders", action="completed", entity_id=order_id).pack())
    b.button(text="⚠️ Спор", callback_data=AdminCb(section="orders", action="dispute", entity_id=order_id).pack())
    b.button(text="↩️ Возврат/отмена", callback_data=AdminCb(section="orders", action="canceled", entity_id=order_id).pack())
    b.button(text="🔙 К заказам", callback_data=AdminCb(section="orders", action="list").pack())
    b.adjust(1)
    return b.as_markup()


def users_admin_kb(users: list[User]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for user in users:
        username = f"@{user.username}" if user.username else "без username"
        b.button(
            text=f"👤 {user.telegram_id} · {username}",
            callback_data=AdminCb(section="users", action="view", entity_id=user.id).pack(),
        )
    b.button(text="🔎 Поиск пользователя", callback_data=AdminCb(section="users", action="search").pack())
    b.button(text="🚫 Блокировки", callback_data=AdminCb(section="blocks", action="list").pack())
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(*([1] * len(users)), 1, 1, 1)
    return b.as_markup()


def user_card_kb(user_id: int, *, is_blocked: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if is_blocked:
        b.button(text="✅ Разблокировать", callback_data=AdminCb(section="users", action="unblock", entity_id=user_id).pack())
    else:
        b.button(text="🚫 Заблокировать", callback_data=AdminCb(section="users", action="block", entity_id=user_id).pack())
    b.button(text="📦 Заказы пользователя", callback_data=AdminCb(section="users", action="orders", entity_id=user_id).pack())
    b.button(text="🔙 К пользователям", callback_data=AdminCb(section="users", action="list").pack())
    b.adjust(1)
    return b.as_markup()


def reviews_admin_kb(reviews: list[Review], *, filter_status: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for review in reviews:
        b.button(
            text=f"⭐ {review.rating} · order #{review.order_id} · {review.status}",
            callback_data=AdminCb(section="reviews", action="view", entity_id=review.id).pack(),
        )
    b.button(text="🙈 Скрытые", callback_data=AdminCb(section="reviews", action="filter_hidden").pack())
    b.button(text="✅ Публик.", callback_data=AdminCb(section="reviews", action="filter_published").pack())
    b.button(text="❌ Отклонённые", callback_data=AdminCb(section="reviews", action="filter_rejected").pack())
    b.button(text="📋 Все", callback_data=AdminCb(section="reviews", action="list").pack())
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(*([1] * len(reviews)), 2, 2, 1)
    return b.as_markup()


def review_admin_actions_kb(review_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Опубликовать", callback_data=AdminCb(section="reviews", action="publish", entity_id=review_id).pack())
    b.button(text="🙈 Скрыть", callback_data=AdminCb(section="reviews", action="hide", entity_id=review_id).pack())
    b.button(text="❌ Отклонить", callback_data=AdminCb(section="reviews", action="reject", entity_id=review_id).pack())
    b.button(text="🔙 К отзывам", callback_data=AdminCb(section="reviews", action="list").pack())
    b.adjust(1)
    return b.as_markup()


def claims_admin_kb(orders: list[Order]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for order in orders:
        label = "⚠️" if order.status == OrderStatus.DISPUTE else "↩️"
        b.button(
            text=f"{label} {order.order_number} · {order.status}",
            callback_data=AdminCb(section="orders", action="view", entity_id=order.id).pack(),
        )
    b.button(text="⚠️ Только споры", callback_data=AdminCb(section="claims", action="filter_dispute").pack())
    b.button(text="↩️ Только отмены", callback_data=AdminCb(section="claims", action="filter_canceled").pack())
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(*([1] * len(orders)), 2, 1)
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


def admin_menu_kb() -> InlineKeyboardMarkup:
    return admin_main_kb()


def back_kb() -> InlineKeyboardMarkup:
    return admin_back_kb()
