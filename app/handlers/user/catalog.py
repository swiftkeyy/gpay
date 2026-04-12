from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import categories_kb, games_kb, product_kb, products_kb
from app.models import Category, Game, Price, Product, User
from app.services.cart import CartService
from app.services.pricing import PricingService
from app.utils.callbacks import NavCb

router = Router(name="user_catalog")


def _format_money(value: Decimal | int | float | str) -> str:
    return f"{Decimal(value):.2f}"


async def _get_active_price(session: AsyncSession, product_id: int) -> Price | None:
    result = await session.execute(
        select(Price)
        .where(
            Price.product_id == product_id,
            Price.is_active.is_(True),
        )
        .order_by(Price.id.desc())
    )
    return result.scalars().first()


@router.callback_query(NavCb.filter(F.target == "games"))
async def open_games(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    result = await session.execute(
        select(Game)
        .where(
            Game.is_active.is_(True),
            Game.is_deleted.is_(False),
        )
        .order_by(Game.sort_order.asc(), Game.id.asc())
    )
    games = result.scalars().all()

    text = "🎮 <b>Игры</b>\n\nВыберите игру:"
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=games_kb(list(games)),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("game:"))
async def open_game_categories(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    try:
        _, game_id_raw = callback.data.split(":")
        game_id = int(game_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректная игра", show_alert=True)
        return

    game_result = await session.execute(
        select(Game).where(
            Game.id == game_id,
            Game.is_active.is_(True),
            Game.is_deleted.is_(False),
        )
    )
    game = game_result.scalar_one_or_none()
    if game is None:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    categories_result = await session.execute(
        select(Category)
        .where(
            Category.game_id == game.id,
            Category.is_active.is_(True),
            Category.is_deleted.is_(False),
        )
        .order_by(Category.sort_order.asc(), Category.id.asc())
    )
    categories = categories_result.scalars().all()

    text = f"🎮 <b>{game.title}</b>\n\nВыберите категорию:"
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=categories_kb(game.id, list(categories)),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def open_category_products(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    try:
        _, game_id_raw, category_id_raw = callback.data.split(":")
        game_id = int(game_id_raw)
        category_id = int(category_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректная категория", show_alert=True)
        return

    category_result = await session.execute(
        select(Category).where(
            Category.id == category_id,
            Category.game_id == game_id,
            Category.is_active.is_(True),
            Category.is_deleted.is_(False),
        )
    )
    category = category_result.scalar_one_or_none()
    if category is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    products_result = await session.execute(
        select(Product)
        .where(
            Product.game_id == game_id,
            Product.category_id == category_id,
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
        .order_by(Product.sort_order.asc(), Product.id.asc())
    )
    products = products_result.scalars().all()

    text = f"🗂 <b>{category.title}</b>\n\nВыберите товар:"
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=products_kb(
                game_id=game_id,
                category_id=category_id,
                products=list(products),
                page=1,
                has_prev=False,
                has_next=False,
            ),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("prod:"))
async def product_view(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    try:
        _, product_id_raw = callback.data.split(":")
        product_id = int(product_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный товар", show_alert=True)
        return

    product_result = await session.execute(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
    )
    product = product_result.scalar_one_or_none()
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    pricing_service = PricingService(session)
    quote = await pricing_service.get_product_price(product, user=db_user)

    text = (
        f"🛍 <b>{product.title}</b>\n\n"
        f"{product.description or 'Описание отсутствует.'}\n\n"
        f"💸 Цена: <b>{_format_money(quote.final_price)} {quote.currency_code}</b>"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=product_kb(product.id),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:add:"))
async def add_to_cart(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    tg_user = callback.from_user

    if db_user is None and tg_user is not None:
        user_result = await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
        db_user = user_result.scalar_one_or_none()

    if db_user is None or getattr(db_user, "id", None) is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    try:
        _, _, product_id_raw = callback.data.split(":")
        product_id = int(product_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный товар", show_alert=True)
        return

    product_result = await session.execute(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
    )
    product = product_result.scalar_one_or_none()
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    cart_service = CartService(session)
    await cart_service.add_item(db_user.id, product, quantity=1)

    await callback.answer("Товар добавлен в корзину")


@router.callback_query(F.data.startswith("buy:now:"))
async def buy_now(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    tg_user = callback.from_user

    if db_user is None and tg_user is not None:
        user_result = await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
        db_user = user_result.scalar_one_or_none()

        if db_user is None:
            db_user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                is_blocked=False,
                block_reason=None,
                personal_discount_percent=0,
                referral_code=f"REF{tg_user.id}",
            )
            session.add(db_user)
            await session.flush()
            await session.commit()

            user_result = await session.execute(
                select(User).where(User.telegram_id == tg_user.id)
            )
            db_user = user_result.scalar_one_or_none()

    if db_user is None or getattr(db_user, "id", None) is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    try:
        _, _, product_id_raw = callback.data.split(":")
        product_id = int(product_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный товар", show_alert=True)
        return

    product_result = await session.execute(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
    )
    product = product_result.scalar_one_or_none()
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    cart_service = CartService(session)
    await cart_service.add_item(db_user.id, product, quantity=1)

    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перейти к оплате", callback_data=NavCb(target="checkout").pack())
    builder.button(text="🛒 В корзину", callback_data=NavCb(target="cart").pack())
    builder.adjust(1)

    if callback.message:
        await callback.message.edit_text(
            "✅ Товар добавлен в корзину.\n\nТеперь создадим заказ и выберем оплату.",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    await callback.answer("Переходим к оплате")
