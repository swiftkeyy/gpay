from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Deal, DealMessage, DealDispute, Seller, User, Lot, Order
from app.models.enums import DealStatus, DisputeStatus
from app.repositories.base import BaseRepository


class DealRepository(BaseRepository[Deal]):
    def __init__(self, session: AsyncSession):
        super().__init__(Deal, session)

    async def get_by_id_with_relations(self, deal_id: int) -> Deal | None:
        stmt = (
            select(Deal)
            .where(Deal.id == deal_id)
            .options(
                selectinload(Deal.buyer),
                selectinload(Deal.seller).selectinload(Seller.user),
                selectinload(Deal.lot),
                selectinload(Deal.order),
                selectinload(Deal.messages)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_order_id(self, order_id: int) -> Deal | None:
        stmt = (
            select(Deal)
            .where(Deal.order_id == order_id)
            .options(
                selectinload(Deal.buyer),
                selectinload(Deal.seller).selectinload(Seller.user),
                selectinload(Deal.lot)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_deals(
        self,
        user_id: int,
        as_buyer: bool = True,
        status: DealStatus | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Deal]:
        if as_buyer:
            stmt = select(Deal).where(Deal.buyer_id == user_id)
        else:
            # User is seller
            stmt = (
                select(Deal)
                .join(Seller, Deal.seller_id == Seller.id)
                .where(Seller.user_id == user_id)
            )
        
        if status:
            stmt = stmt.where(Deal.status == status)
        
        stmt = (
            stmt
            .options(
                selectinload(Deal.buyer),
                selectinload(Deal.seller).selectinload(Seller.user),
                selectinload(Deal.lot),
                selectinload(Deal.order)
            )
            .order_by(Deal.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_seller_deals(
        self,
        seller_id: int,
        status: DealStatus | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Deal]:
        stmt = select(Deal).where(Deal.seller_id == seller_id)
        
        if status:
            stmt = stmt.where(Deal.status == status)
        
        stmt = (
            stmt
            .options(
                selectinload(Deal.buyer),
                selectinload(Deal.lot),
                selectinload(Deal.order)
            )
            .order_by(Deal.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, deal_id: int, status: DealStatus) -> None:
        values = {"status": status}
        
        if status == DealStatus.COMPLETED:
            values["completed_at"] = datetime.utcnow()
        
        await self.session.execute(
            update(Deal)
            .where(Deal.id == deal_id)
            .values(**values)
        )

    async def confirm_by_buyer(self, deal_id: int) -> None:
        await self.session.execute(
            update(Deal)
            .where(Deal.id == deal_id)
            .values(
                buyer_confirmed=True,
                buyer_confirmed_at=datetime.utcnow()
            )
        )

    async def release_escrow(self, deal_id: int) -> None:
        await self.session.execute(
            update(Deal)
            .where(Deal.id == deal_id)
            .values(
                escrow_released=True,
                escrow_released_at=datetime.utcnow()
            )
        )

    async def get_unread_count(self, deal_id: int, user_id: int) -> int:
        """Get count of unread messages for user in deal"""
        stmt = (
            select(func.count(DealMessage.id))
            .where(
                DealMessage.deal_id == deal_id,
                DealMessage.sender_id != user_id,
                DealMessage.is_read == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()


class DealMessageRepository(BaseRepository[DealMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(DealMessage, session)

    async def get_deal_messages(
        self,
        deal_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[DealMessage]:
        stmt = (
            select(DealMessage)
            .where(DealMessage.deal_id == deal_id)
            .options(selectinload(DealMessage.sender))
            .order_by(DealMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(self, deal_id: int, user_id: int) -> None:
        """Mark all messages in deal as read for user (except user's own messages)"""
        await self.session.execute(
            update(DealMessage)
            .where(
                DealMessage.deal_id == deal_id,
                DealMessage.sender_id != user_id,
                DealMessage.is_read == False
            )
            .values(
                is_read=True,
                read_at=datetime.utcnow()
            )
        )

    async def create_system_message(
        self,
        deal_id: int,
        message_text: str
    ) -> DealMessage:
        """Create a system message in deal"""
        message = DealMessage(
            deal_id=deal_id,
            sender_id=1,  # System user
            message_text=message_text,
            is_system=True,
            is_read=True
        )
        self.session.add(message)
        await self.session.flush()
        return message


class DealDisputeRepository(BaseRepository[DealDispute]):
    def __init__(self, session: AsyncSession):
        super().__init__(DealDispute, session)

    async def get_by_deal_id(self, deal_id: int) -> DealDispute | None:
        stmt = (
            select(DealDispute)
            .where(DealDispute.deal_id == deal_id)
            .options(
                selectinload(DealDispute.initiator)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_disputes(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list[DealDispute]:
        stmt = (
            select(DealDispute)
            .where(DealDispute.status.in_([DisputeStatus.OPEN, DisputeStatus.IN_REVIEW]))
            .options(
                selectinload(DealDispute.initiator)
            )
            .order_by(DealDispute.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def resolve_dispute(
        self,
        dispute_id: int,
        admin_id: int,
        resolution: str
    ) -> None:
        await self.session.execute(
            update(DealDispute)
            .where(DealDispute.id == dispute_id)
            .values(
                status=DisputeStatus.RESOLVED,
                admin_id=admin_id,
                resolution=resolution,
                resolved_at=datetime.utcnow()
            )
        )
