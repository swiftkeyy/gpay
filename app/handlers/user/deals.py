from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.deal import DealService
from app.services.seller import SellerService
from app.states.user import DealStates
from app.keyboards.user import get_deal_kb, get_deals_list_kb, get_deal_chat_kb

router = Router(name="deals")


@router.message(Command("deals"))
async def deals_list_cmd(message: Message, session: AsyncSession):
    """List user deals"""
    deal_service = DealService(session)
    
    # Get deals as buyer
    buyer_deals = await deal_service.deal_repo.get_user_deals(
        user_id=message.from_user.id,
        as_buyer=True,
        limit=20
    )
    
    # Check if user is seller
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(message.from_user.id)
    seller_deals = []
    if seller:
        seller_deals = await deal_service.deal_repo.get_seller_deals(
            seller_id=seller.id,
            limit=20
        )
    
    if not buyer_deals and not seller_deals:
        await message.answer(
            "У вас пока нет сделок.\n\n"
            "Сделки создаются автоматически при покупке товаров."
        )
        return
    
    text = "📋 <b>Ваши сделки</b>\n\n"
    
    if buyer_deals:
        text += "🛒 <b>Покупки:</b>\n"
        for deal in buyer_deals[:5]:
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
            text += f"{emoji} Заказ #{deal.order_id} - {deal.amount} ₽\n"
        text += "\n"
    
    if seller_deals:
        text += "💼 <b>Продажи:</b>\n"
        for deal in seller_deals[:5]:
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
            text += f"{emoji} Заказ #{deal.order_id} - {deal.amount} ₽\n"
    
    await message.answer(
        text,
        reply_markup=get_deals_list_kb(buyer_deals, seller_deals)
    )


@router.callback_query(F.data.startswith("deal:"))
async def deal_details_callback(callback: CallbackQuery, session: AsyncSession):
    """Show deal details"""
    deal_id = int(callback.data.split(":")[1])
    
    deal_service = DealService(session)
    deal = await deal_service.deal_repo.get_by_id_with_relations(deal_id)
    
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    
    # Check if user is participant
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(callback.from_user.id)
    
    is_buyer = deal.buyer_id == callback.from_user.id
    is_seller = seller and deal.seller_id == seller.id
    
    if not is_buyer and not is_seller:
        await callback.answer("У вас нет доступа к этой сделке", show_alert=True)
        return
    
    status_text = {
        "created": "Создана",
        "paid": "Оплачена",
        "in_progress": "В процессе",
        "waiting_confirmation": "Ожидает подтверждения",
        "completed": "Завершена",
        "canceled": "Отменена",
        "dispute": "Спор",
        "refunded": "Возврат"
    }
    
    role = "Покупатель" if is_buyer else "Продавец"
    counterparty = deal.seller.shop_name if is_buyer else deal.buyer.first_name or "Покупатель"
    
    text = (
        f"📋 <b>Сделка #{deal.id}</b>\n\n"
        f"👤 Вы: {role}\n"
        f"👥 {counterparty}\n\n"
        f"💰 Сумма: {deal.amount} ₽\n"
        f"📦 Товар: {deal.lot.title}\n"
        f"📊 Статус: {status_text.get(deal.status.value, deal.status.value)}\n"
        f"📅 Создана: {deal.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    )
    
    if deal.completed_at:
        text += f"✅ Завершена: {deal.completed_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    # Get unread messages count
    unread_count = await deal_service.deal_repo.get_unread_count(deal_id, callback.from_user.id)
    if unread_count > 0:
        text += f"\n💬 Непрочитанных сообщений: {unread_count}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_deal_kb(deal_id, deal.status.value, is_buyer)
    )


@router.callback_query(F.data.startswith("deal_chat:"))
async def deal_chat_callback(callback: CallbackQuery, session: AsyncSession):
    """Open deal chat"""
    deal_id = int(callback.data.split(":")[1])
    
    deal_service = DealService(session)
    deal = await deal_service.deal_repo.get_by_id_with_relations(deal_id)
    
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    
    # Mark messages as read
    await deal_service.mark_messages_read(deal_id, callback.from_user.id)
    await session.commit()
    
    # Get messages
    messages = await deal_service.get_deal_messages(deal_id, limit=20)
    
    text = f"💬 <b>Чат по сделке #{deal.id}</b>\n\n"
    
    if messages:
        for msg in messages[-10:]:  # Last 10 messages
            if msg.is_system:
                text += f"ℹ️ {msg.message_text}\n\n"
            else:
                sender_name = msg.sender.first_name or "Пользователь"
                is_me = msg.sender_id == callback.from_user.id
                prefix = "Вы" if is_me else sender_name
                text += f"<b>{prefix}:</b> {msg.message_text}\n"
                text += f"<i>{msg.created_at.strftime('%H:%M')}</i>\n\n"
    else:
        text += "Сообщений пока нет\n\n"
    
    text += "Напишите сообщение или выберите действие:"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_deal_chat_kb(deal_id)
    )
    
    # Set state to wait for message
    await FSMContext(
        storage=callback.bot.get("storage"),
        key=callback.from_user.id
    ).set_state(DealStates.waiting_message)
    await FSMContext(
        storage=callback.bot.get("storage"),
        key=callback.from_user.id
    ).update_data(deal_id=deal_id)


@router.message(DealStates.waiting_message)
async def process_deal_message(message: Message, state: FSMContext, session: AsyncSession):
    """Process message in deal chat"""
    data = await state.get_data()
    deal_id = data.get("deal_id")
    
    if not deal_id:
        await state.clear()
        return
    
    deal_service = DealService(session)
    
    # Send message
    await deal_service.send_message(
        deal_id=deal_id,
        sender_id=message.from_user.id,
        message_text=message.text
    )
    await session.commit()
    
    await message.answer("✅ Сообщение отправлено")
    await state.clear()


@router.callback_query(F.data.startswith("deal_confirm:"))
async def deal_confirm_callback(callback: CallbackQuery, session: AsyncSession):
    """Buyer confirms receipt"""
    deal_id = int(callback.data.split(":")[1])
    
    deal_service = DealService(session)
    deal = await deal_service.deal_repo.get_by_id_with_relations(deal_id)
    
    if not deal or deal.buyer_id != callback.from_user.id:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    try:
        await deal_service.confirm_by_buyer(deal_id)
        await session.commit()
        
        await callback.answer("✅ Получение подтверждено")
        await callback.message.edit_text(
            "✅ Сделка завершена!\n\n"
            "Спасибо за покупку. Вы можете оставить отзыв о продавце.",
            reply_markup=None
        )
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("deal_dispute:"))
async def deal_dispute_callback(callback: CallbackQuery, session: AsyncSession):
    """Open dispute"""
    deal_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "⚠️ Открытие спора\n\n"
        "Опишите проблему подробно. Администрация рассмотрит ваше обращение:",
        reply_markup=None
    )
    
    await FSMContext(
        storage=callback.bot.get("storage"),
        key=callback.from_user.id
    ).set_state(DealStates.waiting_dispute_reason)
    await FSMContext(
        storage=callback.bot.get("storage"),
        key=callback.from_user.id
    ).update_data(deal_id=deal_id)


@router.message(DealStates.waiting_dispute_reason)
async def process_dispute_reason(message: Message, state: FSMContext, session: AsyncSession):
    """Process dispute reason"""
    data = await state.get_data()
    deal_id = data.get("deal_id")
    
    if not deal_id:
        await state.clear()
        return
    
    deal_service = DealService(session)
    
    try:
        await deal_service.open_dispute(
            deal_id=deal_id,
            initiator_id=message.from_user.id,
            reason=message.text
        )
        await session.commit()
        
        await message.answer(
            "✅ Спор открыт\n\n"
            "Администрация рассмотрит ваше обращение в ближайшее время."
        )
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
    
    await state.clear()


@router.callback_query(F.data.startswith("deal_deliver:"))
async def deal_deliver_callback(callback: CallbackQuery, session: AsyncSession):
    """Seller delivers product (manual delivery)"""
    deal_id = int(callback.data.split(":")[1])
    
    deal_service = DealService(session)
    deal = await deal_service.deal_repo.get_by_id_with_relations(deal_id)
    
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    
    # Check if user is seller
    seller_service = SellerService(session)
    seller = await seller_service.get_seller_by_user_id(callback.from_user.id)
    
    if not seller or deal.seller_id != seller.id:
        await callback.answer("У вас нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📦 Доставка товара\n\n"
        "Отправьте данные для доставки покупателю\n"
        "(например, код активации, данные аккаунта и т.д.):",
        reply_markup=None
    )
    
    await FSMContext(
        storage=callback.bot.get("storage"),
        key=callback.from_user.id
    ).set_state(DealStates.waiting_delivery_data)
    await FSMContext(
        storage=callback.bot.get("storage"),
        key=callback.from_user.id
    ).update_data(deal_id=deal_id)


@router.message(DealStates.waiting_delivery_data)
async def process_delivery_data(message: Message, state: FSMContext, session: AsyncSession):
    """Process delivery data from seller"""
    data = await state.get_data()
    deal_id = data.get("deal_id")
    
    if not deal_id:
        await state.clear()
        return
    
    deal_service = DealService(session)
    
    try:
        await deal_service.deliver_product(
            deal_id=deal_id,
            delivery_data=message.text
        )
        await session.commit()
        
        await message.answer(
            "✅ Товар доставлен покупателю\n\n"
            "Ожидайте подтверждения получения."
        )
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
    
    await state.clear()
