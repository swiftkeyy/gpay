from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Deal, DealMessage, DealDispute
from app.models.enums import (
    DealStatus,
    TransactionType,
    NotificationType,
    DisputeStatus
)
from app.repositories.deals import DealRepository, DealMessageRepository, DealDisputeRepository
from app.repositories.transactions import TransactionRepository, NotificationRepository
from app.services.seller import SellerService
from app.services.lot import LotService


class DealService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.deal_repo = DealRepository(session)
        self.message_repo = DealMessageRepository(session)
        self.dispute_repo = DealDisputeRepository(session)
        self.transaction_repo = TransactionRepository(session)
        self.notification_repo = NotificationRepository(session)
        self.seller_service = SellerService(session)
        self.lot_service = LotService(session)

    async def create_deal(
        self,
        order_id: int,
        buyer_id: int,
        seller_id: int,
        lot_id: int,
        amount: Decimal
    ) -> Deal:
        """Create new deal"""
        # Calculate commission
        commission = await self.seller_service.calculate_commission(seller_id, amount)
        seller_amount = amount - commission
        
        # Set auto-complete time (3 days from now)
        auto_complete_at = datetime.utcnow() + timedelta(days=3)
        
        deal = Deal(
            order_id=order_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            lot_id=lot_id,
            status=DealStatus.CREATED,
            amount=amount,
            commission_amount=commission,
            seller_amount=seller_amount,
            auto_complete_at=auto_complete_at
        )
        self.session.add(deal)
        await self.session.flush()
        
        # Create system message
        await self.message_repo.create_system_message(
            deal_id=deal.id,
            message_text="Сделка создана. Ожидание оплаты."
        )
        
        return deal

    async def mark_as_paid(self, deal_id: int) -> None:
        """Mark deal as paid and reserve stock if auto-delivery"""
        deal = await self.deal_repo.get_by_id_with_relations(deal_id)
        if not deal:
            raise ValueError("Deal not found")
        
        # Update status
        await self.deal_repo.update_status(deal_id, DealStatus.PAID)
        
        # Reserve stock item if auto-delivery
        from app.models.enums import LotDeliveryType
        if deal.lot.delivery_type == LotDeliveryType.AUTO:
            stock_item = await self.lot_service.reserve_stock_item(
                lot_id=deal.lot_id,
                deal_id=deal_id,
                minutes=60  # 1 hour reservation
            )
            
            if stock_item:
                # Auto-deliver immediately
                await self.deliver_product(deal_id, stock_item.data)
            else:
                # No stock available - refund
                await self.cancel_deal(deal_id, "Товар закончился")
                return
        else:
            # Manual delivery - notify seller
            await self.deal_repo.update_status(deal_id, DealStatus.IN_PROGRESS)
        
        # Create system message
        await self.message_repo.create_system_message(
            deal_id=deal_id,
            message_text="Оплата получена. Продавец приступил к выполнению заказа."
        )
        
        # Notify seller
        await self.notification_repo.create_notification(
            user_id=deal.seller.user_id,
            notification_type=NotificationType.NEW_ORDER,
            title="Новый заказ",
            message=f"Получен новый заказ #{deal.order_id}",
            reference_type="deal",
            reference_id=deal_id
        )
        
        await self.session.flush()

    async def deliver_product(
        self,
        deal_id: int,
        delivery_data: str
    ) -> None:
        """Deliver product to buyer"""
        deal = await self.deal_repo.get_by_id_with_relations(deal_id)
        if not deal:
            raise ValueError("Deal not found")
        
        # Update status
        await self.deal_repo.update_status(deal_id, DealStatus.WAITING_CONFIRMATION)
        
        # Send delivery message
        await self.message_repo.create_system_message(
            deal_id=deal_id,
            message_text=f"Товар доставлен:\n\n{delivery_data}\n\nПожалуйста, подтвердите получение."
        )
        
        # Notify buyer
        await self.notification_repo.create_notification(
            user_id=deal.buyer_id,
            notification_type=NotificationType.ORDER_STATUS,
            title="Товар доставлен",
            message=f"Ваш заказ #{deal.order_id} доставлен",
            reference_type="deal",
            reference_id=deal_id
        )
        
        await self.session.flush()

    async def confirm_by_buyer(self, deal_id: int) -> None:
        """Buyer confirms receipt of product"""
        deal = await self.deal_repo.get_by_id_with_relations(deal_id)
        if not deal:
            raise ValueError("Deal not found")
        
        # Mark as confirmed
        await self.deal_repo.confirm_by_buyer(deal_id)
        
        # Complete deal
        await self.complete_deal(deal_id)

    async def complete_deal(self, deal_id: int) -> None:
        """Complete deal and release funds to seller"""
        deal = await self.deal_repo.get_by_id_with_relations(deal_id)
        if not deal:
            raise ValueError("Deal not found")
        
        if deal.escrow_released:
            return  # Already completed
        
        # Update status
        await self.deal_repo.update_status(deal_id, DealStatus.COMPLETED)
        await self.deal_repo.release_escrow(deal_id)
        
        # Transfer funds to seller
        await self.seller_service.add_funds(
            seller_id=deal.seller_id,
            amount=deal.seller_amount,
            description=f"Оплата за заказ #{deal.order_id}"
        )
        
        # Deduct commission
        await self.transaction_repo.create_transaction(
            user_id=deal.seller.user_id,
            transaction_type=TransactionType.COMMISSION,
            amount=deal.commission_amount,
            description=f"Комиссия за заказ #{deal.order_id}",
            reference_type="deal",
            reference_id=deal_id
        )
        
        # Increment seller sales counter
        await self.seller_service.increment_sales(deal.seller_id)
        
        # Mark stock item as sold if exists
        from sqlalchemy import select
        from app.models.entities import LotStockItem
        stmt = select(LotStockItem).where(LotStockItem.deal_id == deal_id)
        result = await self.session.execute(stmt)
        stock_item = result.scalar_one_or_none()
        if stock_item:
            await self.lot_service.mark_stock_item_sold(stock_item.id)
        
        # Create system message
        await self.message_repo.create_system_message(
            deal_id=deal_id,
            message_text="Сделка завершена. Спасибо за покупку!"
        )
        
        # Notify both parties
        await self.notification_repo.create_notification(
            user_id=deal.buyer_id,
            notification_type=NotificationType.ORDER_STATUS,
            title="Сделка завершена",
            message=f"Заказ #{deal.order_id} успешно завершен",
            reference_type="deal",
            reference_id=deal_id
        )
        
        await self.notification_repo.create_notification(
            user_id=deal.seller.user_id,
            notification_type=NotificationType.PAYMENT,
            title="Средства зачислены",
            message=f"Получена оплата за заказ #{deal.order_id}",
            reference_type="deal",
            reference_id=deal_id
        )
        
        await self.session.flush()

    async def cancel_deal(
        self,
        deal_id: int,
        reason: str,
        refund: bool = True
    ) -> None:
        """Cancel deal and optionally refund buyer"""
        deal = await self.deal_repo.get_by_id_with_relations(deal_id)
        if not deal:
            raise ValueError("Deal not found")
        
        # Update status
        await self.deal_repo.update_status(deal_id, DealStatus.CANCELED)
        
        # Release reserved stock if exists
        from sqlalchemy import select
        from app.models.entities import LotStockItem
        stmt = select(LotStockItem).where(
            LotStockItem.deal_id == deal_id,
            LotStockItem.is_reserved == True
        )
        result = await self.session.execute(stmt)
        stock_item = result.scalar_one_or_none()
        if stock_item:
            await self.lot_service.release_stock_item(stock_item.id)
        
        # Refund buyer if paid
        if refund and deal.status in [DealStatus.PAID, DealStatus.IN_PROGRESS, DealStatus.WAITING_CONFIRMATION]:
            await self.transaction_repo.create_transaction(
                user_id=deal.buyer_id,
                transaction_type=TransactionType.REFUND,
                amount=deal.amount,
                description=f"Возврат за заказ #{deal.order_id}: {reason}",
                reference_type="deal",
                reference_id=deal_id
            )
        
        # Create system message
        await self.message_repo.create_system_message(
            deal_id=deal_id,
            message_text=f"Сделка отменена. Причина: {reason}"
        )
        
        # Notify both parties
        await self.notification_repo.create_notification(
            user_id=deal.buyer_id,
            notification_type=NotificationType.ORDER_STATUS,
            title="Заказ отменен",
            message=f"Заказ #{deal.order_id} отменен: {reason}",
            reference_type="deal",
            reference_id=deal_id
        )
        
        await self.notification_repo.create_notification(
            user_id=deal.seller.user_id,
            notification_type=NotificationType.ORDER_STATUS,
            title="Заказ отменен",
            message=f"Заказ #{deal.order_id} отменен: {reason}",
            reference_type="deal",
            reference_id=deal_id
        )
        
        await self.session.flush()

    async def send_message(
        self,
        deal_id: int,
        sender_id: int,
        message_text: str | None = None,
        media_id: int | None = None
    ) -> DealMessage:
        """Send message in deal chat"""
        deal = await self.deal_repo.get_by_id_with_relations(deal_id)
        if not deal:
            raise ValueError("Deal not found")
        
        message = DealMessage(
            deal_id=deal_id,
            sender_id=sender_id,
            message_text=message_text,
            media_id=media_id
        )
        self.session.add(message)
        await self.session.flush()
        
        # Notify recipient
        recipient_id = deal.seller.user_id if sender_id == deal.buyer_id else deal.buyer_id
        await self.notification_repo.create_notification(
            user_id=recipient_id,
            notification_type=NotificationType.NEW_MESSAGE,
            title="Новое сообщение",
            message=f"Новое сообщение в заказе #{deal.order_id}",
            reference_type="deal",
            reference_id=deal_id
        )
        
        return message

    async def get_deal_messages(
        self,
        deal_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[DealMessage]:
        """Get messages for deal"""
        return await self.message_repo.get_deal_messages(
            deal_id=deal_id,
            limit=limit,
            offset=offset
        )

    async def mark_messages_read(self, deal_id: int, user_id: int) -> None:
        """Mark all messages as read for user"""
        await self.message_repo.mark_as_read(deal_id, user_id)
        await self.session.flush()

    async def open_dispute(
        self,
        deal_id: int,
        initiator_id: int,
        reason: str
    ) -> DealDispute:
        """Open dispute for deal"""
        deal = await self.deal_repo.get_by_id(deal_id)
        if not deal:
            raise ValueError("Deal not found")
        
        # Update deal status
        await self.deal_repo.update_status(deal_id, DealStatus.DISPUTE)
        
        # Create dispute
        dispute = DealDispute(
            deal_id=deal_id,
            initiator_id=initiator_id,
            reason=reason,
            status=DisputeStatus.OPEN
        )
        self.session.add(dispute)
        await self.session.flush()
        
        # Create system message
        await self.message_repo.create_system_message(
            deal_id=deal_id,
            message_text=f"Открыт спор. Причина: {reason}\nАдминистрация рассмотрит обращение в ближайшее время."
        )
        
        return dispute

    async def resolve_dispute(
        self,
        dispute_id: int,
        admin_id: int,
        resolution: str,
        refund_buyer: bool = False
    ) -> None:
        """Resolve dispute"""
        dispute = await self.dispute_repo.get_by_id(dispute_id)
        if not dispute:
            raise ValueError("Dispute not found")
        
        deal = await self.deal_repo.get_by_id(dispute.deal_id)
        if not deal:
            raise ValueError("Deal not found")
        
        # Resolve dispute
        await self.dispute_repo.resolve_dispute(dispute_id, admin_id, resolution)
        
        if refund_buyer:
            # Refund and cancel
            await self.cancel_deal(dispute.deal_id, f"Спор решен в пользу покупателя: {resolution}", refund=True)
        else:
            # Complete deal in favor of seller
            await self.complete_deal(dispute.deal_id)
        
        # Create system message
        await self.message_repo.create_system_message(
            deal_id=dispute.deal_id,
            message_text=f"Спор решен администратором.\n\nРешение: {resolution}"
        )
        
        await self.session.flush()

    async def auto_complete_expired_deals(self) -> int:
        """Auto-complete deals that passed auto-complete time"""
        from sqlalchemy import select
        
        now = datetime.utcnow()
        
        stmt = select(Deal).where(
            Deal.status == DealStatus.WAITING_CONFIRMATION,
            Deal.auto_complete_at < now,
            Deal.escrow_released == False
        )
        result = await self.session.execute(stmt)
        expired_deals = result.scalars().all()
        
        for deal in expired_deals:
            await self.complete_deal(deal.id)
        
        await self.session.flush()
        return len(expired_deals)
