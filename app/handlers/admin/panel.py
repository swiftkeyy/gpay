from __future__ import annotations

from dataclasses import dataclass

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Admin, Game
from app.utils.callbacks import NavCb

router = Router(name="admin_panel")
settings = get_settings()


class GameCrudStates(StatesGroup):
    create_title = State()
    create_slug = State()
    create_description = State()
    create_sort_order = State()

    edit_title = State()
    edit_slug = State()
    edit_description = State()
    edit_sort_order = State()


@dataclass(slots=True)
class GameDraft:
    title: str
    slug: str
    description: str
    sort_order: int


def _has_access(admin: Admin | None, user_id: int) -> bool:
    return admin is not None or user_id in {
        settings.super_admin_tg_id,
        settings.second_admin_tg_id,
    }


def _slugify(value: str) -> str:
    value = value.strip().lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    value = value.replace(" ", "-")
    cleaned = "".join(ch for ch in value if ch in allowed or "а" <= ch <= "я" or ch == "ё")
    cleaned = cleaned.replace("--", "-").strip("-")
    return cleaned or "game"


def _admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📦 Заказы", callback_data=NavCb(target="admin_orders").pack())
    b.button(text="🎮 Игры", callback_data=NavCb(target="admin_games").pack())
    b.button(text="🗂 Категории", callback_data=NavCb(target="admin_categories").pack())
    b.button(text="🛍 Товары", callback_data=NavCb(target="admin_products").pack())
    b.button(text="💸 Цены", callback_data=NavCb(target="admin_prices").pack())
    b.adjust(1)
    return b.as_markup()


def _back_to_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=NavCb(target="admin_panel").pack())
    return b.as_markup()


def _games_list_kb(games: list[Game]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    for game in games:
        status = "🟢" if game.is_active else "⚪"
        b.button(text=f"{status} {game.title}", callback_data=f"ag:view:{game.id}")

    b.button(text="➕ Добавить игру", callback_data="ag:create")
    b.button(text="🔙 В админку", callback_data=NavCb(target="admin_panel").pack())
    b.adjust(1)
    return b.as_markup()


def _game_actions_kb(game_id: int, is_active: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Название", callback_data=f"ag:edit_title:{game_id}")
    b.button(text="🔗 Slug", callback_data=f"ag:edit_slug:{game_id}")
    b.button(text="📝 Описание", callback_data=f"ag:edit_desc:{game_id}")
    b.button(text="↕️ Сортировка", callback_data=f"ag:edit_sort:{game_id}")
    b.button(
        text="⏸ Выключить" if is_active else "▶️ Включить",
        callback_data=f"ag:toggle:{game_id}",
    )
    b.button(text="🗑 Удалить", callback_data=f"ag:delete:{game_id}")
    b.button(text="🔙 К играм", callback_data=NavCb(target="admin_games").pack())
    b.adjust(1)
    return b.as_markup()


async def _get_game(session: AsyncSession, game_id: int) -> Game | None:
    result = await session.execute(
        select(Game).where(Game.id == game_id, Game.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def _render_admin_panel(target: Message | CallbackQuery) -> None:
    text = "👮 <b>Админ-панель</b>\n\nВыберите раздел:"
    if isinstance(target, Message):
        await target.answer(text, reply_markup=_admin_main_kb(), parse_mode="HTML")
    else:
        if target.message:
            await target.message.edit_text(
                text,
                reply_markup=_admin_main_kb(),
                parse_mode="HTML",
            )
        await target.answer()


async def _render_games_list(callback: CallbackQuery, session: AsyncSession) -> None:
    result = await session.execute(
        select(Game)
        .where(Game.is_deleted.is_(False))
        .order_by(Game.sort_order.asc(), Game.id.asc())
    )
    games = list(result.scalars().all())

    text = "🎮 <b>Игры</b>\n\nВыберите игру или создайте новую."
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=_games_list_kb(games),
            parse_mode="HTML",
        )
    await callback.answer()


async def _render_game_view(callback: CallbackQuery, game: Game) -> None:
    text = (
        f"🎮 <b>{game.title}</b>\n\n"
        f"<b>ID:</b> <code>{game.id}</code>\n"
        f"<b>Slug:</b> <code>{game.slug}</code>\n"
        f"<b>Активна:</b> {'Да' if game.is_active else 'Нет'}\n"
        f"<b>Сортировка:</b> {game.sort_order}\n\n"
        f"{game.description or 'Описание отсутствует.'}"
    )
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=_game_actions_kb(game.id, game.is_active),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(Command("admin"))
async def admin_command(
    message: Message,
    admin: Admin | None = None,
) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not _has_access(admin, user_id):
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return
    await _render_admin_panel(message)


@router.callback_query(NavCb.filter(F.target == "admin_panel"))
async def admin_panel(callback: CallbackQuery, admin: Admin | None = None) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await _render_admin_panel(callback)


@router.callback_query(NavCb.filter(F.target == "admin_games"))
async def admin_games(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await _render_games_list(callback, session)


@router.callback_query(F.data == "ag:create")
async def game_create_start(
    callback: CallbackQuery,
    state: FSMContext,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await state.set_state(GameCrudStates.create_title)

    if callback.message:
        await callback.message.edit_text(
            "➕ <b>Создание игры</b>\n\nВведите название игры:",
            reply_markup=_back_to_panel_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(GameCrudStates.create_title)
async def game_create_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer("Название слишком короткое. Введите ещё раз.")
        return

    await state.update_data(title=title)
    await state.set_state(GameCrudStates.create_slug)
    await message.answer("Введите slug игры.\nПример: <code>brawl-stars</code>", parse_mode="HTML")


@router.message(GameCrudStates.create_slug)
async def game_create_slug(message: Message, state: FSMContext, session: AsyncSession) -> None:
    slug = _slugify(message.text or "")
    exists = await session.execute(select(Game).where(Game.slug == slug))
    if exists.scalar_one_or_none():
        await message.answer("Такой slug уже существует. Введите другой.")
        return

    await state.update_data(slug=slug)
    await state.set_state(GameCrudStates.create_description)
    await message.answer("Введите описание игры.")


@router.message(GameCrudStates.create_description)
async def game_create_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    await state.update_data(description=description)
    await state.set_state(GameCrudStates.create_sort_order)
    await message.answer("Введите sort_order числом. Например: 10")


@router.message(GameCrudStates.create_sort_order)
async def game_create_sort_order(message: Message, state: FSMContext, session: AsyncSession) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужно число. Введите sort_order ещё раз.")
        return

    data = await state.get_data()
    game = Game(
        slug=data["slug"],
        title=data["title"],
        description=data.get("description"),
        image_id=None,
        is_active=True,
        sort_order=int(raw),
        is_deleted=False,
    )
    session.add(game)
    await session.commit()
    await state.clear()

    await message.answer(
        f"✅ Игра создана: <b>{game.title}</b>",
        reply_markup=_back_to_panel_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("ag:view:"))
async def game_view(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        game_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Некорректная игра", show_alert=True)
        return

    game = await _get_game(session, game_id)
    if game is None:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    await _render_game_view(callback, game)


@router.callback_query(F.data.startswith("ag:toggle:"))
async def game_toggle(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        game_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Некорректная игра", show_alert=True)
        return

    game = await _get_game(session, game_id)
    if game is None:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    game.is_active = not game.is_active
    await session.commit()
    await _render_game_view(callback, game)


@router.callback_query(F.data.startswith("ag:delete:"))
async def game_delete(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        game_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Некорректная игра", show_alert=True)
        return

    game = await _get_game(session, game_id)
    if game is None:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    game.is_deleted = True
    game.is_active = False
    await session.commit()
    await _render_games_list(callback, session)


@router.callback_query(F.data.startswith("ag:edit_title:"))
async def game_edit_title_start(
    callback: CallbackQuery,
    state: FSMContext,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        game_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Некорректная игра", show_alert=True)
        return

    await state.clear()
    await state.update_data(game_id=game_id)
    await state.set_state(GameCrudStates.edit_title)

    if callback.message:
        await callback.message.edit_text(
            "✏️ Введите новое название игры:",
            reply_markup=_back_to_panel_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(GameCrudStates.edit_title)
async def game_edit_title(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer("Название слишком короткое. Введите ещё раз.")
        return

    data = await state.get_data()
    game = await _get_game(session, int(data["game_id"]))
    if game is None:
        await state.clear()
        await message.answer("Игра не найдена.")
        return

    game.title = title
    await session.commit()
    await state.clear()
    await message.answer("✅ Название игры обновлено.", reply_markup=_back_to_panel_kb())


@router.callback_query(F.data.startswith("ag:edit_slug:"))
async def game_edit_slug_start(
    callback: CallbackQuery,
    state: FSMContext,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        game_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Некорректная игра", show_alert=True)
        return

    await state.clear()
    await state.update_data(game_id=game_id)
    await state.set_state(GameCrudStates.edit_slug)

    if callback.message:
        await callback.message.edit_text(
            "🔗 Введите новый slug игры:",
            reply_markup=_back_to_panel_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(GameCrudStates.edit_slug)
async def game_edit_slug(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    slug = _slugify(message.text or "")
    data = await state.get_data()
    game_id = int(data["game_id"])

    existing = await session.execute(
        select(Game).where(Game.slug == slug, Game.id != game_id)
    )
    if existing.scalar_one_or_none():
        await message.answer("Такой slug уже существует. Введите другой.")
        return

    game = await _get_game(session, game_id)
    if game is None:
        await state.clear()
        await message.answer("Игра не найдена.")
        return

    game.slug = slug
    await session.commit()
    await state.clear()
    await message.answer("✅ Slug игры обновлён.", reply_markup=_back_to_panel_kb())


@router.callback_query(F.data.startswith("ag:edit_desc:"))
async def game_edit_desc_start(
    callback: CallbackQuery,
    state: FSMContext,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        game_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Некорректная игра", show_alert=True)
        return

    await state.clear()
    await state.update_data(game_id=game_id)
    await state.set_state(GameCrudStates.edit_description)

    if callback.message:
        await callback.message.edit_text(
            "📝 Введите новое описание игры:",
            reply_markup=_back_to_panel_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(GameCrudStates.edit_description)
async def game_edit_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    description = (message.text or "").strip()
    data = await state.get_data()
    game = await _get_game(session, int(data["game_id"]))
    if game is None:
        await state.clear()
        await message.answer("Игра не найдена.")
        return

    game.description = description
    await session.commit()
    await state.clear()
    await message.answer("✅ Описание игры обновлено.", reply_markup=_back_to_panel_kb())


@router.callback_query(F.data.startswith("ag:edit_sort:"))
async def game_edit_sort_start(
    callback: CallbackQuery,
    state: FSMContext,
    admin: Admin | None = None,
) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if not _has_access(admin, user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        game_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Некорректная игра", show_alert=True)
        return

    await state.clear()
    await state.update_data(game_id=game_id)
    await state.set_state(GameCrudStates.edit_sort_order)

    if callback.message:
        await callback.message.edit_text(
            "↕️ Введите новый sort_order:",
            reply_markup=_back_to_panel_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(GameCrudStates.edit_sort_order)
async def game_edit_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужно число. Введите ещё раз.")
        return

    data = await state.get_data()
    game = await _get_game(session, int(data["game_id"]))
    if game is None:
        await state.clear()
        await message.answer("Игра не найдена.")
        return

    game.sort_order = int(raw)
    await session.commit()
    await state.clear()
    await message.answer("✅ Сортировка игры обновлена.", reply_markup=_back_to_panel_kb())
