from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.seller import SellerService
from app.services.lot import LotService
from app.states.user import SellerStates
from app.keyboards.user import get_seller_menu_kb, get_seller_lots_kb, get_lot_actions_kb

router = Router(name="seller")


@router.message(Command("seller"))
async def seller_menu_cmd(message: Message, session: AsyncSession):
    """Seller menu"""
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(message.from_user.id)
    
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
async def process_shop_name(message: Message, state: FSMContext, session: AsyncSession):
    """Process shop name for new seller"""
    shop_name = message.text.strip()
    
    if len(shop_name) < 3:
        await message.answer("Название магазина должно быть не менее 3 символов. Попробуйте еще раз:")
        return
    
    seller_service = SellerService(session)
    seller = await seller_service.create_seller(
        user_id=message.from_user.id,
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
async def my_lots_callback(callback: CallbackQuery, session: AsyncSession):
    """Show seller's lots"""
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(callback.from_user.id)
    
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
async def seller_balance_callback(callback: CallbackQuery, session: AsyncSession):
    """Show seller balance and transactions"""
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(callback.from_user.id)
    
    if not seller:
        await callback.answer("Вы не зарегистрированы как продавец", show_alert=True)
        return
    
    from app.repositories.transactions import TransactionRepository
    transaction_repo = TransactionRepository(session)
    transactions = await transaction_repo.get_user_transactions(
        user_id=callback.from_user.id,
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
async def seller_withdraw_callback(callback: CallbackQuery, session: AsyncSession):
    """Request withdrawal"""
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(callback.from_user.id)
    
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
