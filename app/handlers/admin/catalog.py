from __future__ import annotations

from decimal import Decimal
import secrets

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import (
    categories_admin_kb,
    game_actions_kb,
    games_admin_kb,
    product_actions_kb,
    products_admin_kb,
)
from app.keyboards.common import confirm_keyboard
from app.models import Category, Game, Price, Product
from app.models.enums import AuditAction, EntityType, FulfillmentType
from app.repositories.catalog import CategoryRepository, GameRepository, ProductRepository
from app.services.audit import AuditService
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb, ConfirmCb, NavCb
from app.utils.validators import ValidationError, validate_non_empty, validate_price

router = Router(name='admin_catalog')


@router.callback_query(AdminCb.filter(F.section == 'games'), AdminPermissionFilter('games.manage'))
async def admin_games(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext) -> None:
    repo = GameRepository(session)
    if callback_data.action == 'list':
        games = await repo.list(limit=100)
        await callback.message.edit_text('🎮 <b>Игры</b>', reply_markup=games_admin_kb(games), parse_mode='HTML')
    elif callback_data.action == 'create':
        await state.set_state(AdminCatalogStates.waiting_game_title)
        await callback.message.answer('Введите название новой игры сообщением.')
    elif callback_data.action == 'view':
        game = await repo.get(callback_data.entity_id)
        if not game:
            await callback.answer('Игра не найдена.', show_alert=True)
            return
        text = f'🎮 <b>{game.title}</b>\n\nSlug: <code>{game.slug}</code>\nАктивна: {game.is_active}'
        await callback.message.edit_text(text, reply_markup=game_actions_kb(game.id, game.is_active), parse_mode='HTML')
    elif callback_data.action == 'toggle':
        game = await repo.get(callback_data.entity_id)
        if game:
            old = {'is_active': game.is_active}
            game.is_active = not game.is_active
            await AuditService(session).log(
                action=AuditAction.UPDATE,
                entity_type=EntityType.GAME,
                entity_id=game.id,
                old_values=old,
                new_values={'is_active': game.is_active},
            )
            await callback.answer('Статус игры обновлён.')
            await admin_games(callback, AdminCb(section='games', action='view', entity_id=game.id), session, state)
            return
    elif callback_data.action == 'delete':
        token = secrets.token_hex(4)
        await state.update_data(confirm_delete_game=token)
        await callback.message.answer('Подтвердите удаление игры.', reply_markup=confirm_keyboard('game_delete', callback_data.entity_id, token, 'admin_home'))
    await callback.answer()


@router.message(AdminCatalogStates.waiting_game_title, AdminPermissionFilter('games.manage'))
async def create_game(message: Message, session: AsyncSession, state: FSMContext) -> None:
    title = validate_non_empty(message.text or '', 'title')
    slug = title.lower().replace(' ', '_').replace('-', '_')[:64]
    game = await GameRepository(session).create(title=title, slug=slug, description='Новое описание игры', is_active=True)
    await AuditService(session).log(
        action=AuditAction.CREATE,
        entity_type=EntityType.GAME,
        entity_id=game.id,
        new_values={'title': game.title, 'slug': game.slug},
    )
    await state.clear()
    await message.answer(f'Игра создана: {game.title}')


@router.callback_query(ConfirmCb.filter(F.action == 'game_delete'), AdminPermissionFilter('games.manage'))
async def confirm_delete_game(callback: CallbackQuery, callback_data: ConfirmCb, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get('confirm_delete_game') != callback_data.token:
        await callback.answer('Подтверждение устарело.', show_alert=True)
        return
    game = await GameRepository(session).get(callback_data.entity_id)
    if not game:
        await callback.answer('Игра не найдена.', show_alert=True)
        return
    game.is_deleted = True
    game.is_active = False
    await AuditService(session).log(action=AuditAction.DELETE, entity_type=EntityType.GAME, entity_id=game.id, old_values={'title': game.title})
    await state.clear()
    await callback.message.edit_text('Игра помечена как удалённая.')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'categories'), AdminPermissionFilter('categories.manage'))
async def admin_categories(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession) -> None:
    categories = await CategoryRepository(session).list(limit=200)
    await callback.message.edit_text('🗂 <b>Категории</b>', reply_markup=categories_admin_kb(categories), parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'products'), AdminPermissionFilter('products.manage'))
async def admin_products(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession) -> None:
    repo = ProductRepository(session)
    if callback_data.action == 'list':
        products = await repo.list(limit=200)
        await callback.message.edit_text('🛍 <b>Товары</b>', reply_markup=products_admin_kb(products), parse_mode='HTML')
    elif callback_data.action == 'view':
        product = await repo.get_full(callback_data.entity_id)
        if not product:
            await callback.answer('Товар не найден.', show_alert=True)
            return
        text = (
            f'🛍 <b>{product.title}</b>\n'
            f'Slug: <code>{product.slug}</code>\n'
            f'Выдача: <code>{product.fulfillment_type}</code>\n'
            f'Активен: {product.is_active}'
        )
        await callback.message.edit_text(text, reply_markup=product_actions_kb(product.id), parse_mode='HTML')
    await callback.answer()
