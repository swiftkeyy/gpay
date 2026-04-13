from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import admin_back_kb
from app.models import Order, User
from app.repositories.settings import AuditLogRepository, BotSettingRepository
from app.repositories.users import AdminRepository, UserRepository
from app.utils.callbacks import AdminCb, NavCb

router = Router(name="admin_misc")


@router.callback_query(NavCb.filter(F.target == "admin_home"), AdminPermissionFilter("orders.view"))
async def admin_home(callback: CallbackQuery, session: AsyncSession) -> None:
    users_count = int(await session.scalar(select(func.count()).select_from(User)) or 0)
    orders_count = int(await session.scalar(select(func.count()).select_from(Order)) or 0)
    text = (
        "👮 <b>Админ-панель Game Pay</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>"
    )
    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == "settings"), AdminPermissionFilter("settings.manage"))
async def admin_settings(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = await BotSettingRepository(session).list(limit=100)
    lines = [f"• <code>{item.key}</code> = <b>{item.value}</b>" for item in settings]
    text = "⚙️ <b>Настройки</b>\n\n" + ("\n".join(lines) if lines else "Настроек пока нет.")
    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == "users"), AdminPermissionFilter("users.view"))
async def admin_users(callback: CallbackQuery, session: AsyncSession) -> None:
    users = await UserRepository(session).list(limit=50)
    text = "👥 <b>Пользователи</b>\n\n" + (
        "\n".join(
            f"• ID <code>{u.id}</code> | TG <code>{u.telegram_id}</code> | @{u.username or '-'}"
            for u in users
        )
        if users else "Пользователей пока нет."
    )
    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == "blocks"), AdminPermissionFilter("users.block"))
async def admin_blocks(callback: CallbackQuery, session: AsyncSession) -> None:
    users = list(await session.scalars(select(User).where(User.is_blocked.is_(True)).limit(50)))
    text = "🚫 <b>Блокировки</b>\n\n" + (
        "\n".join(
            f"• TG <code>{u.telegram_id}</code> | причина: {u.block_reason or 'не указана'}"
            for u in users
        )
        if users else "Сейчас никого не заблокировано."
    )
    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == "admins"), AdminPermissionFilter("admins.manage"))
async def admin_admins(callback: CallbackQuery, session: AsyncSession) -> None:
    admins = await AdminRepository(session).list(limit=30)
    text = "👮 <b>Администраторы</b>\n\n" + (
        "\n".join(
            f"• user_id=<code>{a.user_id}</code> | role=<b>{a.role}</b> | active={'yes' if a.is_active else 'no'}"
            for a in admins
        )
        if admins else "Администраторов пока нет."
    )
    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == "logs"), AdminPermissionFilter("logs.view"))
async def admin_logs(callback: CallbackQuery, session: AsyncSession) -> None:
    logs = await AuditLogRepository(session).list(limit=30)
    text = "🧾 <b>Логи</b>\n\n" + (
        "\n".join(
            f"• {log.created_at:%Y-%m-%d %H:%M} | {log.action} | {log.entity_type}:{log.entity_id}"
            for log in logs
        )
        if logs else "Логов пока нет."
    )
    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == "stats"), AdminPermissionFilter("orders.view"))
async def admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    users_count = int(await session.scalar(select(func.count()).select_from(User)) or 0)
    orders_count = int(await session.scalar(select(func.count()).select_from(Order)) or 0)
    revenue = await session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)))

    waiting_payment = int(
        await session.scalar(
            select(func.count()).select_from(Order).where(Order.status == "waiting_payment")
        ) or 0
    )
    paid = int(
        await session.scalar(
            select(func.count()).select_from(Order).where(Order.status == "paid")
        ) or 0
    )
    processing = int(
        await session.scalar(
            select(func.count()).select_from(Order).where(Order.status == "processing")
        ) or 0
    )
    completed = int(
        await session.scalar(
            select(func.count()).select_from(Order).where(Order.status == "completed")
        ) or 0
    )

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n"
        f"💰 Оборот: <b>{revenue}</b>\n\n"
        f"⏳ Ожидают оплату: <b>{waiting_payment}</b>\n"
        f"✅ Оплачены: <b>{paid}</b>\n"
        f"🛠 В обработке: <b>{processing}</b>\n"
        f"🏁 Завершены: <b>{completed}</b>"
    )
    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()
