from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import ConfirmCb, NavCb


def back_button(target: str, entity_id: int = 0, page: int = 1) -> InlineKeyboardButton:
    return InlineKeyboardButton(text="🔙 Назад", callback_data=NavCb(target=target, entity_id=entity_id, page=page).pack())


def confirm_keyboard(action: str, entity_id: int, token: str, cancel_target: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=ConfirmCb(action=action, entity_id=entity_id, value=token).pack())
    builder.button(text="❌ Отмена", callback_data=NavCb(target=cancel_target).pack())
    builder.adjust(1)
    return builder.as_markup()
