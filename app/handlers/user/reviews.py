from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderStatus, Review, ReviewStatus, User
from app.repositories.settings import ReviewRepository
from app.states.user import CheckoutStates
from app.utils.callbacks import NavCb
from app.utils.validators import validate_positive_int

router = Router(name='user_reviews')


@router.callback_query(NavCb.filter(F.target == 'reviews'))
async def reviews_info(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        '⭐ <b>Отзывы</b>\n\nОставить отзыв можно после выполненного заказа.', parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'review_create'))
async def review_start(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    order = await session.get(Order, callback_data.entity_id)
    if not order or order.user_id != db_user.id or order.status not in {OrderStatus.FULFILLED, OrderStatus.COMPLETED}:
        await callback.answer('Оставить отзыв можно только после выполненного заказа.', show_alert=True)
        return
    await state.set_state(CheckoutStates.leaving_review)
    await state.update_data(review_order_id=order.id)
    await callback.message.answer('Введите отзыв в формате: <оценка 1-5> ; <текст отзыва>')
    await callback.answer()


@router.message(CheckoutStates.leaving_review)
async def review_submit(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    payload = (message.text or '').split(';', maxsplit=1)
    if len(payload) != 2:
        await message.answer('Формат: 5 ; отличный сервис')
        return
    rating = validate_positive_int(payload[0].strip(), 'rating')
    text = payload[1].strip()
    data = await state.get_data()
    order_id = data.get('review_order_id')
    await ReviewRepository(session).create(
        user_id=db_user.id,
        order_id=order_id,
        rating=min(rating, 5),
        text=text,
        status=ReviewStatus.HIDDEN,
    )
    await state.clear()
    await message.answer('Спасибо! Отзыв отправлен на модерацию.')
