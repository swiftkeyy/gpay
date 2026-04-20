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
    db_user = None,
) -> None:
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Admin command called: user_id={message.from_user.id if message.from_user else None}, admin={admin}, admin_id={admin.id if admin else None}, db_user={db_user.id if db_user else None}")
    
    # WORKAROUND: If middleware didn't load admin, try loading it directly
    if admin is None and db_user is not None:
        logger.warning(f"Middleware didn't load admin, trying direct load for user_id={db_user.id}")
        admin_result = await session.execute(
            select(Admin).where(
                Admin.user_id == db_user.id,
                Admin.is_active.is_(True),
            )
        )
        admin = admin_result.scalar_one_or_none()
        logger.warning(f"Direct admin load result: admin={'Found' if admin else 'None'}, admin_id={admin.id if admin else None}, role={admin.role if admin else None}")
    
    if message.from_user is None or not _has_access(admin, message.from_user.id):
        help_text = (
            "🔒 <b>У вас нет доступа к админ-панели.</b>\n\n"
            f"Debug info:\n"
            f"• user_id: {message.from_user.id if message.from_user else 'None'}\n"
            f"• db_user: {db_user.id if db_user else 'None'}\n"
            f"• admin object: {'Found' if admin else 'None'}\n"
            f"• admin.id: {admin.id if admin else 'N/A'}\n"
            f"• admin.role: {admin.role if admin else 'N/A'}\n"
            f"• admin.is_active: {admin.is_active if admin else 'N/A'}\n\n"
            "Для получения доступа администратор должен выполнить команду:\n\n"
            f"<code>python add_admin.py add {message.from_user.id} super_admin</code>\n\n"
            "📖 Доступные роли:\n"
            "• <b>super_admin</b> - Полный доступ\n"
            "• <b>admin</b> - Управление контентом\n"
            "• <b>moderator</b> - Модерация\n"
            "• <b>security</b> - Безопасность\n\n"
            "Подробнее: ADMIN_MANAGEMENT.md"
        )
        await message.answer(help_text, parse_mode="HTML")
        return
    await _render_admin_panel(message, session)


@router.callback_query(NavCb.filter(F.target == "admin_panel"))
async def open_admin_panel(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin | None = None,
) -> None:
    if callback.from_user is None or not _has_access(admin, callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await _render_admin_panel(callback, session)
