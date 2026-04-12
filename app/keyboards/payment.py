from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import NavCb, PaymentCb


def payment_methods_kb(order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⭐ Оплатить Stars", callback_data=PaymentCb(action="stars", order_id=order_id).pack())
    b.button(text="💎 Оплатить Crypto Bot", callback_data=PaymentCb(action="cryptobot", order_id=order_id).pack())
    b.button(text="💬 Manual", callback_data=PaymentCb(action="manual", order_id=order_id).pack())
    b.button(text="🛒 В корзину", callback_data=NavCb(target="cart").pack())
    b.button(text="🏠 В меню", callback_data=NavCb(target="home").pack())
    b.adjust(1)
    return b.as_markup()
