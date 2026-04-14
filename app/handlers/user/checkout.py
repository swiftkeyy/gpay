from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.keyboards.payment import cryptobot_invoice_kb, payment_methods_kb
from app.models import Order, OrderItem, OrderStatus, PaymentProviderType, User
from app.services.cart import CartService
from app.services.payment import CryptoBotClient, PaymentError, TelegramStarsPaymentService
from app.utils.callbacks import NavCb, PaymentCb

router = Router(name="user_checkout")
settings = get_settings()


def _order_number() -> str:
    return f"GP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"


async def _safe_callback_answer(callback: CallbackQuery, text: str | None = None, *, show_alert: bool = False) -> None:
    try:
        await callback.answer(text=text, show_alert=show_alert)
    except TelegramBadRequest as exc:
        msg = str(exc).lower()
        if "query is too old" in msg or "query id is invalid" in msg:
            return
        raise


async def _resolve_db_user(
    session: AsyncSession,
    db_user: User | None,
    tg_user,
) -> User | None:
    if db_user is not None and getattr(db_user, "id", None) is not None:
        return db_user

    if tg_user is None:
        return None

    result = await session.execute(select(User).where(User.telegram_id == tg_user.id))
    user = result.scalar_one_or_none()

    if user is not None:
        changed = False
        if user.username != tg_user.username:
            user.username = tg_user.username
            changed = True
        if user.first_name != tg_user.first_name:
            user.first_name = tg_user.first_name
            changed = True
        if user.last_name != tg_user.last_name:
            user.last_name = tg_user.last_name
            changed = True
        if changed:
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
    return user


async def _get_order_for_user(
    session: AsyncSession,
    order_id: int,
    *,
    db_user: User | None = None,
    tg_user=None,
) -> Order | None:
    db_user = await _resolve_db_user(session, db_user, tg_user)
    if db_user is None or getattr(db_user, "id", None) is None:
        return None

    result = await session.execute(
        select(Order).where(Order.id == order_id, Order.user_id == db_user.id)
    )
    return result.scalar_one_or_none()


async def _mark_order_paid(
    session: AsyncSession,
    order: Order,
    *,
    payment_external_id: str,
) -> None:
    order.status = OrderStatus.PAID
    order.payment_external_id = payment_external_id
    await session.flush()
    await session.commit()


def _extract_cryptobot_invoice_id(order: Order) -> int | None:
    if not order.payment_external_id or not order.payment_external_id.startswith("cryptobot:"):
        return None
    _, _, raw_invoice_id = order.payment_external_id.partition(":")
    try:
        return int(raw_invoice_id)
    except ValueError:
        return None


@router.callback_query(NavCb.filter(F.target == "checkout"))
async def checkout_from_cart(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    db_user = await _resolve_db_user(session, db_user, callback.from_user)

    if db_user is None or getattr(db_user, "id", None) is None:
        await _safe_callback_answer(callback, "Пользователь не найден", show_alert=True)
        return

    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    totals = await cart_service.get_cart_totals(db_user)

    if cart is None or not getattr(cart, "items", None):
        await _safe_callback_answer(callback, "Корзина пуста", show_alert=True)
        return

    order = Order(
        order_number=_order_number(),
        user_id=db_user.id,
        status=OrderStatus.NEW,
        subtotal_amount=Decimal(str(totals["subtotal"])),
        discount_amount=Decimal(str(totals["discount"])),
        total_amount=Decimal(str(totals["total"])),
        currency_code=str(totals["currency_code"]),
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
    order.payment_provider = PaymentProviderType.MANUAL
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
            reply_markup=payment_methods_kb(
                order.id,
                stars_enabled=settings.telegram_stars_enabled,
                cryptobot_enabled=settings.cryptobot_enabled and bool(settings.cryptobot_api_token),
            ),
            parse_mode="HTML",
        )
    await _safe_callback_answer(callback)


@router.callback_query(PaymentCb.filter(F.action == "manual"))
async def choose_manual_payment(
    callback: CallbackQuery,
    callback_data: PaymentCb,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    order = await _get_order_for_user(
        session,
        callback_data.order_id,
        db_user=db_user,
        tg_user=callback.from_user,
    )
    if order is None:
        await _safe_callback_answer(callback, "Заказ не найден", show_alert=True)
        return

    # Фиксируем сумму - не даем ей измениться
    fixed_total = Decimal(str(order.total_amount))
    fixed_currency = str(order.currency_code)
    
    order.status = OrderStatus.WAITING_PAYMENT
    order.payment_provider = PaymentProviderType.MANUAL
    await session.commit()

    text = (
        f"💬 <b>Ручная оплата</b>\n\n"
        f"Заказ: <code>{order.order_number}</code>\n"
        f"Сумма: <b>{fixed_total} {fixed_currency}</b>\n\n"
        f"Свяжитесь с поддержкой или оплатите по инструкции магазина."
    )

    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML")
    await _safe_callback_answer(callback)


@router.callback_query(PaymentCb.filter(F.action == "stars"))
async def choose_stars_payment(
    callback: CallbackQuery,
    callback_data: PaymentCb,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    if not settings.telegram_stars_enabled:
        await _safe_callback_answer(callback, "Оплата Stars отключена", show_alert=True)
        return

    order = await _get_order_for_user(
        session,
        callback_data.order_id,
        db_user=db_user,
        tg_user=callback.from_user,
    )
    if order is None:
        await _safe_callback_answer(callback, "Заказ не найден", show_alert=True)
        return

    stars_amount = TelegramStarsPaymentService.stars_amount(order)
    payload = TelegramStarsPaymentService.build_payload(order.id, callback.from_user.id)

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Оплата заказа {order.order_number}",
        description=f"{settings.shop_name}: оплата цифрового товара. Заказ {order.order_number}.",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label=f"Заказ {order.order_number}", amount=stars_amount)],
        provider_token="",
        start_parameter=f"stars-{order.id}",
    )

    order.status = OrderStatus.WAITING_PAYMENT
    order.payment_provider = PaymentProviderType.STUB
    order.payment_external_id = payload
    await session.commit()

    if callback.message:
        await callback.message.edit_text(
            (
                f"⭐ <b>Счёт Telegram Stars отправлен</b>\n\n"
                f"Заказ: <code>{order.order_number}</code>\n"
                f"К оплате: <b>{stars_amount} XTR</b>\n\n"
                f"Откройте инвойс и завершите оплату."
            ),
            parse_mode="HTML",
        )
    await _safe_callback_answer(callback)


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    payload = pre_checkout_query.invoice_payload or ""
    if payload.startswith("stars:order:"):
        await pre_checkout_query.answer(ok=True)
        return
    await pre_checkout_query.answer(ok=False, error_message="Неизвестный платёж")


@router.message(F.successful_payment)
async def handle_successful_stars_payment(
    message: Message,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    successful_payment = message.successful_payment
    if successful_payment is None:
        return

    parsed = TelegramStarsPaymentService.parse_payload(successful_payment.invoice_payload)
    if parsed is None:
        return

    order_id, telegram_user_id = parsed
    if message.from_user is None or message.from_user.id != telegram_user_id:
        return

    order = await _get_order_for_user(
        session,
        order_id,
        db_user=db_user,
        tg_user=message.from_user,
    )
    if order is None:
        return

    await _mark_order_paid(
        session,
        order,
        payment_external_id=successful_payment.telegram_payment_charge_id,
    )

    await message.answer(
        (
            f"✅ <b>Оплата получена</b>\n\n"
            f"Заказ: <code>{order.order_number}</code>\n"
            f"Сумма: <b>{successful_payment.total_amount} {successful_payment.currency}</b>\n\n"
            f"Мы уже передали заказ в обработку."
        ),
        parse_mode="HTML",
    )


@router.callback_query(PaymentCb.filter(F.action == "cryptobot"))
async def choose_cryptobot_payment(
    callback: CallbackQuery,
    callback_data: PaymentCb,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    if not settings.cryptobot_enabled:
        await _safe_callback_answer(callback, "Crypto Bot отключён", show_alert=True)
        return

    order = await _get_order_for_user(
        session,
        callback_data.order_id,
        db_user=db_user,
        tg_user=callback.from_user,
    )
    if order is None:
        await _safe_callback_answer(callback, "Заказ не найден", show_alert=True)
        return

    try:
        client = CryptoBotClient()
        invoice = await client.create_invoice(order)
    except PaymentError as exc:
        await _safe_callback_answer(callback, str(exc), show_alert=True)
        return

    order.status = OrderStatus.WAITING_PAYMENT
    order.payment_provider = PaymentProviderType.STUB
    order.payment_external_id = f"cryptobot:{invoice.invoice_id}"
    await session.commit()

    text = (
        f"💎 <b>Crypto Bot</b>\n\n"
        f"Заказ: <code>{order.order_number}</code>\n"
        f"Сумма: <b>{order.total_amount} {order.currency_code}</b>\n\n"
        f"Нажмите кнопку ниже, чтобы открыть счёт, затем после оплаты вернитесь и нажмите «Проверить оплату»."
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=cryptobot_invoice_kb(invoice.bot_invoice_url, order.id),
            parse_mode="HTML",
        )
    await _safe_callback_answer(callback)


@router.callback_query(PaymentCb.filter(F.action == "cryptocheck"))
async def check_cryptobot_payment(
    callback: CallbackQuery,
    callback_data: PaymentCb,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    order = await _get_order_for_user(
        session,
        callback_data.order_id,
        db_user=db_user,
        tg_user=callback.from_user,
    )
    if order is None:
        await _safe_callback_answer(callback, "Заказ не найден", show_alert=True)
        return

    invoice_id = _extract_cryptobot_invoice_id(order)
    if invoice_id is None:
        await _safe_callback_answer(callback, "Инвойс Crypto Bot не найден", show_alert=True)
        return

    try:
        client = CryptoBotClient()
        invoice = await client.get_invoice(invoice_id)
    except PaymentError as exc:
        await _safe_callback_answer(callback, str(exc), show_alert=True)
        return

    if invoice.status == "paid":
        await _mark_order_paid(
            session,
            order,
            payment_external_id=f"cryptobot:{invoice.invoice_id}:paid",
        )
        if callback.message:
            await callback.message.edit_text(
                (
                    f"✅ <b>Оплата через Crypto Bot получена</b>\n\n"
                    f"Заказ: <code>{order.order_number}</code>\n"
                    f"Сумма: <b>{order.total_amount} {order.currency_code}</b>\n\n"
                    f"Заказ передан в обработку."
                ),
                parse_mode="HTML",
            )
        await _safe_callback_answer(callback, "Оплата найдена")
        return

    await _safe_callback_answer(callback, f"Статус счёта: {invoice.status}", show_alert=True)
