from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import review_admin_actions_kb, reviews_admin_kb
from app.models import Review
from app.models.enums import ReviewStatus
from app.utils.callbacks import AdminCb

router = Router(name="admin_reviews")


STATUS_FILTERS = {
    "filter_hidden": ReviewStatus.HIDDEN,
    "filter_published": ReviewStatus.PUBLISHED,
    "filter_rejected": ReviewStatus.REJECTED,
}


async def _list_reviews(session: AsyncSession, *, status: ReviewStatus | None = None) -> list[Review]:
    stmt = select(Review).order_by(Review.created_at.desc(), Review.id.desc()).limit(50)
    if status is not None:
        stmt = stmt.where(Review.status == status)
    return list(await session.scalars(stmt))


def _review_card(review: Review) -> str:
    return (
        f"⭐ <b>Отзыв #{review.id}</b>\n\n"
        f"Пользователь ID: <code>{review.user_id}</code>\n"
        f"Заказ ID: <code>{review.order_id}</code>\n"
        f"Товар ID: <code>{review.product_id or 0}</code>\n"
        f"Оценка: <b>{review.rating}/5</b>\n"
        f"Статус: <b>{review.status}</b>\n"
        f"Создан: <b>{review.created_at.strftime('%Y-%m-%d %H:%M')}</b>\n\n"
        f"{review.text or 'Без текста'}"
    )


@router.callback_query(AdminCb.filter(F.section == "reviews"), AdminPermissionFilter("reviews.manage"))
async def admin_reviews(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession) -> None:
    action = callback_data.action

    if action == "list" or action in STATUS_FILTERS:
        status = STATUS_FILTERS.get(action)
        reviews = await _list_reviews(session, status=status)
        text = "⭐ <b>Отзывы</b>"
        if status is not None:
            text += f"\n\nФильтр: <b>{status}</b>"
        await callback.message.edit_text(text, reply_markup=reviews_admin_kb(reviews, filter_status=status.value if status else None), parse_mode="HTML")
        await callback.answer()
        return

    review = await session.get(Review, callback_data.entity_id or 0)
    if review is None:
        await callback.answer("Отзыв не найден", show_alert=True)
        return

    if action == "view":
        await callback.message.edit_text(_review_card(review), reply_markup=review_admin_actions_kb(review.id), parse_mode="HTML")
        await callback.answer()
        return

    if action == "publish":
        review.status = ReviewStatus.PUBLISHED
    elif action == "hide":
        review.status = ReviewStatus.HIDDEN
    elif action == "reject":
        review.status = ReviewStatus.REJECTED
    else:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    review.moderated_at = datetime.now(timezone.utc)
    review.moderated_by_admin_id = None
    await session.flush()
    await callback.message.edit_text(_review_card(review), reply_markup=review_admin_actions_kb(review.id), parse_mode="HTML")
    await callback.answer("Статус отзыва обновлён")
