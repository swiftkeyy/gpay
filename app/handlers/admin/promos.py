from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
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
        text = '🎁 <b>Промокоды</b>\n\n' + ('\n'.join(f'• {p.code} | {p.promo_type} | {p.value}' for p in promos) or 'Промокодов пока нет.')
        text += '\n\nДля создания введите сообщением: CODE;percent|fixed;value'
        await callback.message.edit_text(text, parse_mode='HTML')
        await state.set_state(AdminCatalogStates.waiting_promo_code)
    await callback.answer()


@router.message(AdminCatalogStates.waiting_promo_code, AdminPermissionFilter('promos.manage'))
async def promo_create(message: Message, session: AsyncSession, state: FSMContext) -> None:
    try:
        code, promo_type_raw, value_raw = [part.strip() for part in (message.text or '').split(';', maxsplit=2)]
        value = Decimal(value_raw)
    except (ValueError, InvalidOperation):
        await message.answer('Формат: CODE;percent|fixed;value')
        return

    promo_type = PromoType.PERCENT if promo_type_raw == 'percent' else PromoType.FIXED
    promo = await PromoCodeRepository(session).create(
        code=code.upper(),
        promo_type=promo_type,
        value=value,
        is_active=True,
    )
    await state.clear()
    await message.answer(f'Промокод создан: {promo.code}')
