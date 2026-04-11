from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings import SettingsService
from app.utils.callbacks import NavCb

router = Router(name='user_support')


@router.callback_query(NavCb.filter(F.target == 'support'))
async def support_view(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = SettingsService(session)
    contact = await settings.get('support_contact', '@support')
    faq = await settings.get('faq_text', 'По вопросам оплаты и заказа напишите в поддержку.')
    text = f'🆘 <b>Поддержка</b>\n\nКонтакт: {contact}\n\n{faq}'
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'info'))
async def info_view(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = SettingsService(session)
    rules = await settings.get('rules_text', 'Соблюдайте правила магазина.')
    payment = await settings.get('payment_methods_text', 'Ручная оплата через оператора.')
    text = f'ℹ️ <b>Информация / Правила</b>\n\n{rules}\n\n💳 Способы оплаты:\n{payment}'
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()
