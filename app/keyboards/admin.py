from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import NavCb


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
