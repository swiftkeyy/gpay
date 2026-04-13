from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import admin_back_kb, user_card_kb, users_admin_kb
from app.models import Admin, AuditLog, Order, Review, User, UserBlock
from app.models.enums import BlockActionScope
from app.repositories.settings import AuditLogRepository, BotSettingRepository
from app.repositories.users import AdminRepository, UserRepository
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb, NavCb

router = Router(name="admin_misc")


async def _render_user_card(session: AsyncSession, user: User) -> str:
    orders_count = int(await session.scalar(select(func.count()).select_from(Order).where(Order.user_id == user.id)) or 0)
    reviews_count = int(await session.scalar(select(func.count()).select_from(Review).where(Review.user_id == user.id)) or 0)
    spent = await session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.user_id == user.id))
    active_blocks = list(
        await session.scalars(
            select(UserBlock)
            .where(UserBlock.user_id == user.id)
            .order_by(UserBlock.created_at.desc(), UserBlock.id.desc())
            .limit(3)
        )
    )
    block_text = "\n".join(
        f"• {row.scope} — {row.reason or 'без причины'}"
        for row in active_blocks
    ) or "Нет"

    return (
        f"👤 <b>Карточка пользователя</b>\n\n"
        f"DB ID: <code>{user.id}</code>\n"
        f"TG ID: <code>{user.telegram_id}</code>\n"
        f"Username: @{user.username or '-'}\n"
        f"Имя: <b>{(user.first_name or '')} {(user.last_name or '')}</b>\n"
        f"Заблокирован: <b>{'да' if user.is_blocked else 'нет'}</b>\n"
        f"Персональная скидка: <b>{user.personal_discount_percent}%</b>\n"
        f"Заказов: <b>{orders_count}</b>\n"
        f"Отзывов: <b>{reviews_count}</b>\n"
        f"Потрачено: <b>{spent}</b>\n"
        f"Реферальный код: <code>{user.referral_code or '-'}</code>\n\n"
        f"<b>Последние блокировки</b>\n{block_text}"
    )


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
async def admin_users(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext) -> None:
    if callback_data.action == "search":
        await state.set_state(AdminCatalogStates.waiting_user_search)
        await callback.message.edit_text(
            "🔎 <b>Поиск пользователя</b>\n\nОтправь TG ID, DB ID или username.",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    if callback_data.action == "list":
        users = await UserRepository(session).list(limit=50)
        await callback.message.edit_text(
            "👥 <b>Пользователи</b>",
            reply_markup=users_admin_kb(users),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    user = await UserRepository(session).get(callback_data.entity_id or 0)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    if callback_data.action == "view":
        await callback.message.edit_text(
            await _render_user_card(session, user),
            reply_markup=user_card_kb(user.id, is_blocked=user.is_blocked),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    if callback_data.action == "orders":
        orders = list(
            await session.scalars(
                select(Order)
                .where(Order.user_id == user.id)
                .order_by(Order.created_at.desc(), Order.id.desc())
                .limit(20)
            )
        )
        lines = [f"• <code>{row.order_number}</code> — <b>{row.status}</b> — {row.total_amount} {row.currency_code}" for row in orders]
        text = "📦 <b>Заказы пользователя</b>\n\n" + ("\n".join(lines) if lines else "У пользователя заказов пока нет.")
        await callback.message.edit_text(text, reply_markup=user_card_kb(user.id, is_blocked=user.is_blocked), parse_mode="HTML")
        await callback.answer()
        return

    if callback_data.action == "block":
        user.is_blocked = True
        session.add(UserBlock(user_id=user.id, blocked_by_admin_id=None, scope=BlockActionScope.FULL, reason="Заблокирован из админки"))
        await session.flush()
        await callback.message.edit_text(
            await _render_user_card(session, user),
            reply_markup=user_card_kb(user.id, is_blocked=True),
            parse_mode="HTML",
        )
        await callback.answer("Пользователь заблокирован")
        return

    if callback_data.action == "unblock":
        user.is_blocked = False
        await session.flush()
        await callback.message.edit_text(
            await _render_user_card(session, user),
            reply_markup=user_card_kb(user.id, is_blocked=False),
            parse_mode="HTML",
        )
        await callback.answer("Пользователь разблокирован")
        return

    await callback.answer("Неизвестное действие", show_alert=True)


@router.message(AdminCatalogStates.waiting_user_search, AdminPermissionFilter("users.view"))
async def admin_users_search(message: Message, session: AsyncSession, state: FSMContext) -> None:
    query = (message.text or "").strip().lstrip("@")
    stmt = select(User).order_by(User.created_at.desc(), User.id.desc()).limit(30)
    if query:
        if query.isdigit():
            stmt = stmt.where((User.id == int(query)) | (User.telegram_id == int(query)))
        else:
            stmt = stmt.where(User.username.ilike(f"%{query}%"))
    users = list(await session.scalars(stmt))
    await state.clear()

    if not users:
        await message.answer("Пользователь не найден.")
        return

    await message.answer(
        f"🔎 <b>Найдено пользователей:</b> <b>{len(users)}</b>",
        reply_markup=users_admin_kb(users),
        parse_mode="HTML",
    )


@router.callback_query(AdminCb.filter(F.section == "blocks"), AdminPermissionFilter("users.block"))
async def admin_blocks(callback: CallbackQuery, session: AsyncSession) -> None:
    rows = list(
        await session.scalars(
            select(UserBlock).order_by(UserBlock.created_at.desc(), UserBlock.id.desc()).limit(30)
        )
    )
    text = "🚫 <b>Блокировки</b>\n\n" + (
        "\n".join(
            f"• user_id=<code>{row.user_id}</code> | {row.scope} | {row.reason or 'без причины'}"
            for row in rows
        )
        if rows else "Сейчас блокировок нет."
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
    reviews_count = int(await session.scalar(select(func.count()).select_from(Review)) or 0)
    disputes_count = int(await session.scalar(select(func.count()).select_from(Order).where(Order.status == "dispute")) or 0)
    revenue = await session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)))

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n"
        f"⭐ Отзывов: <b>{reviews_count}</b>\n"
        f"⚠️ Споров: <b>{disputes_count}</b>\n"
        f"💰 Оборот: <b>{revenue}</b>"
    )
    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()
