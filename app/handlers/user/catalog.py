from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import categories_kb, games_kb, product_kb, products_kb
from app.repositories.catalog import CategoryRepository, GameRepository, ProductRepository
from app.services.media import MediaService
from app.services.pricing import PricingService
from app.utils.callbacks import NavCb
from app.utils.pagination import get_offset
from app.utils.texts import game_caption, product_caption

router = Router(name='user_catalog')
PAGE_SIZE = 5


@router.callback_query(NavCb.filter(F.target == 'games'))
async def games_list(callback: CallbackQuery, session: AsyncSession) -> None:
    games = await GameRepository(session).list_active()
    await callback.message.edit_text('🎮 <b>Игры</b>', reply_markup=games_kb(games), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'game'))
async def game_view(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession) -> None:
    game = await GameRepository(session).get(callback_data.entity_id)
    if not game or not game.is_active:
        await callback.answer('Игра не найдена.', show_alert=True)
        return
    categories = await CategoryRepository(session).list_by_game(game.id)
    caption = game_caption(game)
    await callback.message.edit_text(caption, reply_markup=categories_kb(game.id, categories), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'game_from_category'))
async def game_from_category(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession) -> None:
    category = await CategoryRepository(session).get(callback_data.entity_id)
    if not category:
        await callback.answer('Категория не найдена.', show_alert=True)
        return
    cb = NavCb(target='game', entity_id=category.game_id)
    await game_view(callback, cb, session)


@router.callback_query(NavCb.filter(F.target == 'category'))
async def category_view(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession) -> None:
    category = await CategoryRepository(session).get(callback_data.entity_id)
    if not category:
        await callback.answer('Категория не найдена.', show_alert=True)
        return
    page = callback_data.page or 1
    repo = ProductRepository(session)
    total = await repo.count_by_category(category.id)
    products = await repo.list_by_category(category.id, limit=PAGE_SIZE, offset=get_offset(page, PAGE_SIZE))
    title = f'🗂 <b>{category.title}</b>\n\nВыберите товар:'
    await callback.message.edit_text(
        title,
        reply_markup=products_kb(category.id, products, page, total, PAGE_SIZE),
        parse_mode='HTML',
    )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'product'))
async def product_view(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession, db_user) -> None:
    product = await ProductRepository(session).get_full(callback_data.entity_id)
    if not product or not product.is_active:
        await callback.answer('Товар не найден.', show_alert=True)
        return
    quote = await PricingService(session).get_product_price(product, user=db_user)
    caption = product_caption(product, quote.final_price, quote.currency_code)
    await callback.message.edit_text(
        caption,
        reply_markup=product_kb(product.id, product.category_id, callback_data.page or 1),
        parse_mode='HTML',
    )
    await callback.answer()
