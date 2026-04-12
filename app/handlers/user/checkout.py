from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.payment import payment_methods_kb
from app.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatus,
    PaymentProviderType,
    User,
)
from app.services.cart import CartService
from app.utils.callbacks import NavCb, PaymentCb

router = Router(name="user_checkout")


def _order_number() -> str:
    return f"GP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"


@router.callback_query(NavCb.filter(F.target == "checkout"))
async def checkout_from_cart(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    if db_user is None or getattr(db_user, "id", None) is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    cart_service = CartService(session)
    totals = await cart_service.get_cart_totals(db_user)
    cart = await cart_service.get_cart(db_user.id)

    if cart is None or not getattr(cart, "items", None):
        await callback.answer("Корзина пуста", show_alert=True)
        return

    order = Order(
        order_number=_order_number(),
        user_id=db_user.id,
        status=OrderStatus.NEW,
        subtotal_amount=totals["subtotal"],
        discount_amount=totals["discount"],
        total_amount=totals["total"],
        currency_code=totals["currency_code"],
        payment_provider=PaymentProviderType.MANUAL,
        payment_external_id=None,
        fulfillment_type=cart.items[0].product.fulfillment_type if cart.items and cart.items[0].product else "manual",
        customer_data_json={},
        admin_comment=None,
    )
    session.add(order)
    await session.flush()

    for item in cart.items:
        if not item.product:
            continue

        unit_price = Decimal("0.00")
        line_total = Decimal("0.00")

        for row in totals["items"]:
            if row["item"].id == item.id:
                quote = row["quote"]
                if item.quantity > 0:
                    unit_price = quote.final_price / item.quantity
                line_total = quote.final_price
                break

        session.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product.id,
                title_snapshot=item.product.title,
                quantity=item.quantity,
                unit_price=unit_price,
                total_price=line_total,
                fulfillment_type=item.product.fulfillment_type,
                metadata_json={},
            )
        )

    await session.flush()

    for item in list(cart.items):
        await session.delete(item)

    await session.commit()

    text = (
        f"🧾 <b>Заказ создан</b>\n\n"
        f"Номер: <code>{order.order_number}</code>\n"
        f"Сумма: <b>{order.total_amount} {order.currency_code}</b>\n\n"
        f"Выберите способ оплаты:"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=payment_methods_kb(order.id),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(PaymentCb.filter(F.action == "manual"))
async def choose_manual_payment(
    callback: CallbackQuery,
    callback_data: PaymentCb,
    session: AsyncSession,
) -> None:
    order = await session.get(Order, callback_data.order_id)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    order.status = OrderStatus.WAITING_PAYMENT
    order.payment_provider = PaymentProviderType.MANUAL
    await session.commit()

    text = (
        f"💬 <b>Ручная оплата</b>\n\n"
        f"Заказ: <code>{order.order_number}</code>\n"
        f"Сумма: <b>{order.total_amount} {order.currency_code}</b>\n\n"
        f"Отправьте оплату по инструкции магазина и дождитесь подтверждения администратора."
    )

    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(PaymentCb.filter(F.action == "stars"))
async def choose_stars_payment(
    callback: CallbackQuery,
    callback_data: PaymentCb,
    session: AsyncSession,
) -> None:
    order = await session.get(Order, callback_data.order_id)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    order.status = OrderStatus.WAITING_PAYMENT
    await session.commit()

    text = (
        f"⭐ <b>Telegram Stars</b>\n\n"
        f"Заказ: <code>{order.order_number}</code>\n"
        f"Сумма: <b>{order.total_amount}</b>\n\n"
        f"Интеграция Stars подключается следующим шагом через sendInvoice."
    )

    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(PaymentCb.filter(F.action == "cryptobot"))
async def choose_cryptobot_payment(
    callback: CallbackQuery,
    callback_data: PaymentCb,
    session: AsyncSession,
) -> None:
    order = await session.get(Order, callback_data.order_id)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    order.status = OrderStatus.WAITING_PAYMENT
    await session.commit()

    text = (
        f"💎 <b>Crypto Bot</b>\n\n"
        f"Заказ: <code>{order.order_number}</code>\n"
        f"Сумма: <b>{order.total_amount} {order.currency_code}</b>\n\n"
        f"Интеграция Crypto Bot подключается следующим шагом через createInvoice."
    )

    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()
