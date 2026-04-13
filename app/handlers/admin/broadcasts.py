from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import admin_back_kb
from app.models.enums import BroadcastStatus
from app.repositories.settings import BroadcastRepository
from app.services.broadcast import BroadcastService
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb

router = Router(name="admin_broadcasts")


@router.callback_query(AdminCb.filter(F.section == "broadcasts"), AdminPermissionFilter("broadcasts.manage"))
async def broadcast_entry(
    callback: CallbackQuery,
    callback_data: AdminCb,
    session,
    state: FSMContext,
) -> None:
    broadcasts = await BroadcastRepository(session).list(limit=30)
    lines = [f"• {b.title} | {b.status}" for b in broadcasts]

    text = "📢 <b>Рассылки</b>\n\n" + ("\n".join(lines) if lines else "Пока нет рассылок.")
    text += "\n\nОтправь следующим сообщением текст новой рассылки."

    await callback.message.edit_text(
        text,
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await state.set_state(AdminCatalogStates.waiting_broadcast_text)
    await callback.answer()


@router.message(AdminCatalogStates.waiting_broadcast_text, AdminPermissionFilter("broadcasts.manage"))
async def broadcast_create(
    message: Message,
    session,
    state: FSMContext,
    bot: Bot,
) -> None:
    repo = BroadcastRepository(session)
    item = await repo.create(
        title="Broadcast",
        text=message.text or "",
        status=BroadcastStatus.DRAFT,
    )
    sent = await BroadcastService(session).send(bot, item)
    await state.clear()
    await message.answer(
        f"✅ Рассылка отправлена. Получателей: <b>{sent}</b>",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
