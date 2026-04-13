from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.keyboards.admin import admin_main_kb
from app.models import Admin, Game, Order, Product, User
from app.utils.callbacks import NavCb

router = Router(name="admin_panel")
settings = get_settings()


def _has_access(admin: Admin | None, user_id: int) -> bool:
    return admin is not None or user_id in {
        settings.super_admin_tg_id,
        settings.second_admin_tg_id,
    }


async def _build_panel_text(session: AsyncSession) -> str:
    users_count = int(await session.scalar(select(func.count()).select_from(User)) or 0)
    orders_count = int(await session.scalar(select(func.count()).select_from(Order)) or 0)
    games_count = int(
        await session.scalar(
            select(func.count()).select_from(Game).where(Game.is_deleted.is_(False))
        )
        or 0
    )
    products_count = int(
        await session.scalar(
            select(func.count()).select_from(Product).where(Product.is_deleted.is_(False))
        )
        or 0
    )

    return (
        "👮 <b>Админ-панель Game Pay</b>\n\n"
        "Управляй витриной, заказами и контентом из одного места.\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n"
        f"🎮 Игр: <b>{games_count}</b>\n"
        f"🛍 Товаров: <b>{products_count}</b>"
    )


async def _render_admin_panel(target: Message | CallbackQuery, session: AsyncSession) -> None:
    text = await _build_panel_text(session)
    markup = admin_main_kb()
    if isinstance(target, Message):
        await target.answer(text, reply_markup=markup, parse_mode="HTML")
    else:
        if target.message:
            await target.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        await target.answer()


@router.message(Command("admin"))
async def admin_command(
    message: Message,
    session: AsyncSession,
    admin: Admin | None = None,
) -> None:
    if message.from_user is None or not _has_access(admin, message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    await _render_admin_panel(message, session)


@router.callback_query(NavCb.filter(F.target == "admin_panel"))
async def open_admin_panel(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin | None = None,
) -> None:
    if callback.from_user is None or not _has_access(admin, callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await _render_admin_panel(callback, session)
