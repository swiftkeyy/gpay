from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import admin_menu_kb
from app.models import Admin, BotSetting, PromoCode, User
from app.models.enums import AdminRole, AuditAction, EntityType, PromoType
from app.repositories.settings import BotSettingRepository
from app.repositories.users import AdminRepository, UserRepository
from app.services.audit import AuditService
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb, NavCb
from app.utils.validators import ValidationError, validate_non_empty

router = Router(name='admin_misc')


@router.callback_query(NavCb.filter(F.target == 'admin_home'), AdminPermissionFilter('orders.view'))
async def admin_home(callback: CallbackQuery) -> None:
    await callback.message.edit_text('👮 <b>Админ-панель Game Pay</b>', reply_markup=admin_menu_kb(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'settings'), AdminPermissionFilter('settings.manage'))
async def admin_settings(callback: CallbackQuery, session: AsyncSession) -> None:
    repo = BotSettingRepository(session)
    settings = await repo.list(limit=100)
    lines = [f'• <code>{item.key}</code> = {item.value}' for item in settings]
    await callback.message.edit_text('⚙️ <b>Настройки</b>\n\n' + '\n'.join(lines), parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'users'), AdminPermissionFilter('users.view'))
async def admin_users(callback: CallbackQuery, session: AsyncSession) -> None:
    users = await UserRepository(session).list(limit=30)
    text = '👥 <b>Пользователи</b>\n\n' + '\n'.join(f'• {u.id} | {u.telegram_id} | @{u.username or "-"}' for u in users)
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'blocks'), AdminPermissionFilter('users.block'))
async def admin_blocks(callback: CallbackQuery, session: AsyncSession) -> None:
    users = list(await session.scalars(select(User).where(User.is_blocked.is_(True)).limit(50)))
    text = '🚫 <b>Блокировки</b>\n\n' + ('\n'.join(f'• {u.telegram_id}: {u.block_reason}' for u in users) or 'Нет блокировок.')
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'admins'), AdminPermissionFilter('admins.manage'))
async def admin_admins(callback: CallbackQuery, session: AsyncSession) -> None:
    admins = await AdminRepository(session).list(limit=30)
    text = '👮 <b>Админы</b>\n\n' + '\n'.join(f'• user_id={a.user_id} | role={a.role}' for a in admins)
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'logs'), AdminPermissionFilter('logs.view'))
async def admin_logs(callback: CallbackQuery, session: AsyncSession) -> None:
    from app.repositories.settings import AuditLogRepository

    logs = await AuditLogRepository(session).list(limit=30)
    text = '🧾 <b>Логи</b>\n\n' + '\n'.join(
        f'• {log.created_at:%Y-%m-%d %H:%M} | {log.action} | {log.entity_type}:{log.entity_id}' for log in logs
    )
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'stats'), AdminPermissionFilter('orders.view'))
async def admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    users_count = int(await session.scalar(select(func.count()).select_from(User)) or 0)
    orders_count = int(await session.scalar(select(func.count()).select_from(__import__('app.models', fromlist=['Order']).Order)) or 0)
    revenue = await session.scalar(select(func.coalesce(func.sum(__import__('app.models', fromlist=['Order']).Order.total_amount), 0)))
    text = f'📊 <b>Статистика</b>\n\nПользователей: {users_count}\nЗаказов: {orders_count}\nОборот: {revenue}'
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()
