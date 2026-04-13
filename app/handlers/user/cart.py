from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import cart_kb
from app.models import User
from app.services.cart import CartService
from app.utils.callbacks import CartCb, NavCb

router = Router(name="user_cart")


async def _resolve_db_user(session: AsyncSession, tg_user) -> User | None:
    if tg_user is None:
        return None

    result = await session.execute(
        select(User).where(User.telegram_id == tg_user.id)
    )
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


def _fmt_amount(value: Decimal | int | float) -> str:
    try:
        return f"{Decimal(value):.2f}"
    except Exception:
        return str(value)


async def _render_cart(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    totals = await cart_service.get_cart_totals(db_user)

    if cart is None or not getattr(cart, "items", None):
        text = "🛒 <b>Корзина</b>\n\nВаша корзина пуста."
        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=cart_kb([]),
                parse_mode="HTML",
            )
        await callback.answer()
        return

    lines: list[str] = ["🛒 <b>Корзина</b>\n"]

    for row in totals["items"]:
        item = row["item"]
        quote = row["quote"]
        title = getattr(item.product, "title", f"Товар #{item.product_id}")
        lines.append(
            f"• <b>{title}</b>\n"
            f"  Кол-во: <b>{item.quantity}</b>\n"
            f"  Сумма: <b>{_fmt_amount(quote.final_price)} {quote.currency_code}</b>\n"
        )

    lines.append(f"💵 Подытог: <b>{_fmt_amount(totals['subtotal'])} {totals['currency_code']}</b>")
    lines.append(f"🎁 Скидка: <b>{_fmt_amount(totals['discount'])} {totals['currency_code']}</b>")
    lines.append(f"💳 Итого: <b>{_fmt_amount(totals['total'])} {totals['currency_code']}</b>")

    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=cart_kb(cart),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "cart"))
async def open_cart(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    if db_user is None:
        db_user = await _resolve_db_user(session, callback.from_user)

    if db_user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await _render_cart(callback, session, db_user)


@router.callback_query(CartCb.filter())
async def cart_actions(
    callback: CallbackQuery,
    callback_data: CartCb,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    if db_user is None:
        db_user = await _resolve_db_user(session, callback.from_user)

    if db_user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    cart_service = CartService(session)

    if callback_data.action == "inc" and callback_data.item_id:
        await cart_service.change_quantity(db_user, callback_data.item_id, 1)
        await session.commit()
    elif callback_data.action == "dec" and callback_data.item_id:
        await cart_service.change_quantity(db_user, callback_data.item_id, -1)
        await session.commit()
    elif callback_data.action == "del" and callback_data.item_id:
        await cart_service.remove_item(db_user, callback_data.item_id)
        await session.commit()
    elif callback_data.action == "clear":
        await cart_service.clear_cart(db_user)
        await session.commit()

    await _render_cart(callback, session, db_user)
