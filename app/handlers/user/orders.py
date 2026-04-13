from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import order_actions_kb, orders_kb
from app.models import OrderStatus, User
from app.repositories.orders import OrderRepository
from app.services.cart import CartService
from app.utils.callbacks import NavCb
from app.utils.texts import order_card

router = Router(name="user_orders")


@router.callback_query(NavCb.filter(F.target == "orders_current"))
async def current_orders(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    orders = await OrderRepository(session).list_by_user(db_user.id)
    active = [order for order in orders if order.status not in {OrderStatus.COMPLETED, OrderStatus.CANCELED, OrderStatus.FAILED}]
    await callback.message.edit_text("📦 <b>Текущие заказы</b>", reply_markup=orders_kb(active), parse_mode="HTML")
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "orders_history"))
async def history_orders(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    orders = await OrderRepository(session).list_by_user(db_user.id)
    history = [order for order in orders if order.status in {OrderStatus.COMPLETED, OrderStatus.CANCELED, OrderStatus.FAILED}]
    await callback.message.edit_text("🕘 <b>История заказов</b>", reply_markup=orders_kb(history), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("order:"))
async def order_actions(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    data = callback.data or ""
    parts = data.split(":")
    repo = OrderRepository(session)

    if len(parts) == 2:
        try:
            order_id = int(parts[1])
        except ValueError:
            await callback.answer("Заказ не найден.", show_alert=True)
            return

        order = await repo.get_full(order_id)
        if not order or order.user_id != db_user.id:
            await callback.answer("Заказ не найден.", show_alert=True)
            return

        await callback.message.edit_text(order_card(order), reply_markup=order_actions_kb(order.id), parse_mode="HTML")
        await callback.answer()
        return

    if len(parts) == 3 and parts[1] == "repeat":
        try:
            order_id = int(parts[2])
        except ValueError:
            await callback.answer("Заказ не найден.", show_alert=True)
            return

        order = await repo.get_full(order_id)
        if not order or order.user_id != db_user.id:
            await callback.answer("Заказ не найден.", show_alert=True)
            return

        cart_service = CartService(session)
        await cart_service.clear(db_user.id)
        from app.repositories.catalog import ProductRepository

        product_repo = ProductRepository(session)
        for item in order.items:
            product = await product_repo.get_full(item.product_id)
            if product and product.is_active:
                await cart_service.add_item(db_user.id, product, quantity=item.quantity)

        await callback.answer("Заказ повторно добавлен в корзину.")
        return

    if len(parts) == 3 and parts[1] == "history":
        try:
            order_id = int(parts[2])
        except ValueError:
            await callback.answer("Заказ не найден.", show_alert=True)
            return

        order = await repo.get_full(order_id)
        if not order or order.user_id != db_user.id:
            await callback.answer("Заказ не найден.", show_alert=True)
            return

        text = (
            "📜 <b>История статусов</b>\n\n"
            f"Заказ: <code>{order.order_number}</code>\n"
            f"Текущий статус: <b>{order.status}</b>\n\n"
            "Подробный журнал статусов пока не реализован в интерфейсе."
        )
        await callback.message.edit_text(text, reply_markup=order_actions_kb(order.id), parse_mode="HTML")
        await callback.answer()
        return

    await callback.answer("Неизвестное действие", show_alert=True)
