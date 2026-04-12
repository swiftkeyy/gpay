from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.payment import payment_methods_kb
from app.models import Order, OrderItem, OrderStatus, PaymentProviderType, User
from app.services.cart import CartService
from app.utils.callbacks import NavCb, PaymentCb

router = Router(name="user_checkout")


def _order_number() -> str:
    return f"GP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"


async def _resolve_db_user(
    session: AsyncSession,
    db_user: User | None,
    tg_user,
) -> User | None:
    if db_user is not None and getattr(db_user, "id", None) is not None:
        return db_user

    if tg_user is None:
        return None

    result = await session.execute(
        select(User).where(User.telegram_id == tg_user.id)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        user.username = tg_user.username
        user.first_name = tg_user.first_name
        user.last_name = tg_user.last_name
        await session.flush()
        return user

    user = User(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        is_blocked=False,
        block_reason=None,
        personal_discount_percent=0,
        referral_code=f"REF{tg_user.id}",
    )
    session.add(user)
    await session.flush()
    await session.commit()

    result = await session.execute(
        select(User).where(User.telegram_id == tg_user.id)
    )
    return result.scalar_one_or_none()


@router.callback_query(NavCb.filter(F.target == "checkout"))
async def checkout_from_cart(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    db_user = await _resolve_db_user(session, db_user, callback.from_user)

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
                    unit_price = (quote.final_price / item.quantity).quantize(Decimal("0.01"))
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

    order.status = OrderStatus.WAITING_PAYMENT
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
        f"Свяжитесь с поддержкой или оплатите по инструкции магазина."
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
        f"Следующим шагом сюда подключается sendInvoice."
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
        f"Следующим шагом сюда подключается createInvoice."
    )

    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()
