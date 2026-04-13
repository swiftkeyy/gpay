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


def _format_money(value: Decimal | int | float | str) -> str:
    return f"{Decimal(value):.2f}"


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
        return user

    return None


async def render_cart(
    target: CallbackQuery,
    session: AsyncSession,
    db_user: User | None,
) -> None:
    db_user = await _resolve_db_user(session, db_user, target.from_user)

    if db_user is None or getattr(db_user, "id", None) is None:
        if target.message:
            await target.message.edit_text(
                "🛒 <b>Корзина</b>\n\nВаша корзина пока пуста.",
                reply_markup=cart_kb([]),
                parse_mode="HTML",
            )
        await target.answer()
        return

    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    totals = await cart_service.get_cart_totals(db_user)

    if cart is None or not getattr(cart, "items", None):
        text = "🛒 <b>Корзина</b>\n\nВаша корзина пока пуста."
        if target.message:
            await target.message.edit_text(
                text,
                reply_markup=cart_kb([]),
                parse_mode="HTML",
            )
        await target.answer()
        return

    lines: list[str] = ["🛒 <b>Корзина</b>\n"]

    for entry in totals["items"]:
        item = entry["item"]
        product = entry["product"]
        quote = entry["quote"]

        lines.append(
            f"• <b>{product.title}</b>\n"
            f"  Кол-во: {item.quantity}\n"
            f"  Сумма: {_format_money(quote.final_price)} {quote.currency_code}\n"
        )

    lines.append(f"\nПромежуточный итог: <b>{_format_money(totals['subtotal'])} {totals['currency_code']}</b>")
    lines.append(f"Скидка: <b>{_format_money(totals['discount'])} {totals['currency_code']}</b>")
    lines.append(f"Итого: <b>{_format_money(totals['total'])} {totals['currency_code']}</b>")

    text = "\n".join(lines)

    if target.message:
        await target.message.edit_text(
            text,
            reply_markup=cart_kb(cart),
            parse_mode="HTML",
        )
    await target.answer()


@router.callback_query(NavCb.filter(F.target == "cart"))
async def open_cart(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    await render_cart(callback, session, db_user)


@router.callback_query(CartCb.filter())
async def cart_actions(
    callback: CallbackQuery,
    callback_data: CartCb,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    db_user = await _resolve_db_user(session, db_user, callback.from_user)
    if db_user is None or getattr(db_user, "id", None) is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    cart_service = CartService(session)

    if callback_data.action == "clear":
        await cart_service.clear(db_user.id)
        await session.commit()
        await render_cart(callback, session, db_user)
        return

    if callback_data.action == "inc" and callback_data.item_id:
        await cart_service.change_quantity(callback_data.item_id, 1)
        await session.commit()
        await render_cart(callback, session, db_user)
        return

    if callback_data.action == "dec" and callback_data.item_id:
        await cart_service.change_quantity(callback_data.item_id, -1)
        await session.commit()
        await render_cart(callback, session, db_user)
        return

    if callback_data.action == "del" and callback_data.item_id:
        await cart_service.remove_item(callback_data.item_id)
        await session.commit()
        await render_cart(callback, session, db_user)
        return

    await callback.answer("Неизвестное действие", show_alert=True)
