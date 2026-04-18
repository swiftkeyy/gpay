"""Deals management router - escrow, delivery, disputes."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.entities import (
    Deal, DealMessage, DealDispute, Lot, User, Seller, Transaction
)
from app.models.enums import (
    DealStatus, TransactionType, TransactionStatus
)

router = APIRouter()


# Request/Response Models
class DeliverGoodsRequest(BaseModel):
    delivery_data: str
    comment: str | None = None


class ConfirmDeliveryRequest(BaseModel):
    rating: int | None = None
    comment: str | None = None


class OpenDisputeRequest(BaseModel):
    reason: str
    description: str


class ResolveDisputeRequest(BaseModel):
    resolution: str  # release_to_seller, refund_to_buyer, partial
    comment: str
    partial_amount: Decimal | None = None


class DealResponse(BaseModel):
    id: int
    order_id: int
    buyer_id: int
    seller_id: int
    lot_id: int
    lot_title: str
    status: str
    amount: Decimal
    commission_amount: Decimal
    seller_amount: Decimal
    escrow_released: bool
    auto_complete_at: datetime | None
    completed_at: datetime | None
    buyer_confirmed: bool
    created_at: datetime
    updated_at: datetime


class DisputeResponse(BaseModel):
    id: int
    deal_id: int
    initiator_id: int
    reason: str
    description: str
    status: str
    resolution: str | None
    admin_comment: str | None
    created_at: datetime
    resolved_at: datetime | None


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Get deal details."""
    # Get deal with lot
    result = await session.execute(
        select(Deal)
        .options(selectinload(Deal.lot))
        .where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check access
    if deal.buyer_id != user_id and deal.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return DealResponse(
        id=deal.id,
        order_id=deal.order_id,
        buyer_id=deal.buyer_id,
        seller_id=deal.seller_id,
        lot_id=deal.lot_id,
        lot_title=deal.lot.title,
        status=deal.status.value,
        amount=deal.amount,
        commission_amount=deal.commission_amount,
        seller_amount=deal.seller_amount,
        escrow_released=deal.escrow_released,
        auto_complete_at=deal.auto_complete_at,
        completed_at=deal.completed_at,
        buyer_confirmed=deal.buyer_confirmed,
        created_at=deal.created_at,
        updated_at=deal.updated_at
    )


@router.post("/{deal_id}/deliver")
async def deliver_goods(
    deal_id: int,
    request: DeliverGoodsRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Seller delivers goods manually."""
    # Get deal
    result = await session.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check seller access
    if deal.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Only seller can deliver goods")
    
    # Check status
    if deal.status not in [DealStatus.PAID, DealStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot deliver goods for deal with status: {deal.status.value}"
        )
    
    # Update deal
    deal.status = DealStatus.WAITING_CONFIRMATION
    deal.updated_at = datetime.utcnow()
    
    # TODO: Store delivery_data securely
    # TODO: Send notification to buyer
    
    await session.commit()
    
    return {
        "message": "Goods delivered, waiting for buyer confirmation",
        "deal_id": deal_id,
        "status": deal.status.value
    }


@router.post("/{deal_id}/confirm")
async def confirm_delivery(
    deal_id: int,
    request: ConfirmDeliveryRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Buyer confirms delivery and releases escrow."""
    # Get deal
    result = await session.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check buyer access
    if deal.buyer_id != user_id:
        raise HTTPException(status_code=403, detail="Only buyer can confirm delivery")
    
    # Check status
    if deal.status != DealStatus.WAITING_CONFIRMATION:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm delivery for deal with status: {deal.status.value}"
        )
    
    # Update deal
    deal.status = DealStatus.COMPLETED
    deal.completed_at = datetime.utcnow()
    deal.buyer_confirmed = True
    deal.buyer_confirmed_at = datetime.utcnow()
    deal.updated_at = datetime.utcnow()
    
    # Release escrow
    await _release_escrow(deal, session)
    
    # TODO: Create review if rating provided
    
    await session.commit()
    
    return {
        "message": "Delivery confirmed, escrow released to seller",
        "deal_id": deal_id,
        "status": deal.status.value
    }


@router.post("/{deal_id}/dispute")
async def open_dispute(
    deal_id: int,
    request: OpenDisputeRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Open dispute for deal."""
    # Get deal
    result = await session.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check access
    if deal.buyer_id != user_id and deal.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check status
    if deal.status in [DealStatus.COMPLETED, DealStatus.CANCELED, DealStatus.REFUNDED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot open dispute for deal with status: {deal.status.value}"
        )
    
    # Check if dispute already exists
    result = await session.execute(
        select(DealDispute).where(
            and_(
                DealDispute.deal_id == deal_id,
                DealDispute.status == "open"
            )
        )
    )
    existing_dispute = result.scalar_one_or_none()
    
    if existing_dispute:
        raise HTTPException(status_code=400, detail="Dispute already exists for this deal")
    
    # Create dispute
    dispute = DealDispute(
        deal_id=deal_id,
        initiator_id=user_id,
        reason=request.reason,
        description=request.description,
        status="open"
    )
    session.add(dispute)
    
    # Update deal status
    deal.status = DealStatus.DISPUTE
    deal.updated_at = datetime.utcnow()
    
    # TODO: Notify admin
    
    await session.commit()
    
    return {
        "message": "Dispute opened, admin will review",
        "dispute_id": dispute.id,
        "deal_id": deal_id
    }


@router.get("/{deal_id}/dispute", response_model=DisputeResponse)
async def get_dispute(
    deal_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Get dispute details."""
    # Get deal first to check access
    result = await session.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check access
    if deal.buyer_id != user_id and deal.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get dispute
    result = await session.execute(
        select(DealDispute).where(DealDispute.deal_id == deal_id)
    )
    dispute = result.scalar_one_or_none()
    
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    return DisputeResponse(
        id=dispute.id,
        deal_id=dispute.deal_id,
        initiator_id=dispute.initiator_id,
        reason=dispute.reason,
        description=dispute.description,
        status=dispute.status,
        resolution=dispute.resolution,
        admin_comment=dispute.admin_comment,
        created_at=dispute.created_at,
        resolved_at=dispute.resolved_at
    )


@router.post("/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: int,
    request: ResolveDisputeRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Admin resolves dispute."""
    # TODO: Check if user is admin
    
    # Get dispute with deal
    result = await session.execute(
        select(DealDispute)
        .options(selectinload(DealDispute.deal))
        .where(DealDispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    if dispute.status != "open":
        raise HTTPException(status_code=400, detail="Dispute is already resolved")
    
    deal = dispute.deal
    
    # Process resolution
    if request.resolution == "release_to_seller":
        # Release escrow to seller
        await _release_escrow(deal, session)
        deal.status = DealStatus.COMPLETED
        deal.completed_at = datetime.utcnow()
        
    elif request.resolution == "refund_to_buyer":
        # Refund to buyer
        await _refund_to_buyer(deal, session)
        deal.status = DealStatus.REFUNDED
        
    elif request.resolution == "partial":
        # Partial refund
        if not request.partial_amount:
            raise HTTPException(status_code=400, detail="partial_amount required for partial resolution")
        
        await _partial_refund(deal, request.partial_amount, session)
        deal.status = DealStatus.COMPLETED
        deal.completed_at = datetime.utcnow()
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown resolution: {request.resolution}")
    
    # Update dispute
    dispute.status = "resolved"
    dispute.resolution = request.resolution
    dispute.admin_comment = request.comment
    dispute.resolved_at = datetime.utcnow()
    dispute.resolved_by_id = user_id
    
    deal.updated_at = datetime.utcnow()
    
    # TODO: Notify buyer and seller
    
    await session.commit()
    
    return {
        "message": "Dispute resolved",
        "dispute_id": dispute_id,
        "resolution": request.resolution
    }


async def _release_escrow(deal: Deal, session: AsyncSession):
    """Release escrow funds to seller."""
    if deal.escrow_released:
        return
    
    # Get seller
    result = await session.execute(
        select(Seller).where(Seller.id == deal.seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        return
    
    # Get seller user
    result = await session.execute(
        select(User).where(User.id == seller.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return
    
    # Add funds to seller balance
    old_balance = user.balance
    user.balance += deal.seller_amount
    
    # Create transaction for seller
    seller_transaction = Transaction(
        user_id=user.id,
        transaction_type=TransactionType.SALE,
        amount=deal.seller_amount,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=old_balance,
        balance_after=user.balance,
        description=f"Payment for deal #{deal.id}",
        reference_type="deal",
        reference_id=deal.id
    )
    session.add(seller_transaction)
    
    # Create transaction for commission
    commission_transaction = Transaction(
        user_id=user.id,
        transaction_type=TransactionType.COMMISSION,
        amount=-deal.commission_amount,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=user.balance,
        balance_after=user.balance,
        description=f"Commission for deal #{deal.id}",
        reference_type="deal",
        reference_id=deal.id
    )
    session.add(commission_transaction)
    
    # Mark escrow as released
    deal.escrow_released = True
    deal.escrow_released_at = datetime.utcnow()
    
    await session.flush()


async def _refund_to_buyer(deal: Deal, session: AsyncSession):
    """Refund full amount to buyer."""
    # Get buyer
    result = await session.execute(
        select(User).where(User.id == deal.buyer_id)
    )
    buyer = result.scalar_one_or_none()
    
    if not buyer:
        return
    
    # Add funds to buyer balance
    old_balance = buyer.balance
    buyer.balance += deal.amount
    
    # Create transaction
    refund_transaction = Transaction(
        user_id=buyer.id,
        transaction_type=TransactionType.REFUND,
        amount=deal.amount,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=old_balance,
        balance_after=buyer.balance,
        description=f"Refund for deal #{deal.id}",
        reference_type="deal",
        reference_id=deal.id
    )
    session.add(refund_transaction)
    
    await session.flush()


async def _partial_refund(deal: Deal, refund_amount: Decimal, session: AsyncSession):
    """Partial refund to buyer, rest to seller."""
    # Refund to buyer
    result = await session.execute(
        select(User).where(User.id == deal.buyer_id)
    )
    buyer = result.scalar_one_or_none()
    
    if buyer:
        old_balance = buyer.balance
        buyer.balance += refund_amount
        
        refund_transaction = Transaction(
            user_id=buyer.id,
            transaction_type=TransactionType.REFUND,
            amount=refund_amount,
            currency_code="RUB",
            status=TransactionStatus.COMPLETED,
            balance_before=old_balance,
            balance_after=buyer.balance,
            description=f"Partial refund for deal #{deal.id}",
            reference_type="deal",
            reference_id=deal.id
        )
        session.add(refund_transaction)
    
    # Pay seller the rest
    seller_amount = deal.amount - refund_amount - deal.commission_amount
    
    result = await session.execute(
        select(Seller).where(Seller.id == deal.seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if seller:
        result = await session.execute(
            select(User).where(User.id == seller.user_id)
        )
        seller_user = result.scalar_one_or_none()
        
        if seller_user:
            old_balance = seller_user.balance
            seller_user.balance += seller_amount
            
            seller_transaction = Transaction(
                user_id=seller_user.id,
                transaction_type=TransactionType.SALE,
                amount=seller_amount,
                currency_code="RUB",
                status=TransactionStatus.COMPLETED,
                balance_before=old_balance,
                balance_after=seller_user.balance,
                description=f"Partial payment for deal #{deal.id}",
                reference_type="deal",
                reference_id=deal.id
            )
            session.add(seller_transaction)
    
    # Mark escrow as released
    deal.escrow_released = True
    deal.escrow_released_at = datetime.utcnow()
    
    await session.flush()


@router.post("/auto-complete")
async def auto_complete_deals(
    session: AsyncSession = Depends(get_session)
):
    """Auto-complete deals after timeout (cron job)."""
    # Get deals waiting for confirmation that passed auto_complete_at
    result = await session.execute(
        select(Deal).where(
            and_(
                Deal.status == DealStatus.WAITING_CONFIRMATION,
                Deal.auto_complete_at <= datetime.utcnow(),
                Deal.escrow_released == False
            )
        )
    )
    deals = result.scalars().all()
    
    completed_count = 0
    
    for deal in deals:
        # Auto-complete
        deal.status = DealStatus.COMPLETED
        deal.completed_at = datetime.utcnow()
        deal.buyer_confirmed = False  # Auto-completed, not manually confirmed
        deal.updated_at = datetime.utcnow()
        
        # Release escrow
        await _release_escrow(deal, session)
        
        completed_count += 1
    
    await session.commit()
    
    return {
        "message": f"Auto-completed {completed_count} deals",
        "count": completed_count
    }
