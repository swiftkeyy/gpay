from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import main_menu_kb
from app.models import Order, User
from app.repositories.users import UserRepository
from app.services.referral import ReferralService
from app.services.settings import SettingsService
from app.utils.callbacks import NavCb
from app.utils.texts import main_menu_text

router = Router(name='user_start')


async def _render_home(target: Message | CallbackQuery, session: AsyncSession, db_user: User) -> None:
    settings_service = SettingsService(session)
    welcome = await settings_service.get('welcome_text', 'Добро пожаловать в Game Pay.')
    shop_name = await settings_service.get('shop_name', 'Game Pay')
    text = main_menu_text(shop_name, welcome)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=main_menu_kb(), parse_mode='HTML')
    else:
        await target.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode='HTML')
        await target.answer()


@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    await state.clear()
    args = (message.text or '').split(maxsplit=1)
    if len(args) > 1 and args[1].startswith('ref_'):
        code_user_id = args[1].removeprefix('ref_')
        if code_user_id.isdigit():
            referrer = await UserRepository(session).get(int(code_user_id))
            if referrer:
                await ReferralService(session).register_referral(referrer, db_user)
    await _render_home(message, session, db_user)


@router.callback_query(NavCb.filter(F.target == 'home'))
async def home_callback(callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    await state.clear()
    await _render_home(callback, session, db_user)
