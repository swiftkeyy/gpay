from __future__ import annotations

from aiogram import F, Router
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.models.enums import BroadcastStatus
from app.repositories.settings import BroadcastRepository
from app.services.broadcast import BroadcastService
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb

router = Router(name='admin_broadcasts')


@router.callback_query(AdminCb.filter(F.section == 'broadcasts'), AdminPermissionFilter('broadcasts.manage'))
async def broadcast_entry(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext) -> None:
    broadcasts = await BroadcastRepository(session).list(limit=30)
    lines = [f'• {b.title} | {b.status}' for b in broadcasts]
    await callback.message.edit_text('📢 <b>Рассылки</b>\n\n' + ('\n'.join(lines) or 'Пока нет рассылок.'), parse_mode='HTML')
    await callback.message.answer('Введите текст новой рассылки сообщением.')
    await state.set_state(AdminCatalogStates.waiting_broadcast_text)
    await callback.answer()


@router.message(AdminCatalogStates.waiting_broadcast_text, AdminPermissionFilter('broadcasts.manage'))
async def broadcast_create(message: Message, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    repo = BroadcastRepository(session)
    item = await repo.create(title='Broadcast', text=message.text or '', status=BroadcastStatus.DRAFT)
    sent = await BroadcastService(session).send(bot, item)
    await state.clear()
    await message.answer(f'Рассылка отправлена. Получателей: {sent}')
