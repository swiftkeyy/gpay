from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import categories_kb, games_kb, product_kb, products_kb
from app.models import Category, Game, Product, User
from app.services.cart import CartService
from app.services.pricing import PricingService
from app.utils.callbacks import NavCb

router = Router(name="user_catalog")


def _format_money(value: Decimal | int | float | str) -> str:
    return f"{Decimal(value):.2f}"


async def _resolve_db_user(
    session: AsyncSession,
    db_user: User | None,
    tg_user,
) -> User | None:
    if db_user is not None and getattr(db_user, "id", None) is not None:
        return db_user

    if tg_user is None:
        return None

    result = await session.execute(select(User).where(User.telegram_id == tg_user.id))
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
    db_user = await _resolve_db_user(session, db_user, callback.from_user)
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
    await session.commit()

    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Открыть корзину", callback_data=NavCb(target="cart").pack())
    builder.button(text="💳 Оформить заказ", callback_data=NavCb(target="checkout").pack())
    builder.button(text="🔙 Назад к товарам", callback_data=f"cat:{product.game_id}:{product.category_id}")
    builder.adjust(1)

    if callback.message:
        await callback.message.edit_text(
            "✅ <b>Товар добавлен в корзину</b>\n\nТеперь можешь открыть корзину или сразу перейти к оформлению.",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:now:"))
async def buy_now(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    db_user = await _resolve_db_user(session, db_user, callback.from_user)
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
    await session.commit()

    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перейти к оплате", callback_data=NavCb(target="checkout").pack())
    builder.button(text="🛒 Открыть корзину", callback_data=NavCb(target="cart").pack())
    builder.adjust(1)

    if callback.message:
        await callback.message.edit_text(
            "✅ <b>Товар добавлен в корзину</b>\n\nТеперь создадим заказ и выберем оплату.",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    await callback.answer()



@router.callback_query(F.data.startswith("prod_lots:"))
async def show_product_lots(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show available lots for product"""
    try:
        _, product_id_raw = callback.data.split(":")
        product_id = int(product_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный товар", show_alert=True)
        return
    
    from app.services.lot import LotService
    from app.keyboards.user import get_lots_by_product_kb
    
    lot_service = LotService(session)
    lots = await lot_service.get_lots_by_product(product_id, limit=20, sort_by="price")
    
    if not lots:
        await callback.answer("Нет доступных предложений", show_alert=True)
        return
    
    # Get product info
    product_result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = product_result.scalar_one_or_none()
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    text = f"🛍 <b>{product.title}</b>\n\n"
    text += f"Доступно предложений: {len(lots)}\n\n"
    text += "Выберите продавца:\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_lots_by_product_kb(product_id, lots),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lot:buy:"))
async def buy_lot(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    """Buy specific lot"""
    try:
        _, _, lot_id_raw = callback.data.split(":")
        lot_id = int(lot_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный лот", show_alert=True)
        return
    
    user = await _resolve_db_user(session, db_user, callback.from_user)
    if user is None:
        await callback.answer("Ошибка пользователя", show_alert=True)
        return
    
    from app.services.lot import LotService
    from app.keyboards.user import get_lot_detail_kb
    
    lot_service = LotService(session)
    lot = await lot_service.get_lot_with_details(lot_id)
    
    if not lot:
        await callback.answer("Лот не найден", show_alert=True)
        return
    
    if lot.stock_count == 0:
        await callback.answer("Товар закончился", show_alert=True)
        return
    
    delivery_type_text = {
        "auto": "⚡ Автоматическая",
        "manual": "👤 Ручная",
        "coordinates": "📍 По координатам"
    }
    
    text = (
        f"🛍 <b>{lot.title}</b>\n\n"
        f"💰 Цена: {lot.price} ₽\n"
        f"🏪 Продавец: {lot.seller.shop_name}\n"
        f"⭐ Рейтинг: {float(lot.seller.rating):.1f} ({lot.seller.total_reviews} отзывов)\n"
        f"📦 В наличии: {lot.stock_count} шт.\n"
        f"🚚 Доставка: {delivery_type_text.get(lot.delivery_type.value, lot.delivery_type.value)}\n"
    )
    
    if lot.delivery_time_minutes:
        text += f"⏱ Время доставки: ~{lot.delivery_time_minutes} мин.\n"
    
    if lot.description:
        text += f"\n📝 Описание:\n{lot.description}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_lot_detail_kb(lot_id, lot.seller_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lot:purchase:"))
async def purchase_lot(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    """Purchase lot - create order and deal"""
    try:
        _, _, lot_id_raw = callback.data.split(":")
        lot_id = int(lot_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный лот", show_alert=True)
        return
    
    user = await _resolve_db_user(session, db_user, callback.from_user)
    if user is None:
        await callback.answer("Ошибка пользователя", show_alert=True)
        return
    
    from app.services.lot import LotService
    from app.services.orders import OrderService
    from app.services.deal import DealService
    from app.models.enums import OrderStatus
    import secrets
    
    lot_service = LotService(session)
    lot = await lot_service.get_lot_with_details(lot_id)
    
    if not lot or lot.stock_count == 0:
        await callback.answer("Товар недоступен", show_alert=True)
        return
    
    # Check balance
    if user.balance < lot.price:
        await callback.answer(
            f"Недостаточно средств. Ваш баланс: {user.balance} ₽, нужно: {lot.price} ₽",
            show_alert=True
        )
        return
    
    try:
        # Create order
        from app.models.entities import Order, OrderItem
        order = Order(
            order_number=f"ORD-{secrets.token_hex(4).upper()}",
            user_id=user.id,
            status=OrderStatus.NEW,
            subtotal_amount=lot.price,
            total_amount=lot.price,
            fulfillment_type=lot.product.fulfillment_type
        )
        session.add(order)
        await session.flush()
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=lot.product_id,
            title_snapshot=lot.title,
            quantity=1,
            unit_price=lot.price,
            total_price=lot.price,
            fulfillment_type=lot.product.fulfillment_type
        )
        session.add(order_item)
        await session.flush()
        
        # Create deal
        deal_service = DealService(session)
        deal = await deal_service.create_deal(
            order_id=order.id,
            buyer_id=user.id,
            seller_id=lot.seller_id,
            lot_id=lot_id,
            amount=lot.price
        )
        
        # Deduct from balance
        from app.repositories.transactions import TransactionRepository
        from app.models.enums import TransactionType
        transaction_repo = TransactionRepository(session)
        await transaction_repo.create_transaction(
            user_id=user.id,
            transaction_type=TransactionType.PURCHASE,
            amount=lot.price,
            description=f"Покупка: {lot.title}",
            reference_type="deal",
            reference_id=deal.id
        )
        
        # Mark as paid and process
        await deal_service.mark_as_paid(deal.id)
        
        await session.commit()
        
        await callback.message.edit_text(
            f"✅ Заказ #{order.order_number} создан!\n\n"
            f"Сделка #{deal.id} в процессе.\n"
            f"Используйте /deals для отслеживания.",
            parse_mode="HTML"
        )
        await callback.answer("Покупка успешна!")
        
    except Exception as e:
        await session.rollback()
        await callback.answer(f"Ошибка при покупке: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("lot:favorite:"))
async def toggle_favorite_lot(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    """Add/remove lot from favorites"""
    try:
        _, _, lot_id_raw = callback.data.split(":")
        lot_id = int(lot_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный лот", show_alert=True)
        return
    
    user = await _resolve_db_user(session, db_user, callback.from_user)
    if user is None:
        await callback.answer("Ошибка пользователя", show_alert=True)
        return
    
    from app.models.entities import Favorite
    
    # Check if already in favorites
    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.lot_id == lot_id
        )
    )
    favorite = result.scalar_one_or_none()
    
    if favorite:
        await session.delete(favorite)
        await session.commit()
        await callback.answer("❌ Удалено из избранного")
    else:
        favorite = Favorite(user_id=user.id, lot_id=lot_id)
        session.add(favorite)
        await session.commit()
        await callback.answer("❤️ Добавлено в избранное")


@router.callback_query(F.data.startswith("seller:view:"))
async def view_seller_profile(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """View seller profile"""
    try:
        _, _, seller_id_raw = callback.data.split(":")
        seller_id = int(seller_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный продавец", show_alert=True)
        return
    
    from app.services.seller import SellerService
    
    seller_service = SellerService(session)
    seller = await seller_service.seller_repo.get_by_id(seller_id)
    
    if not seller:
        await callback.answer("Продавец не найден", show_alert=True)
        return
    
    stats = await seller_service.get_seller_stats(seller_id)
    
    text = (
        f"🏪 <b>{seller.shop_name}</b>\n\n"
        f"⭐ Рейтинг: {stats['rating']:.1f} ({stats['total_reviews']} отзывов)\n"
        f"📊 Продаж: {stats['total_sales']}\n"
    )
    
    if seller.is_verified:
        text += "✅ Верифицирован\n"
    
    if seller.description:
        text += f"\n📝 О продавце:\n{seller.description}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Товары продавца", callback_data=f"seller:lots:{seller_id}")
    builder.button(text="⭐ Отзывы", callback_data=f"seller:reviews:{seller_id}")
    builder.button(text="🔙 Назад", callback_data=NavCb(target="games").pack())
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
