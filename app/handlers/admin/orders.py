from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import order_admin_actions_kb, orders_admin_kb
from app.models.enums import AuditAction, EntityType, OrderStatus
from app.repositories.orders import OrderRepository
from app.services.audit import AuditService
from app.services.orders import OrderService
from app.utils.callbacks import AdminCb
from app.utils.texts import order_card

router = Router(name='admin_orders')


@router.callback_query(AdminCb.filter(F.section == 'orders'), AdminPermissionFilter('orders.view'))
async def admin_orders(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession) -> None:
    repo = OrderRepository(session)
    if callback_data.action == 'list':
        orders = await repo.list_recent(limit=100)
        await callback.message.edit_text('📦 <b>Заказы</b>', reply_markup=orders_admin_kb(orders), parse_mode='HTML')
    elif callback_data.action == 'view':
        order = await repo.get_full(callback_data.entity_id)
        if not order:
            await callback.answer('Заказ не найден.', show_alert=True)
            return
        await callback.message.edit_text(order_card(order), reply_markup=order_admin_actions_kb(order.id), parse_mode='HTML')
    else:
        order = await repo.get_full(callback_data.entity_id)
        if not order:
            await callback.answer('Заказ не найден.', show_alert=True)
            return
        status = OrderStatus(callback_data.action)
        await OrderService(session).change_status(order=order, status=status, actor_user_id=None, actor_label='admin')
        await AuditService(session).log(
            action=AuditAction.STATUS_CHANGE,
            entity_type=EntityType.DEFAULT,
            entity_id=order.id,
            old_values={'status': str(order.status)},
            new_values={'status': str(status)},
        )
        await callback.answer('Статус заказа обновлён.')
        await callback.message.edit_text(order_card(order), reply_markup=order_admin_actions_kb(order.id), parse_mode='HTML')
        return
    await callback.answer()
