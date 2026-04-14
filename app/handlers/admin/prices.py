from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.keyboards.admin import prices_admin_kb
from app.models import Admin, Price, Product
from app.states.admin import AdminCrudStates
from app.utils.callbacks import AdminCb

router = Router(name="admin_prices")
settings = get_settings()


def _has_access(user_id: int, admin: Admin | None) -> bool:
    return admin is not None or user_id in {settings.super_admin_tg_id, settings.second_admin_tg_id}


@router.callback_query(AdminCb.filter(F.section == "prices"))
async def admin_prices(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(callback.from_user.id, admin):
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback_data.action == "list":
        products = list(await session.scalars(select(Product).where(Product.is_deleted.is_(False)).options(selectinload(Product.prices)).order_by(Product.sort_order, Product.id)))
        rows = []
        for product in products:
            active_price = next((p for p in sorted(product.prices, key=lambda x: x.id, reverse=True) if p.is_active), None)
            rows.append((product, active_price))
        await callback.message.edit_text("💸 <b>Цены</b>", reply_markup=prices_admin_kb(rows), parse_mode="HTML")
        await callback.answer()
        return

    if callback_data.action == "set":
        product = await session.get(Product, callback_data.entity_id or 0)
        if not product or product.is_deleted:
            await callback.answer("Товар не найден", show_alert=True)
            return
        await state.clear()
        await state.set_state(AdminCrudStates.waiting_price_value)
        await state.update_data(price_product_id=product.id)
        await callback.message.answer(f"Введите новую цену для товара <b>{product.title}</b> сообщением.\nПример: 199.00", parse_mode="HTML")
        await callback.answer()
        return

    await callback.answer()


@router.message(AdminCrudStates.waiting_price_value)
async def set_price(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    data = await state.get_data()
    product = await session.get(Product, data.get("price_product_id", 0))
    if not product or product.is_deleted:
        await state.clear()
        await message.answer("Товар не найден.")
        return

    raw = (message.text or "").strip().replace(",", ".")
    try:
        value = Decimal(raw)
    except InvalidOperation:
        await message.answer("Цена должна быть числом, например 199.00")
        return
    if value <= 0:
        await message.answer("Цена должна быть больше нуля.")
        return

    current = await session.scalar(select(Price).where(Price.product_id == product.id, Price.is_active.is_(True)).order_by(Price.id.desc()).limit(1))
    if current:
        current.base_price = value
        current.discounted_price = value
        current.currency_code = "RUB"
    else:
        session.add(Price(product_id=product.id, base_price=value, discounted_price=value, currency_code="RUB", starts_at=None, ends_at=None, is_active=True, changed_by_admin_id=None))
    await session.flush()
    await state.clear()
    await message.answer(f"✅ Цена для <b>{product.title}</b> обновлена: {value:.2f} RUB", parse_mode="HTML")
