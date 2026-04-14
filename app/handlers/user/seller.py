from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.seller import SellerService
from app.services.lot import LotService
from app.states.user import SellerStates
from app.keyboards.user import get_seller_menu_kb, get_seller_lots_kb, get_lot_actions_kb
from app.models.enums import LotDeliveryType

router = Router(name="seller")


@router.message(Command("seller"))
async def seller_menu_cmd(message: Message, session: AsyncSession, db_user):
    """Seller menu"""
    if not db_user:
        await message.answer("Ошибка: пользователь не найден")
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(db_user.id)
    
    if not seller:
        await message.answer(
            "🏪 Вы еще не зарегистрированы как продавец.\n\n"
            "Хотите начать продавать товары? Отправьте название вашего магазина:",
            reply_markup=None
        )
        await FSMContext(storage=message.bot.get("storage"), key=message.from_user.id).set_state(SellerStates.waiting_shop_name)
        return
    
    stats = await seller_service.get_seller_stats(seller.id)
    
    text = (
        f"🏪 <b>{seller.shop_name}</b>\n\n"
        f"📊 Статистика:\n"
        f"• Продаж: {stats['total_sales']}\n"
        f"• Рейтинг: {stats['rating']:.2f} ⭐ ({stats['total_reviews']} отзывов)\n"
        f"• Баланс: {stats['balance']:.2f} ₽\n"
        f"• Статус: {stats['status']}\n"
    )
    
    if stats['is_verified']:
        text += "✅ Верифицирован\n"
    
    await message.answer(text, reply_markup=get_seller_menu_kb())


@router.message(SellerStates.waiting_shop_name)
async def process_shop_name(message: Message, state: FSMContext, session: AsyncSession, db_user):
    """Process shop name for new seller"""
    if not db_user:
        await message.answer("Ошибка: пользователь не найден")
        return
    
    shop_name = message.text.strip()
    
    if len(shop_name) < 3:
        await message.answer("Название магазина должно быть не менее 3 символов. Попробуйте еще раз:")
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.create_seller(
        user_id=db_user.id,
        shop_name=shop_name
    )
    await session.commit()
    
    await state.clear()
    await message.answer(
        f"✅ Магазин <b>{shop_name}</b> создан!\n\n"
        "Ваша заявка отправлена на модерацию. После проверки вы сможете добавлять товары.\n\n"
        "Используйте /seller для управления магазином.",
        reply_markup=get_seller_menu_kb()
    )


@router.callback_query(F.data == "seller:my_lots")
async def my_lots_callback(callback: CallbackQuery, session: AsyncSession, db_user):
    """Show seller's lots"""
    if not db_user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(db_user.id)
    
    if not seller:
        await callback.answer("Вы не зарегистрированы как продавец", show_alert=True)
        return
    
    lot_service = LotService(session)
    lots = await lot_service.get_seller_lots(seller.id)
    
    if not lots:
        await callback.message.edit_text(
            "У вас пока нет лотов.\n\nДобавьте первый лот через меню.",
            reply_markup=get_seller_menu_kb()
        )
        return
    
    await callback.message.edit_text(
        f"📦 Ваши лоты ({len(lots)}):",
        reply_markup=get_seller_lots_kb(lots)
    )


@router.callback_query(F.data.startswith("seller:lot:"))
async def lot_details_callback(callback: CallbackQuery, session: AsyncSession):
    """Show lot details"""
    lot_id = int(callback.data.split(":")[2])
    
    lot_service = LotService(session)
    lot = await lot_service.get_lot_with_details(lot_id)
    
    if not lot:
        await callback.answer("Лот не найден", show_alert=True)
        return
    
    status_emoji = {
        "draft": "📝",
        "active": "✅",
        "paused": "⏸",
        "out_of_stock": "❌",
        "deleted": "🗑"
    }
    
    text = (
        f"{status_emoji.get(lot.status.value, '📦')} <b>{lot.title}</b>\n\n"
        f"💰 Цена: {lot.price} ₽\n"
        f"📦 В наличии: {lot.stock_count}\n"
        f"🔒 Зарезервировано: {lot.reserved_count}\n"
        f"✅ Продано: {lot.sold_count}\n"
        f"📊 Статус: {lot.status.value}\n"
    )
    
    if lot.description:
        text += f"\n📝 Описание:\n{lot.description}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_lot_actions_kb(lot_id, lot.status.value)
    )


@router.callback_query(F.data.startswith("seller:lot_action:"))
async def lot_action_callback(callback: CallbackQuery, session: AsyncSession):
    """Handle lot actions"""
    parts = callback.data.split(":")
    action = parts[2]
    lot_id = int(parts[3])
    
    lot_service = LotService(session)
    
    if action == "activate":
        success = await lot_service.activate_lot(lot_id)
        if success:
            await session.commit()
            await callback.answer("✅ Лот активирован")
        else:
            await callback.answer("❌ Не удалось активировать лот", show_alert=True)
    
    elif action == "pause":
        success = await lot_service.pause_lot(lot_id)
        if success:
            await session.commit()
            await callback.answer("⏸ Лот приостановлен")
        else:
            await callback.answer("❌ Ошибка", show_alert=True)
    
    elif action == "delete":
        success = await lot_service.delete_lot(lot_id)
        if success:
            await session.commit()
            await callback.answer("🗑 Лот удален")
            await callback.message.edit_text(
                "Лот удален",
                reply_markup=get_seller_menu_kb()
            )
            return
        else:
            await callback.answer("❌ Ошибка", show_alert=True)
    
    # Refresh lot details
    lot = await lot_service.get_lot_with_details(lot_id)
    if lot:
        status_emoji = {
            "draft": "📝",
            "active": "✅",
            "paused": "⏸",
            "out_of_stock": "❌"
        }
        
        text = (
            f"{status_emoji.get(lot.status.value, '📦')} <b>{lot.title}</b>\n\n"
            f"💰 Цена: {lot.price} ₽\n"
            f"📦 В наличии: {lot.stock_count}\n"
            f"📊 Статус: {lot.status.value}\n"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_lot_actions_kb(lot_id, lot.status.value)
        )


@router.callback_query(F.data == "seller:balance")
async def seller_balance_callback(callback: CallbackQuery, session: AsyncSession, db_user):
    """Show seller balance and transactions"""
    if not db_user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(db_user.id)
    
    if not seller:
        await callback.answer("Вы не зарегистрированы как продавец", show_alert=True)
        return
    
    from app.repositories.transactions import TransactionRepository
    transaction_repo = TransactionRepository(session)
    transactions = await transaction_repo.get_user_transactions(
        user_id=db_user.id,
        limit=10
    )
    
    text = f"💰 <b>Баланс: {seller.balance} ₽</b>\n\n"
    
    if transactions:
        text += "📊 Последние транзакции:\n\n"
        for t in transactions:
            emoji = "+" if t.transaction_type.value in ["deposit", "sale", "refund", "bonus"] else "-"
            text += f"{emoji}{t.amount} ₽ - {t.description or t.transaction_type.value}\n"
    else:
        text += "Транзакций пока нет"
    
    await callback.message.edit_text(text, reply_markup=get_seller_menu_kb())


@router.callback_query(F.data == "seller:withdraw")
async def seller_withdraw_callback(callback: CallbackQuery, session: AsyncSession, db_user):
    """Request withdrawal"""
    if not db_user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(db_user.id)
    
    if not seller:
        await callback.answer("Вы не зарегистрированы как продавец", show_alert=True)
        return
    
    if seller.balance < 100:
        await callback.answer("Минимальная сумма для вывода: 100 ₽", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"💰 Доступно для вывода: {seller.balance} ₽\n\n"
        "Введите сумму для вывода:",
        reply_markup=None
    )
    
    await FSMContext(
        storage=callback.bot.get("storage"),
        key=callback.from_user.id
    ).set_state(SellerStates.waiting_withdrawal_amount)


@router.callback_query(F.data == "seller:add_lot")
async def add_lot_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext, db_user):
    """Start adding new lot"""
    if not db_user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(db_user.id)
    
    if not seller:
        await callback.answer("Вы не зарегистрированы как продавец", show_alert=True)
        return
    
    if seller.status.value != "active":
        await callback.answer("Ваш магазин еще не активирован. Дождитесь модерации.", show_alert=True)
        return
    
    # Get list of products to choose from
    from app.repositories.catalog import ProductRepository
    product_repo = ProductRepository(session)
    products = await product_repo.list_active(limit=50)
    
    if not products:
        await callback.answer("В каталоге пока нет товаров", show_alert=True)
        return
    
    # Show products list
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    for product in products[:20]:  # Show first 20
        builder.button(
            text=f"{product.title}",
            callback_data=f"seller:select_product:{product.id}"
        )
    
    builder.adjust(1)
    builder.button(text="🔙 Назад", callback_data="seller:my_lots")
    
    await callback.message.edit_text(
        "➕ <b>Добавление нового лота</b>\n\n"
        "Выберите товар из каталога:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("seller:select_product:"))
async def select_product_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Product selected, ask for lot details"""
    product_id = int(callback.data.split(":")[2])
    
    from app.repositories.catalog import ProductRepository
    product_repo = ProductRepository(session)
    product = await product_repo.get_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    await state.update_data(product_id=product_id, product_title=product.title)
    
    await callback.message.edit_text(
        f"➕ <b>Добавление лота</b>\n\n"
        f"Товар: {product.title}\n\n"
        f"Отправьте название вашего лота\n"
        f"(например: '{product.title} - быстрая доставка'):",
        reply_markup=None,
        parse_mode="HTML"
    )
    
    await state.set_state(SellerStates.waiting_lot_title)
    await callback.answer()


@router.message(SellerStates.waiting_lot_title)
async def process_lot_title(message: Message, state: FSMContext, session: AsyncSession):
    """Process lot title"""
    title = message.text.strip()
    
    if len(title) < 3:
        await message.answer("Название должно быть не менее 3 символов. Попробуйте еще раз:")
        return
    
    if len(title) > 255:
        await message.answer("Название слишком длинное (максимум 255 символов). Попробуйте еще раз:")
        return
    
    await state.update_data(title=title)
    await message.answer(
        "Отправьте описание товара\n"
        "(или отправьте /skip чтобы пропустить):"
    )
    await state.set_state(SellerStates.waiting_lot_description)


@router.message(SellerStates.waiting_lot_description)
async def process_lot_description(message: Message, state: FSMContext):
    """Process lot description"""
    description = None if message.text == "/skip" else message.text.strip()
    
    if description and len(description) > 2000:
        await message.answer("Описание слишком длинное (максимум 2000 символов). Попробуйте еще раз:")
        return
    
    await state.update_data(description=description)
    await message.answer("Отправьте цену товара в рублях (например: 100 или 99.99):")
    await state.set_state(SellerStates.waiting_lot_price)


@router.message(SellerStates.waiting_lot_price)
async def process_lot_price(message: Message, state: FSMContext, session: AsyncSession, db_user):
    """Process lot price and create lot"""
    if not db_user:
        await message.answer("Ошибка: пользователь не найден")
        return
    
    try:
        from decimal import Decimal
        price = Decimal(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError("Price must be positive")
        if price > 999999:
            raise ValueError("Price too high")
    except:
        await message.answer("Неверная цена. Введите число больше 0 (например: 100 или 99.99):")
        return
    
    data = await state.get_data()
    product_id = data.get("product_id")
    title = data.get("title")
    description = data.get("description")
    
    # Get seller
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(db_user.id)
    
    if not seller:
        await message.answer("Ошибка: вы не зарегистрированы как продавец")
        await state.clear()
        return
    
    # Create lot
    lot_service = LotService(session)
    lot = await lot_service.create_lot(
        seller_id=seller.id,
        product_id=product_id,
        title=title,
        price=price,
        description=description,
        delivery_type=LotDeliveryType.MANUAL  # Default to manual
    )
    
    await session.commit()
    await state.clear()
    
    await message.answer(
        f"✅ <b>Лот создан!</b>\n\n"
        f"📦 {lot.title}\n"
        f"💰 Цена: {lot.price} ₽\n"
        f"📊 Статус: черновик\n\n"
        f"Лот создан в статусе 'черновик'. "
        f"Активируйте его через меню 'Мои лоты' когда будете готовы к продажам.",
        reply_markup=get_seller_menu_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("seller:lot_action:add_stock:"))
async def add_stock_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Start adding stock items"""
    lot_id = int(callback.data.split(":")[3])
    
    lot_service = LotService(session)
    lot = await lot_service.get_lot_with_details(lot_id)
    
    if not lot:
        await callback.answer("Лот не найден", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📦 <b>Добавление товаров</b>\n\n"
        f"Лот: {lot.title}\n\n"
        f"Отправьте товары для автовыдачи, каждый с новой строки.\n"
        f"Например:\n"
        f"<code>код1:пароль1\n"
        f"код2:пароль2\n"
        f"код3:пароль3</code>\n\n"
        f"Или отправьте /cancel для отмены",
        reply_markup=None,
        parse_mode="HTML"
    )
    
    await state.set_state(SellerStates.waiting_stock_items)
    await state.update_data(lot_id=lot_id)
    await callback.answer()


@router.message(SellerStates.waiting_stock_items)
async def process_stock_items(message: Message, state: FSMContext, session: AsyncSession):
    """Process stock items"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено", reply_markup=get_seller_menu_kb())
        return
    
    data = await state.get_data()
    lot_id = data.get("lot_id")
    
    if not lot_id:
        await state.clear()
        return
    
    # Parse items (one per line)
    items_data = [line.strip() for line in message.text.split("\n") if line.strip()]
    
    if not items_data:
        await message.answer("Не найдено ни одного товара. Попробуйте еще раз:")
        return
    
    if len(items_data) > 1000:
        await message.answer("Слишком много товаров за раз (максимум 1000). Попробуйте еще раз:")
        return
    
    # Add stock items
    lot_service = LotService(session)
    added_count = await lot_service.add_stock_items(lot_id, items_data)
    
    await session.commit()
    await state.clear()
    
    await message.answer(
        f"✅ Добавлено товаров: {added_count}\n\n"
        f"Теперь вы можете активировать лот для продажи.",
        reply_markup=get_seller_menu_kb()
    )


@router.callback_query(F.data == "seller:stats")
async def seller_stats_callback(callback: CallbackQuery, session: AsyncSession, db_user):
    """Show seller statistics"""
    if not db_user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(db_user.id)
    
    if not seller:
        await callback.answer("Вы не зарегистрированы как продавец", show_alert=True)
        return
    
    stats = await seller_service.get_seller_stats(seller.id)
    
    text = (
        f"📊 <b>Статистика магазина</b>\n\n"
        f"🏪 {seller.shop_name}\n"
        f"⭐ Рейтинг: {stats['rating']:.2f} ({stats['total_reviews']} отзывов)\n"
        f"💰 Баланс: {stats['balance']:.2f} ₽\n"
        f"📦 Всего продаж: {stats['total_sales']}\n"
        f"📊 Статус: {stats['status']}\n"
    )
    
    if stats['is_verified']:
        text += "✅ Верифицирован\n"
    
    # Добавим статистику по лотам
    lot_service = LotService(session)
    lots = await lot_service.get_seller_lots(seller.id)
    
    active_lots = sum(1 for lot in lots if lot.status.value == "active")
    total_stock = sum(lot.stock_count for lot in lots)
    
    text += f"\n📦 Активных лотов: {active_lots}\n"
    text += f"📦 Товаров в наличии: {total_stock}\n"
    
    await callback.message.edit_text(text, reply_markup=get_seller_menu_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "seller:sales")
async def seller_sales_callback(callback: CallbackQuery, session: AsyncSession, db_user):
    """Show seller sales"""
    if not db_user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(db_user.id)
    
    if not seller:
        await callback.answer("Вы не зарегистрированы как продавец", show_alert=True)
        return
    
    # Получаем сделки продавца
    from app.repositories.deals import DealRepository
    deal_repo = DealRepository(session)
    deals = await deal_repo.get_seller_deals(seller.id, limit=10)
    
    if not deals:
        await callback.message.edit_text(
            "💼 У вас пока нет продаж",
            reply_markup=get_seller_menu_kb()
        )
        await callback.answer()
        return
    
    text = "💼 <b>Ваши продажи</b>\n\n"
    
    for deal in deals:
        status_emoji = {
            "created": "🆕",
            "paid": "💳",
            "in_progress": "⏳",
            "waiting_confirmation": "⏰",
            "completed": "✅",
            "canceled": "❌",
            "dispute": "⚠️"
        }
        emoji = status_emoji.get(deal.status.value, "📦")
        text += f"{emoji} Заказ #{deal.order_id} - {deal.amount} ₽ ({deal.status.value})\n"
    
    await callback.message.edit_text(text, reply_markup=get_seller_menu_kb(), parse_mode="HTML")
    await callback.answer()
