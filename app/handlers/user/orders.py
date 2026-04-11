from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import order_actions_kb, orders_kb
from app.models import Order, OrderStatus, User
from app.repositories.orders import OrderRepository
from app.services.cart import CartService
from app.utils.callbacks import NavCb
from app.utils.texts import order_card, profile_text

router = Router(name='user_orders')


@router.callback_query(NavCb.filter(F.target == 'orders_current'))
async def current_orders(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    orders = await OrderRepository(session).list_by_user(db_user.id)
    active = [order for order in orders if order.status not in {OrderStatus.COMPLETED, OrderStatus.CANCELED, OrderStatus.FAILED}]
    await callback.message.edit_text('📦 <b>Текущие заказы</b>', reply_markup=orders_kb(active), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'orders_history'))
async def history_orders(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    orders = await OrderRepository(session).list_by_user(db_user.id)
    history = [order for order in orders if order.status in {OrderStatus.COMPLETED, OrderStatus.CANCELED, OrderStatus.FAILED}]
    await callback.message.edit_text('🕘 <b>История заказов</b>', reply_markup=orders_kb(history), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'order'))
async def order_view(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession) -> None:
    order = await OrderRepository(session).get_full(callback_data.entity_id)
    if not order:
        await callback.answer('Заказ не найден.', show_alert=True)
        return
    await callback.message.edit_text(order_card(order), reply_markup=order_actions_kb(order.id), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'repeat_order'))
async def repeat_order(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession, db_user: User) -> None:
    order = await OrderRepository(session).get_full(callback_data.entity_id)
    if not order:
        await callback.answer('Заказ не найден.', show_alert=True)
        return
    cart_service = CartService(session)
    await cart_service.clear(db_user.id)
    from app.repositories.catalog import ProductRepository

    product_repo = ProductRepository(session)
    for item in order.items:
        product = await product_repo.get_full(item.product_id)
        if product and product.is_active:
            await cart_service.add_item(db_user.id, product, quantity=item.quantity)
    await callback.answer('Заказ повторно добавлен в корзину.')
