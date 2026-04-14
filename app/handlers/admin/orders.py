from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import claims_admin_kb, order_admin_actions_kb, orders_admin_kb
from app.models import Order, OrderStatusHistory
from app.models.enums import OrderStatus
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb

router = Router(name="admin_orders")


STATUS_FILTERS = {
    "filter_waiting_payment": OrderStatus.WAITING_PAYMENT,
    "filter_paid": OrderStatus.PAID,
    "filter_processing": OrderStatus.PROCESSING,
    "filter_completed": OrderStatus.COMPLETED,
}


CLAIMS_FILTERS = {
    "list": None,
    "filter_dispute": OrderStatus.DISPUTE,
    "filter_canceled": OrderStatus.CANCELED,
}


async def _get_order(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    return result.scalar_one_or_none()


async def _get_history(session: AsyncSession, order_id: int) -> list[OrderStatusHistory]:
    result = await session.execute(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == order_id)
        .order_by(OrderStatusHistory.created_at.desc(), OrderStatusHistory.id.desc())
    )
    return list(result.scalars().all())


async def _list_orders(session: AsyncSession, *, status: OrderStatus | None = None, query: str | None = None, limit: int = 50) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(limit)
    )
    if status is not None:
        stmt = stmt.where(Order.status == status)
    if query:
        q = query.strip()
        if q:
            if q.isdigit():
                stmt = stmt.where(or_(Order.id == int(q), Order.user_id == int(q)))
            else:
                stmt = stmt.where(Order.order_number.ilike(f"%{q}%"))
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def _order_card(order: Order, history: list[OrderStatusHistory]) -> str:
    items_block = "\n".join(
        f"• <b>{item.title_snapshot}</b> × {item.quantity} = <b>{item.total_price} {order.currency_code}</b>"
        for item in order.items
    ) or "Нет позиций"

    history_block = "\n".join(
        f"• {_fmt_dt(row.created_at)} → <b>{row.new_status}</b>{f' — {row.comment}' if row.comment else ''}"
        for row in history[:8]
    ) or "История пока пуста"

    return (
        f"📦 <b>Заказ {order.order_number}</b>\n\n"
        f"ID: <code>{order.id}</code>\n"
        f"Пользователь ID: <code>{order.user_id}</code>\n"
        f"Статус: <b>{order.status}</b>\n"
        f"Оплата: <b>{order.payment_provider}</b>\n"
        f"Сумма: <b>{order.total_amount} {order.currency_code}</b>\n"
        f"Создан: <b>{_fmt_dt(order.created_at)}</b>\n\n"
        f"<b>Позиции</b>\n{items_block}\n\n"
        f"<b>Последние изменения</b>\n{history_block}"
    )


@router.callback_query(AdminCb.filter(F.section == "orders"), AdminPermissionFilter("orders.view"))
async def admin_orders(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext) -> None:
    action = callback_data.action

    if action == "search":
        await state.set_state(AdminCatalogStates.waiting_order_search)
        await callback.message.edit_text(
            "🔎 <b>Поиск заказа</b>\n\nОтправь номер заказа, ID заказа или ID пользователя.",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    if action == "list" or action in STATUS_FILTERS:
        status = STATUS_FILTERS.get(action)
        orders = await _list_orders(session, status=status)
        title = "📦 <b>Заказы</b>"
        if status is not None:
            title += f"\n\nФильтр: <b>{status}</b>"
        await callback.message.edit_text(title, reply_markup=orders_admin_kb(orders, filter_status=status.value if status else None), parse_mode="HTML")
        await callback.answer()
        return

    if action == "view":
        order = await _get_order(session, callback_data.entity_id or 0)
        if order is None:
            await callback.answer("Заказ не найден", show_alert=True)
            return
        history = await _get_history(session, order.id)
        await callback.message.edit_text(_order_card(order, history), reply_markup=order_admin_actions_kb(order.id), parse_mode="HTML")
        await callback.answer()
        return

    try:
        new_status = OrderStatus(action)
    except ValueError:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    order = await _get_order(session, callback_data.entity_id or 0)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    old_status = order.status
    order.status = new_status
    session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            changed_by_admin_id=None,
            comment=f"Изменено через админку: {old_status} → {new_status}",
            payload_json={"source": "admin_panel"},
        )
    )
    await session.flush()

    history = await _get_history(session, order.id)
    await callback.message.edit_text(_order_card(order, history), reply_markup=order_admin_actions_kb(order.id), parse_mode="HTML")
    await callback.answer("Статус обновлён")


@router.message(AdminCatalogStates.waiting_order_search, AdminPermissionFilter("orders.view"))
async def admin_orders_search(message: Message, session: AsyncSession, state: FSMContext) -> None:
    query = (message.text or "").strip()
    orders = await _list_orders(session, query=query)
    await state.clear()

    if not orders:
        await message.answer("Ничего не найдено по этому запросу.")
        return

    await message.answer(
        f"🔎 <b>Результаты поиска</b>\n\nНайдено: <b>{len(orders)}</b>",
        reply_markup=orders_admin_kb(orders),
        parse_mode="HTML",
    )


@router.callback_query(AdminCb.filter(F.section == "claims"), AdminPermissionFilter("orders.view"))
async def admin_claims(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession) -> None:
    status = CLAIMS_FILTERS.get(callback_data.action)
    stmt = select(Order).order_by(Order.created_at.desc(), Order.id.desc()).limit(50)
    if status is None:
        stmt = stmt.where(Order.status.in_([OrderStatus.DISPUTE, OrderStatus.CANCELED]))
    else:
        stmt = stmt.where(Order.status == status)
    result = await session.execute(stmt)
    orders = list(result.scalars().all())

    text = "⚠️ <b>Споры и возвраты</b>"
    if status is not None:
        text += f"\n\nФильтр: <b>{status}</b>"
    await callback.message.edit_text(text, reply_markup=claims_admin_kb(orders), parse_mode="HTML")
    await callback.answer()
