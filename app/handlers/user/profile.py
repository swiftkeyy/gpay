from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, Referral, User
from app.services.referral import ReferralService
from app.utils.callbacks import NavCb
from app.utils.texts import profile_text

router = Router(name='user_profile')


@router.callback_query(NavCb.filter(F.target == 'profile'))
async def profile_view(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    orders_count = int(await session.scalar(select(func.count()).select_from(Order).where(Order.user_id == db_user.id)) or 0)
    total_spent = await session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.user_id == db_user.id))
    referral_code = await ReferralService(session).get_or_create_user_ref_code(db_user)
    text = profile_text(db_user, orders_count, Decimal(total_spent or 0), referral_code)
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'ref'))
async def referral_view(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    referral_code = await ReferralService(session).get_or_create_user_ref_code(db_user)
    bot_username = await __import__('app.services.settings', fromlist=['SettingsService']).SettingsService(session).get('bot_username', 'game_pay_bot')
    text = (
        '🤝 <b>Реферальная система</b>\n\n'
        f'Ваш код: <code>{referral_code}</code>\n'
        f'Ссылка: https://t.me/{bot_username}?start=ref_{db_user.id}'
    )
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()
