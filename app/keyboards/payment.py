from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import NavCb, PaymentCb


def payment_methods_kb(
    order_id: int,
    *,
    stars_enabled: bool = True,
    cryptobot_enabled: bool = True,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if stars_enabled:
        b.button(text="⭐ Оплатить Stars", callback_data=PaymentCb(action="stars", order_id=order_id).pack())
    if cryptobot_enabled:
        b.button(text="💎 Оплатить Crypto Bot", callback_data=PaymentCb(action="cryptobot", order_id=order_id).pack())
    b.button(text="💬 Ручная оплата", callback_data=PaymentCb(action="manual", order_id=order_id).pack())
    b.button(text="📦 Мои заказы", callback_data=NavCb(target="orders_current").pack())
    b.button(text="🏠 В меню", callback_data=NavCb(target="home").pack())
    b.adjust(1)
    return b.as_markup()


def cryptobot_invoice_kb(invoice_url: str, order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Открыть счёт Crypto Bot", url=invoice_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=PaymentCb(action="cryptocheck", order_id=order_id).pack())],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data=NavCb(target="orders_current").pack())],
            [InlineKeyboardButton(text="🏠 В меню", callback_data=NavCb(target="home").pack())],
        ]
    )
