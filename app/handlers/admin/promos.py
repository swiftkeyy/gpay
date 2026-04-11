from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.models import PromoCode
from app.models.enums import PromoType
from app.repositories.promo import PromoCodeRepository
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb

router = Router(name='admin_promos')


@router.callback_query(AdminCb.filter(F.section == 'promos'), AdminPermissionFilter('promos.manage'))
async def promos(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext) -> None:
    repo = PromoCodeRepository(session)
    if callback_data.action == 'list':
        promos = await repo.list(limit=50)
        text = '🎁 <b>Промокоды</b>\n\n' + '\n'.join(f'• {p.code} | {p.promo_type} | {p.value}' for p in promos)
        text += '\n\nНажмите кнопку ниже, чтобы создать новый промокод.'
        await callback.message.edit_text(text, parse_mode='HTML')
        await callback.message.answer('Для создания введите сообщением: CODE;title;percent|fixed;value')
        await state.set_state(AdminCatalogStates.waiting_promo_code)
    await callback.answer()


@router.message(AdminCatalogStates.waiting_promo_code, AdminPermissionFilter('promos.manage'))
async def promo_create(message: Message, session: AsyncSession, state: FSMContext) -> None:
    try:
        code, title, promo_type, value = [part.strip() for part in (message.text or '').split(';', maxsplit=3)]
    except ValueError:
        await message.answer('Формат: CODE;title;percent|fixed;value')
        return
    promo = await PromoCodeRepository(session).create(
        code=code.upper(),
        title=title,
        promo_type=PromoType.PERCENT if promo_type == 'percent' else PromoType.FIXED,
        value=Decimal(value),
        is_enabled=True,
    )
    await state.clear()
    await message.answer(f'Промокод создан: {promo.code}')
