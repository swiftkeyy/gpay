from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.keyboards.user import categories_kb, games_kb, product_kb, products_kb
from app.models import Category, Game, Product, User
from app.services.cart import CartService
from app.utils.callbacks import NavCb

router = Router(name="user_catalog")

PRODUCTS_PER_PAGE = 8


async def _resolve_db_user(session: AsyncSession, tg_user) -> User | None:
    if tg_user is None:
        return None

    result = await session.execute(
        select(User).where(User.telegram_id == tg_user.id)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        changed = False
        if user.username != tg_user.username:
            user.username = tg_user.username
            changed = True
        if user.first_name != tg_user.first_name:
            user.first_name = tg_user.first_name
            changed = True
        if user.last_name != tg_user.last_name:
            user.last_name = tg_user.last_name
            changed = True
        if changed:
            await session.flush()
        return user

    user = User(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        is_blocked=False,
        block_reason=None,
        personal_discount_percent=0,
        referral_code=f"REF{tg_user.id}",
    )
    session.add(user)
    await session.flush()
    return user


@router.callback_query(NavCb.filter(F.target == "games"))
async def games_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    result = await session.execute(
        select(Game)
        .where(Game.is_active.is_(True), Game.is_deleted.is_(False))
        .order_by(Game.sort_order.asc(), Game.id.asc())
    )
    games = list(result.scalars().all())

    text = "🎮 <b>Игры</b>\n\nВыберите игру:"
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=games_kb(games),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^game:\d+$"))
async def game_categories(callback: CallbackQuery, session: AsyncSession) -> None:
    game_id = int(callback.data.split(":")[1])

    game = await session.get(Game, game_id)
    if game is None or not game.is_active or game.is_deleted:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    result = await session.execute(
        select(Category)
        .where(
            Category.game_id == game_id,
            Category.is_active.is_(True),
            Category.is_deleted.is_(False),
        )
        .order_by(Category.sort_order.asc(), Category.id.asc())
    )
    categories = list(result.scalars().all())

    text = f"🎮 <b>{game.title}</b>\n\nВыберите категорию:"
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=categories_kb(game_id, categories),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^cat:\d+:\d+$"))
async def category_products(callback: CallbackQuery, session: AsyncSession) -> None:
    _, game_id_raw, category_id_raw = callback.data.split(":")
    game_id = int(game_id_raw)
    category_id = int(category_id_raw)
    await _render_products_page(callback, session, game_id, category_id, page=1)


@router.callback_query(F.data.regexp(r"^prodpage:\d+:\d+:\d+$"))
async def category_products_page(callback: CallbackQuery, session: AsyncSession) -> None:
    _, game_id_raw, category_id_raw, page_raw = callback.data.split(":")
    game_id = int(game_id_raw)
    category_id = int(category_id_raw)
    page = max(int(page_raw), 1)
    await _render_products_page(callback, session, game_id, category_id, page=page)


async def _render_products_page(
    callback: CallbackQuery,
    session: AsyncSession,
    game_id: int,
    category_id: int,
    *,
    page: int,
) -> None:
    category = await session.get(Category, category_id)
    if category is None or not category.is_active or category.is_deleted:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    result = await session.execute(
        select(Product)
        .where(
            Product.game_id == game_id,
            Product.category_id == category_id,
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
        .order_by(Product.sort_order.asc(), Product.id.asc())
    )
    all_products = list(result.scalars().all())

    start = (page - 1) * PRODUCTS_PER_PAGE
    end = start + PRODUCTS_PER_PAGE
    page_products = all_products[start:end]

    has_prev = page > 1
    has_next = end < len(all_products)

    text = f"🛍 <b>{category.title}</b>\n\nВыберите товар:"
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=products_kb(
                game_id,
                category_id,
                page_products,
                page=page,
                has_prev=has_prev,
                has_next=has_next,
            ),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^prod:\d+$"))
async def product_view(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split(":")[1])

    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.active_price),
            selectinload(Product.category),
            selectinload(Product.game),
        )
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if product is None or not product.is_active or product.is_deleted:
        await callback.answer("Товар не найден", show_alert=True)
        return

    price_text = "Цена уточняется"
    if product.active_price is not None:
        price_text = f"{product.active_price.base_price} {product.active_price.currency_code}"

    category_title = product.category.title if product.category else "Без категории"
    game_title = product.game.title if product.game else "Без игры"

    text = (
        f"🛍 <b>{product.title}</b>\n\n"
        f"🎮 Игра: <b>{game_title}</b>\n"
        f"🗂 Категория: <b>{category_title}</b>\n"
        f"💸 Цена: <b>{price_text}</b>\n\n"
        f"{product.description or 'Описание отсутствует.'}"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=product_kb(product.id),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^buy:(add|now):\d+$"))
async def buy_product(callback: CallbackQuery, session: AsyncSession) -> None:
    _, action, product_id_raw = callback.data.split(":")
    product_id = int(product_id_raw)

    product = await session.get(Product, product_id)
    if product is None or not product.is_active or product.is_deleted:
        await callback.answer("Товар недоступен", show_alert=True)
        return

    db_user = await _resolve_db_user(session, callback.from_user)
    if db_user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    cart_service = CartService(session)
    await cart_service.add_item(db_user, product_id, quantity=1)
    await session.commit()

    if action == "now":
        if callback.message:
            await callback.message.edit_text(
                "✅ Товар добавлен в корзину.\n\nПереходим к оформлению заказа.",
                parse_mode="HTML",
            )
        callback.data = NavCb(target="checkout").pack()
        await callback.answer()
        return

    await callback.answer("Товар добавлен в корзину")
