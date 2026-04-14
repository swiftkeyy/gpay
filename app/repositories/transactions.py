from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Transaction, SellerWithdrawal, Notification
from app.models.enums import TransactionType, TransactionStatus, WithdrawalStatus, NotificationType
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(Transaction, session)

    async def get_user_transactions(
        self,
        user_id: int,
        transaction_type: TransactionType | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Transaction]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        
        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type)
        
        stmt = stmt.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_balance(self, user_id: int) -> Decimal:
        """Get current user balance from last transaction"""
        stmt = (
            select(Transaction.balance_after)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        balance = result.scalar_one_or_none()
        return balance or Decimal("0.00")

    async def create_transaction(
        self,
        user_id: int,
        transaction_type: TransactionType,
        amount: Decimal,
        description: str | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
        metadata: dict | None = None
    ) -> Transaction:
        """Create a new transaction and update balance"""
        from app.models.entities import User
        from sqlalchemy import update
        
        # Get current balance
        current_balance = await self.get_balance(user_id)
        
        # Calculate new balance
        if transaction_type in [TransactionType.DEPOSIT, TransactionType.SALE, TransactionType.REFUND, TransactionType.BONUS]:
            new_balance = current_balance + amount
        elif transaction_type in [TransactionType.PURCHASE, TransactionType.WITHDRAWAL, TransactionType.COMMISSION, TransactionType.PENALTY]:
            new_balance = current_balance - amount
        else:
            new_balance = current_balance
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            balance_before=current_balance,
            balance_after=new_balance,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            metadata_json=metadata or {}
        )
        self.session.add(transaction)
        
        # Update user balance
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance=new_balance)
        )
        
        await self.session.flush()
        return transaction

    async def get_total_by_type(
        self,
        user_id: int,
        transaction_type: TransactionType,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> Decimal:
        """Get total amount for specific transaction type"""
        stmt = (
            select(func.sum(Transaction.amount))
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == transaction_type,
                Transaction.status == TransactionStatus.COMPLETED
            )
        )
        
        if start_date:
            stmt = stmt.where(Transaction.created_at >= start_date)
        
        if end_date:
            stmt = stmt.where(Transaction.created_at <= end_date)
        
        result = await self.session.execute(stmt)
        total = result.scalar_one_or_none()
        return total or Decimal("0.00")


class WithdrawalRepository(BaseRepository[SellerWithdrawal]):
    def __init__(self, session: AsyncSession):
        super().__init__(SellerWithdrawal, session)

    async def get_seller_withdrawals(
        self,
        seller_id: int,
        status: WithdrawalStatus | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[SellerWithdrawal]:
        stmt = select(SellerWithdrawal).where(SellerWithdrawal.seller_id == seller_id)
        
        if status:
            stmt = stmt.where(SellerWithdrawal.status == status)
        
        stmt = stmt.order_by(SellerWithdrawal.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_withdrawals(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list[SellerWithdrawal]:
        stmt = (
            select(SellerWithdrawal)
            .where(SellerWithdrawal.status == WithdrawalStatus.PENDING)
            .order_by(SellerWithdrawal.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def approve_withdrawal(
        self,
        withdrawal_id: int,
        admin_id: int
    ) -> None:
        from sqlalchemy import update
        
        await self.session.execute(
            update(SellerWithdrawal)
            .where(SellerWithdrawal.id == withdrawal_id)
            .values(
                status=WithdrawalStatus.COMPLETED,
                processed_by_admin_id=admin_id,
                processed_at=datetime.utcnow()
            )
        )

    async def reject_withdrawal(
        self,
        withdrawal_id: int,
        admin_id: int,
        reason: str
    ) -> None:
        from sqlalchemy import update
        
        await self.session.execute(
            update(SellerWithdrawal)
            .where(SellerWithdrawal.id == withdrawal_id)
            .values(
                status=WithdrawalStatus.REJECTED,
                processed_by_admin_id=admin_id,
                processed_at=datetime.utcnow(),
                rejection_reason=reason
            )
        )


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)

    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: int) -> int:
        stmt = (
            select(func.count(Notification.id))
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def mark_as_read(self, notification_id: int) -> None:
        from sqlalchemy import update
        
        await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(
                is_read=True,
                read_at=datetime.utcnow()
            )
        )

    async def mark_all_as_read(self, user_id: int) -> None:
        from sqlalchemy import update
        
        await self.session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .values(
                is_read=True,
                read_at=datetime.utcnow()
            )
        )

    async def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        reference_type: str | None = None,
        reference_id: int | None = None
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id
        )
        self.session.add(notification)
        await self.session.flush()
        return notification
