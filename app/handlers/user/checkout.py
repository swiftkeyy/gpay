from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, User
from app.services.cart import CartService
from app.services.orders import OrderService
from app.services.payment import ManualPaymentProvider
from app.states.user import CheckoutStates
from app.utils.callbacks import NavCb
from app.utils.idempotency import build_checkout_key
from app.utils.validators import ValidationError, validate_dynamic_field

router = Router(name='user_checkout')


def _build_dynamic_fields(products: list[Product]) -> list[dict]:
    fields: list[dict] = []
    for product in products:
        prefix = product.slug
        if product.requires_player_id:
            fields.append({'key': f'{prefix}.player_id', 'label': f'{product.title}: player_id', 'type': 'text', 'required': True})
        if product.requires_nickname:
            fields.append({'key': f'{prefix}.nickname', 'label': f'{product.title}: nickname', 'type': 'text', 'required': True})
        if product.requires_region:
            fields.append({'key': f'{prefix}.region', 'label': f'{product.title}: region', 'type': 'text', 'required': True})
        if product.requires_screenshot:
            fields.append({'key': f'{prefix}.screenshot_note', 'label': f'{product.title}: ссылка/комментарий к скриншоту', 'type': 'text', 'required': True})
        for item in product.extra_fields_schema_json:
            schema = dict(item)
            schema['key'] = f'{prefix}.{schema["key"]}'
            schema['label'] = f'{product.title}: {schema.get("label", schema["key"])}'
            fields.append(schema)
    return fields


async def start_checkout(callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    cart = await CartService(session).get_cart(db_user.id)
    if not cart.items:
        await callback.answer('Корзина пуста.', show_alert=True)
        return
    fields = _build_dynamic_fields([item.product for item in cart.items])
    await state.set_state(CheckoutStates.collecting_fields)
    await state.update_data(checkout_fields=fields, answers={}, step=0)
    if fields:
        await callback.message.answer(f'Оформление заказа.\n\nВведите: {fields[0]["label"]}')
    else:
        await finalize_checkout(callback.message, session, db_user, state)
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'checkout'))
async def checkout_entry(callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    await start_checkout(callback, session, db_user, state)


@router.message(CheckoutStates.collecting_fields)
async def collect_checkout_fields(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    data = await state.get_data()
    fields: list[dict] = data.get('checkout_fields', [])
    step: int = data.get('step', 0)
    answers: dict = data.get('answers', {})
    if step >= len(fields):
        await finalize_checkout(message, session, db_user, state)
        return
    field = fields[step]
    try:
        answers[field['key']] = validate_dynamic_field(field, message.text or '')
    except ValidationError as exc:
        await message.answer(str(exc))
        return
    step += 1
    await state.update_data(answers=answers, step=step)
    if step < len(fields):
        await message.answer(f'Введите: {fields[step]["label"]}')
    else:
        await finalize_checkout(message, session, db_user, state)


async def finalize_checkout(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    if not cart.items:
        await state.clear()
        await message.answer('Корзина пуста.')
        return
    data = await state.get_data()
    answers = data.get('answers', {})
    checkout_key = build_checkout_key(db_user.id, cart.id, cart.version)
    order = await OrderService(session).create_order_from_cart(
        cart=cart,
        user=db_user,
        metadata={'answers': answers},
        checkout_key=checkout_key,
        actor_user_id=db_user.id,
    )
    instruction = await ManualPaymentProvider().build_instruction(order)
    await state.clear()
    await message.answer(instruction.text)
