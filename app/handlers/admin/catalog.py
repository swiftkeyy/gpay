from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import get_settings
from app.keyboards.admin import (
    categories_admin_kb,
    category_actions_kb,
    game_actions_kb,
    games_admin_kb,
    product_actions_kb,
    products_admin_kb,
)
from app.models import Admin, Category, Game, Product
from app.models.enums import FulfillmentType
from app.states.admin import AdminCrudStates
from app.utils.callbacks import AdminCb

router = Router(name="admin_catalog")
settings = get_settings()


def _has_access(user_id: int, admin: Admin | None) -> bool:
    return admin is not None or user_id in {settings.super_admin_tg_id, settings.second_admin_tg_id}


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = value.replace(" ", "-").replace("_", "-")
    value = re.sub(r"[^a-z0-9-]+", "", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:64] or "item"


@router.callback_query(AdminCb.filter(F.section == "games"))
async def admin_games(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(callback.from_user.id, admin):
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback_data.action == "list":
        games = list(await session.scalars(select(Game).where(Game.is_deleted.is_(False)).order_by(Game.sort_order, Game.id)))
        if callback.message:
            await callback.message.edit_text("🎮 <b>Игры</b>", reply_markup=games_admin_kb(games), parse_mode="HTML")
        await callback.answer()
        return

    if callback_data.action == "create":
        await state.clear()
        await state.set_state(AdminCrudStates.waiting_game_title)
        await callback.message.answer("Введите название новой игры сообщением.")
        await callback.answer()
        return

    game = await session.get(Game, callback_data.entity_id or 0)
    if not game or game.is_deleted:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    if callback_data.action == "view":
        text = f"🎮 <b>{game.title}</b>\n\nID: <code>{game.id}</code>\nSlug: <code>{game.slug}</code>\nАктивна: {'да' if game.is_active else 'нет'}"
        await callback.message.edit_text(text, reply_markup=game_actions_kb(game.id, game.is_active), parse_mode="HTML")
    elif callback_data.action == "edit":
        await state.clear()
        await state.set_state(AdminCrudStates.waiting_game_edit_title)
        await state.update_data(game_id=game.id)
        await callback.message.answer(f"Введите новое название для игры «{game.title}».")
    elif callback_data.action == "toggle":
        game.is_active = not game.is_active
        await session.flush()
        await callback.answer("Статус игры обновлён.")
        text = f"🎮 <b>{game.title}</b>\n\nID: <code>{game.id}</code>\nSlug: <code>{game.slug}</code>\nАктивна: {'да' if game.is_active else 'нет'}"
        await callback.message.edit_text(text, reply_markup=game_actions_kb(game.id, game.is_active), parse_mode="HTML")
        return
    elif callback_data.action == "delete_confirm":
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить", callback_data=AdminCb(section="games", action="delete_apply", entity_id=game.id).pack())
        builder.button(text="❌ Отмена", callback_data=AdminCb(section="games", action="view", entity_id=game.id).pack())
        builder.adjust(1)
        await callback.message.edit_text(f"Удалить игру <b>{game.title}</b>?\nЭто soft delete.", reply_markup=builder.as_markup(), parse_mode="HTML")
    elif callback_data.action == "delete_apply":
        game.is_deleted = True
        game.is_active = False
        await session.flush()
        games = list(await session.scalars(select(Game).where(Game.is_deleted.is_(False)).order_by(Game.sort_order, Game.id)))
        await callback.message.edit_text("🎮 <b>Игры</b>", reply_markup=games_admin_kb(games), parse_mode="HTML")
        await callback.answer("Игра удалена.")
        return
    await callback.answer()


@router.message(AdminCrudStates.waiting_game_title)
async def create_game(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым.")
        return
    slug = _slugify(title)
    exists = await session.scalar(select(Game).where(Game.slug == slug))
    if exists:
        slug = f"{slug}-{message.from_user.id % 10000}"
    game = Game(slug=slug, title=title, description=None, image_id=None, is_active=True, sort_order=100, is_deleted=False)
    session.add(game)
    await session.flush()
    await state.clear()
    await message.answer(f"✅ Игра создана: <b>{game.title}</b>", parse_mode="HTML")


@router.message(AdminCrudStates.waiting_game_edit_title)
async def edit_game_title(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    data = await state.get_data()
    game = await session.get(Game, data.get("game_id", 0))
    if not game:
        await state.clear()
        await message.answer("Игра не найдена.")
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым.")
        return
    game.title = title
    await session.flush()
    await state.clear()
    await message.answer(f"✅ Название игры обновлено: <b>{game.title}</b>", parse_mode="HTML")


@router.callback_query(AdminCb.filter(F.section == "categories"))
async def admin_categories(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(callback.from_user.id, admin):
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback_data.action == "list":
        stmt = select(Category).where(Category.is_deleted.is_(False)).options(joinedload(Category.game)).order_by(Category.sort_order, Category.id)
        if callback_data.entity_id:
            stmt = stmt.where(Category.game_id == callback_data.entity_id)
        categories = list(await session.scalars(stmt))
        await callback.message.edit_text("🗂 <b>Категории</b>", reply_markup=categories_admin_kb(categories, game_id=callback_data.entity_id), parse_mode="HTML")
        await callback.answer()
        return

    if callback_data.action == "create":
        await state.clear()
        await state.set_state(AdminCrudStates.waiting_category_game_id)
        if callback_data.entity_id:
            await state.update_data(prefill_game_id=callback_data.entity_id)
            await callback.message.answer("Введите название новой категории сообщением.")
            await state.set_state(AdminCrudStates.waiting_category_title)
        else:
            await callback.message.answer("Введите ID игры, к которой привязать категорию.")
        await callback.answer()
        return

    category = await session.get(Category, callback_data.entity_id or 0)
    if not category or category.is_deleted:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    if callback_data.action == "view":
        game = await session.get(Game, category.game_id)
        text = f"🗂 <b>{category.title}</b>\n\nID: <code>{category.id}</code>\nИгра: <b>{game.title if game else category.game_id}</b>\nSlug: <code>{category.slug}</code>\nАктивна: {'да' if category.is_active else 'нет'}"
        await callback.message.edit_text(text, reply_markup=category_actions_kb(category.id), parse_mode="HTML")
    elif callback_data.action == "edit":
        await state.clear()
        await state.set_state(AdminCrudStates.waiting_category_edit_title)
        await state.update_data(category_id=category.id)
        await callback.message.answer(f"Введите новое название для категории «{category.title}».")
    elif callback_data.action == "toggle":
        category.is_active = not category.is_active
        await session.flush()
        await callback.answer("Статус категории обновлён.")
        game = await session.get(Game, category.game_id)
        text = f"🗂 <b>{category.title}</b>\n\nID: <code>{category.id}</code>\nИгра: <b>{game.title if game else category.game_id}</b>\nSlug: <code>{category.slug}</code>\nАктивна: {'да' if category.is_active else 'нет'}"
        await callback.message.edit_text(text, reply_markup=category_actions_kb(category.id), parse_mode="HTML")
        return
    elif callback_data.action == "delete_confirm":
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить", callback_data=AdminCb(section="categories", action="delete_apply", entity_id=category.id).pack())
        builder.button(text="❌ Отмена", callback_data=AdminCb(section="categories", action="view", entity_id=category.id).pack())
        builder.adjust(1)
        await callback.message.edit_text(f"Удалить категорию <b>{category.title}</b>?\nЭто soft delete.", reply_markup=builder.as_markup(), parse_mode="HTML")
    elif callback_data.action == "delete_apply":
        category.is_deleted = True
        category.is_active = False
        await session.flush()
        categories = list(await session.scalars(select(Category).where(Category.is_deleted.is_(False)).options(joinedload(Category.game)).order_by(Category.sort_order, Category.id)))
        await callback.message.edit_text("🗂 <b>Категории</b>", reply_markup=categories_admin_kb(categories), parse_mode="HTML")
        await callback.answer("Категория удалена.")
        return
    await callback.answer()


@router.message(AdminCrudStates.waiting_category_game_id)
async def create_category_game_pick(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Введите числовой ID игры.")
        return
    game = await session.get(Game, int(text))
    if not game or game.is_deleted:
        await message.answer("Игра не найдена.")
        return
    await state.update_data(prefill_game_id=game.id)
    await state.set_state(AdminCrudStates.waiting_category_title)
    await message.answer(f"Теперь введите название категории для игры «{game.title}».")


@router.message(AdminCrudStates.waiting_category_title)
async def create_category_title(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    data = await state.get_data()
    game_id = data.get("prefill_game_id")
    if not game_id:
        await state.clear()
        await message.answer("Игра для категории не выбрана.")
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым.")
        return
    slug = _slugify(title)
    category = Category(game_id=game_id, slug=slug, title=title, description=None, image_id=None, is_active=True, sort_order=100, is_deleted=False)
    session.add(category)
    await session.flush()
    await state.clear()
    await message.answer(f"✅ Категория создана: <b>{category.title}</b>", parse_mode="HTML")


@router.message(AdminCrudStates.waiting_category_edit_title)
async def edit_category_title(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    data = await state.get_data()
    category = await session.get(Category, data.get("category_id", 0))
    if not category:
        await state.clear()
        await message.answer("Категория не найдена.")
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым.")
        return
    category.title = title
    await session.flush()
    await state.clear()
    await message.answer(f"✅ Название категории обновлено: <b>{category.title}</b>", parse_mode="HTML")


@router.callback_query(AdminCb.filter(F.section == "products"))
async def admin_products(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(callback.from_user.id, admin):
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback_data.action == "list":
        stmt = select(Product).where(Product.is_deleted.is_(False)).options(joinedload(Product.category), joinedload(Product.game)).order_by(Product.sort_order, Product.id)
        if callback_data.entity_id:
            stmt = stmt.where(Product.category_id == callback_data.entity_id)
        products = list(await session.scalars(stmt))
        await callback.message.edit_text("🛍 <b>Товары</b>", reply_markup=products_admin_kb(products, category_id=callback_data.entity_id), parse_mode="HTML")
        await callback.answer()
        return

    if callback_data.action == "create":
        await state.clear()
        await state.update_data(prefill_category_id=callback_data.entity_id)
        if callback_data.entity_id:
            await state.set_state(AdminCrudStates.waiting_product_title)
            await callback.message.answer("Введите название нового товара.")
        else:
            await state.set_state(AdminCrudStates.waiting_product_category_id)
            await callback.message.answer("Введите ID категории, к которой привязать товар.")
        await callback.answer()
        return

    product = await session.get(Product, callback_data.entity_id or 0)
    if not product or product.is_deleted:
        await callback.answer("Товар не найден", show_alert=True)
        return

    if callback_data.action == "view":
        text = f"🛍 <b>{product.title}</b>\n\nID: <code>{product.id}</code>\nSlug: <code>{product.slug}</code>\nКатегория ID: <code>{product.category_id}</code>\nИгра ID: <code>{product.game_id}</code>\nАктивен: {'да' if product.is_active else 'нет'}"
        await callback.message.edit_text(text, reply_markup=product_actions_kb(product.id), parse_mode="HTML")
    elif callback_data.action == "edit":
        await state.clear()
        await state.set_state(AdminCrudStates.waiting_product_edit_title)
        await state.update_data(product_id=product.id)
        await callback.message.answer(f"Введите новое название для товара «{product.title}».")
    elif callback_data.action == "toggle":
        product.is_active = not product.is_active
        await session.flush()
        await callback.answer("Статус товара обновлён.")
        text = f"🛍 <b>{product.title}</b>\n\nID: <code>{product.id}</code>\nSlug: <code>{product.slug}</code>\nКатегория ID: <code>{product.category_id}</code>\nИгра ID: <code>{product.game_id}</code>\nАктивен: {'да' if product.is_active else 'нет'}"
        await callback.message.edit_text(text, reply_markup=product_actions_kb(product.id), parse_mode="HTML")
        return
    elif callback_data.action == "delete_confirm":
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить", callback_data=AdminCb(section="products", action="delete_apply", entity_id=product.id).pack())
        builder.button(text="❌ Отмена", callback_data=AdminCb(section="products", action="view", entity_id=product.id).pack())
        builder.adjust(1)
        await callback.message.edit_text(f"Удалить товар <b>{product.title}</b>?\nЭто soft delete.", reply_markup=builder.as_markup(), parse_mode="HTML")
    elif callback_data.action == "delete_apply":
        product.is_deleted = True
        product.is_active = False
        await session.flush()
        products = list(await session.scalars(select(Product).where(Product.is_deleted.is_(False)).options(joinedload(Product.category), joinedload(Product.game)).order_by(Product.sort_order, Product.id)))
        await callback.message.edit_text("🛍 <b>Товары</b>", reply_markup=products_admin_kb(products), parse_mode="HTML")
        await callback.answer("Товар удалён.")
        return
    await callback.answer()


@router.message(AdminCrudStates.waiting_product_category_id)
async def create_product_pick_category(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Введите числовой ID категории.")
        return
    category = await session.get(Category, int(text))
    if not category or category.is_deleted:
        await message.answer("Категория не найдена.")
        return
    await state.update_data(prefill_category_id=category.id)
    await state.set_state(AdminCrudStates.waiting_product_title)
    await message.answer(f"Теперь введите название товара для категории «{category.title}».")


@router.message(AdminCrudStates.waiting_product_title)
async def create_product_title(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым.")
        return
    await state.update_data(product_title=title)
    await state.set_state(AdminCrudStates.waiting_product_slug)
    await message.answer("Введите slug товара латиницей или отправьте '-' для автогенерации.")


@router.message(AdminCrudStates.waiting_product_slug)
async def create_product_slug(message: Message, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    slug = (message.text or "").strip()
    if slug == "-":
        data = await state.get_data()
        slug = _slugify(data.get("product_title", "product"))
    await state.update_data(product_slug=_slugify(slug))
    await state.set_state(AdminCrudStates.waiting_product_description)
    await message.answer("Введите описание товара или '-' для пустого описания.")


@router.message(AdminCrudStates.waiting_product_description)
async def create_product_description(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    data = await state.get_data()
    category = await session.get(Category, data.get("prefill_category_id", 0))
    if not category or category.is_deleted:
        await state.clear()
        await message.answer("Категория не найдена.")
        return
    description = (message.text or "").strip()
    if description == "-":
        description = ""
    product = Product(
        game_id=category.game_id,
        category_id=category.id,
        slug=data.get("product_slug", _slugify(data.get("product_title", "product"))),
        title=data.get("product_title", "Новый товар"),
        description=description or None,
        image_id=None,
        fulfillment_type=FulfillmentType.ADMIN_PROCESSED,
        requires_player_id=False,
        requires_nickname=False,
        requires_region=False,
        requires_manual_review=False,
        requires_screenshot=False,
        extra_fields_schema_json={},
        is_active=True,
        is_featured=False,
        sort_order=100,
        is_deleted=False,
    )
    session.add(product)
    await session.flush()
    await state.clear()
    await message.answer(f"✅ Товар создан: <b>{product.title}</b>", parse_mode="HTML")


@router.message(AdminCrudStates.waiting_product_edit_title)
async def edit_product_title(message: Message, session: AsyncSession, state: FSMContext, admin: Admin | None = None) -> None:
    if not _has_access(message.from_user.id, admin):
        await message.answer("⛔ Нет доступа.")
        return
    data = await state.get_data()
    product = await session.get(Product, data.get("product_id", 0))
    if not product:
        await state.clear()
        await message.answer("Товар не найден.")
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым.")
        return
    product.title = title
    await session.flush()
    await state.clear()
    await message.answer(f"✅ Название товара обновлено: <b>{product.title}</b>", parse_mode="HTML")
