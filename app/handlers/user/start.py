from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import main_menu_kb
from app.models import Admin, User
from app.repositories.users import UserRepository
from app.services.referral import ReferralService
from app.services.settings import SettingsService
from app.utils.callbacks import NavCb
from app.utils.texts import main_menu_text

router = Router(name="user_start")


async def _render_home(
    target: Message | CallbackQuery,
    session: AsyncSession,
    db_user: User,
    admin: Admin | None = None,
) -> None:
    settings_service = SettingsService(session)

    welcome = await settings_service.get(
        "welcome_text",
        "Добро пожаловать в Game Pay.",
    )
    shop_name = await settings_service.get(
        "shop_name",
        "Game Pay",
    )

    text = main_menu_text(shop_name or "Game Pay", welcome or "Добро пожаловать в Game Pay.")
    menu = main_menu_kb(is_admin=admin is not None)

    if isinstance(target, Message):
        await target.answer(
            text,
            reply_markup=menu,
            parse_mode="HTML",
        )
    else:
        if target.message:
            await target.message.edit_text(
                text,
                reply_markup=menu,
                parse_mode="HTML",
            )
        await target.answer()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    session: AsyncSession,
    db_user: User,
    state: FSMContext,
    admin: Admin | None = None,
) -> None:
    await state.clear()

    args = (message.text or "").split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("ref_"):
        code_user_id = args[1].removeprefix("ref_")
        if code_user_id.isdigit():
            user_repo = UserRepository(session)
            referrer = await user_repo.get(int(code_user_id))
            if referrer:
                referral_service = ReferralService(session)
                await referral_service.register_referral(referrer, db_user)

    await _render_home(message, session, db_user, admin)


@router.callback_query(NavCb.filter(F.target == "home"))
async def home_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    state: FSMContext,
    admin: Admin | None = None,
) -> None:
    await state.clear()
    await _render_home(callback, session, db_user, admin)
