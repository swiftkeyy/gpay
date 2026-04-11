from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import cart_kb
from app.models import User
from app.repositories.catalog import ProductRepository
from app.services.cart import CartService
from app.services.promo import PromoService, PromoValidationError
from app.states.user import CheckoutStates
from app.utils.callbacks import CartCb, NavCb
from app.utils.idempotency import build_checkout_key
from app.utils.texts import cart_caption

router = Router(name='user_cart')


async def render_cart(callback_or_message, session: AsyncSession, db_user: User) -> None:
    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    if not cart.items:
        text = '🛒 <b>Корзина пуста.</b>'
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(text, parse_mode='HTML')
            await callback_or_message.answer()
        else:
            await callback_or_message.answer(text, parse_mode='HTML')
        return
    promo = None
    if cart.promo_code_id:
        promo = await PromoService(session).repo.get(cart.promo_code_id)
    totals = await cart_service.compute_totals(cart, db_user, promo)
    lines = [f'• {item.product.title} × {item.quantity}' for item in cart.items]
    text = cart_caption(totals.subtotal, totals.discount, totals.total, totals.currency_code) + '\n\n' + '\n'.join(lines)
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=cart_kb(cart), parse_mode='HTML')
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(text, reply_markup=cart_kb(cart), parse_mode='HTML')


@router.callback_query(NavCb.filter(F.target == 'cart'))
async def open_cart(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await render_cart(callback, session, db_user)


@router.callback_query(CartCb.filter())
async def cart_actions(callback: CallbackQuery, callback_data: CartCb, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    repo = ProductRepository(session)
    product = await repo.get_full(callback_data.product_id)
    cart_service = CartService(session)
    if callback_data.action == 'add' and product:
        await cart_service.add_item(db_user.id, product)
        await callback.answer('Товар добавлен в корзину.')
    elif callback_data.action == 'buy_now' and product:
        await cart_service.clear(db_user.id)
        await cart_service.add_item(db_user.id, product)
        await callback.answer('Товар добавлен. Переходим к оформлению.')
        await start_checkout(callback, session, db_user, state)
        return
    elif callback_data.action == 'inc':
        await cart_service.change_quantity(db_user.id, callback_data.product_id, 1)
    elif callback_data.action == 'dec':
        await cart_service.change_quantity(db_user.id, callback_data.product_id, -1)
    elif callback_data.action == 'del':
        await cart_service.remove_item(db_user.id, callback_data.product_id)
    else:
        await callback.answer('Некорректное действие.', show_alert=True)
        return
    await render_cart(callback, session, db_user)


@router.callback_query(NavCb.filter(F.target == 'cart_clear'))
async def clear_cart(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await CartService(session).clear(db_user.id)
    await callback.answer('Корзина очищена.')
    await render_cart(callback, session, db_user)


@router.callback_query(NavCb.filter(F.target == 'promo'))
async def promo_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CheckoutStates.entering_promo)
    await callback.message.answer('Введите промокод сообщением. Для отмены нажмите /start')
    await callback.answer()


@router.message(CheckoutStates.entering_promo)
async def promo_apply(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    product_ids = [item.product_id for item in cart.items]
    game_ids = [item.product.game_id for item in cart.items]
    try:
        promo = await PromoService(session).validate_code(message.text or '', user=db_user, product_ids=product_ids, game_ids=game_ids)
        cart.promo_code_id = promo.id
        await state.clear()
        await message.answer(f'🎁 Промокод {promo.code} применён.')
    except PromoValidationError as exc:
        await message.answer(f'Ошибка: {exc}')
