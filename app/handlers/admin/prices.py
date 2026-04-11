from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.models import Price
from app.repositories.catalog import ProductRepository
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb
from app.utils.validators import validate_price

router = Router(name='admin_prices')


@router.callback_query(AdminCb.filter(F.section == 'prices'), AdminPermissionFilter('prices.manage'))
async def price_set_start(callback: CallbackQuery, callback_data: AdminCb, state: FSMContext) -> None:
    if callback_data.action == 'set':
        await state.set_state(AdminCatalogStates.waiting_price_value)
        await state.update_data(price_product_id=callback_data.entity_id)
        await callback.message.answer('Введите новую цену сообщением, например 199.00')
    await callback.answer()


@router.message(AdminCatalogStates.waiting_price_value, AdminPermissionFilter('prices.manage'))
async def price_set_finish(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = data.get('price_product_id')
    product = await ProductRepository(session).get(product_id)
    if not product:
        await message.answer('Товар не найден.')
        await state.clear()
        return
    value = Decimal(validate_price(message.text or '0'))
    session.add(Price(product_id=product.id, base_price=value, discounted_price=value, currency_code='RUB', is_active=True))
    await state.clear()
    await message.answer(f'Цена для {product.title} обновлена: {value} RUB')
