"""Admin panel router."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.entities import User, Seller, Lot, Deal, Dispute, Transaction, Withdrawal, Review as ProductReview, Review as SellerReview, AuditLog, Broadcast
)
from api.dependencies.auth import get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models
class UserUpdateRequest(BaseModel):
    is_blocked: Optional[bool] = None
    balance_adjustment: Optional[Decimal] = None


class SellerUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|active|suspended|banned)$")
    is_verified: Optional[bool] = None


class LotModerationRequest(BaseModel):
    status: Optional[str] = Field(None, pattern="^(draft|active|suspended|deleted)$")
    rejection_reason: Optional[str] = Field(None, max_length=500)


class DisputeResolutionRequest(BaseModel):
    resolution: str = Field(..., pattern="^(release_to_seller|refund_to_buyer|partial)$")
    partial_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    comment: Optional[str] = Field(None, max_length=1000)


class WithdrawalProcessRequest(BaseModel):
    status: str = Field(..., pattern="^(completed|failed)$")
    comment: Optional[str] = Field(None, max_length=500)


class BroadcastCreateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    scheduled_at: Optional[datetime] = None


class ReviewModerationRequest(BaseModel):
    status: str = Field(..., pattern="^(published|rejected)$")
    rejection_reason: Optional[str] = Field(None, max_length=500)


# Dashboard
@router.get("/dashboard")
async def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard stats."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    # Total users
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()
    
    # New users today
    result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    new_users_today = result.scalar()
    
    # Active sellers
    result = await db.execute(
        select(func.count(Seller.id)).where(Seller.status == 'active')
    )
    active_sellers = result.scalar()
    
    # Pending seller applications
    result = await db.execute(
        select(func.count(Seller.id)).where(Seller.status == 'pending')
    )
    pending_sellers = result.scalar()
    
    # Total orders
    result = await db.execute(select(func.count(Deal.id)))
    total_orders = result.scalar()
    
    # Orders today
    result = await db.execute(
        select(func.count(Deal.id)).where(Deal.created_at >= today_start)
    )
    orders_today = result.scalar()
    
    # Revenue (completed deals)
    result = await db.execute(
        select(func.coalesce(func.sum(Deal.amount), 0)).where(Deal.status == 'completed')
    )
    total_revenue = result.scalar()
    
    # Revenue today
    result = await db.execute(
        select(func.coalesce(func.sum(Deal.amount), 0)).where(
            and_(Deal.status == 'completed', Deal.completed_at >= today_start)
        )
    )
    revenue_today = result.scalar()
    
    # Commission earned
    result = await db.execute(
        select(func.coalesce(func.sum(Deal.commission_amount), 0)).where(Deal.status == 'completed')
    )
    total_commission = result.scalar()
    
    # Active disputes
    result = await db.execute(
        select(func.count(Dispute.id)).where(Dispute.status == 'open')
    )
    active_disputes = result.scalar()
    
    # Pending withdrawals
    result = await db.execute(
        select(func.count(Withdrawal.id)).where(Withdrawal.status == 'pending')
    )
    pending_withdrawals = result.scalar()
    
    return {
        "users": {
            "total": total_users,
            "new_today": new_users_today
        },
        "sellers": {
            "active": active_sellers,
            "pending": pending_sellers
        },
        "orders": {
            "total": total_orders,
            "today": orders_today
        },
        "revenue": {
            "total": float(total_revenue),
            "today": float(revenue_today),
            "commission": float(total_commission)
        },
        "moderation": {
            "active_disputes": active_disputes,
            "pending_withdrawals": pending_withdrawals
        }
    }


# User management
@router.get("/users")
async def get_users(
    search: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get users list with filters."""
    query = select(User)
    
    if search:
        query = query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.telegram_id.cast(str).ilike(f"%{search}%")
            )
        )
    
    if is_blocked is not None:
        query = query.where(User.is_blocked == is_blocked)
    
    query = query.order_by(desc(User.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "items": [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "balance": float(user.balance),
                "is_blocked": user.is_blocked,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ],
        "total": len(users),
        "skip": skip,
        "limit": limit
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user (block, grant balance)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.is_blocked is not None:
        user.is_blocked = request.is_blocked
        
        # Audit log
        audit = AuditLog(
            admin_id=current_admin.id,
            action_type="user_block" if request.is_blocked else "user_unblock",
            entity_type="user",
            entity_id=user_id,
            description=f"User {'blocked' if request.is_blocked else 'unblocked'}"
        )
        db.add(audit)
    
    if request.balance_adjustment:
        user.balance += request.balance_adjustment
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            type="admin_adjustment",
            amount=request.balance_adjustment,
            description=f"Balance adjustment by admin"
        )
        db.add(transaction)
        
        # Audit log
        audit = AuditLog(
            admin_id=current_admin.id,
            action_type="balance_adjustment",
            entity_type="user",
            entity_id=user_id,
            description=f"Balance adjusted by {request.balance_adjustment}"
        )
        db.add(audit)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "balance": float(user.balance),
        "is_blocked": user.is_blocked
    }


# Seller management
@router.get("/sellers")
async def get_sellers(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get sellers list with filters."""
    query = select(Seller).options(selectinload(Seller.user))
    
    if status:
        query = query.where(Seller.status == status)
    
    query = query.order_by(desc(Seller.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    sellers = result.scalars().all()
    
    return {
        "items": [
            {
                "id": seller.id,
                "user_id": seller.user_id,
                "shop_name": seller.shop_name,
                "status": seller.status,
                "is_verified": seller.is_verified,
                "rating": float(seller.rating),
                "total_sales": seller.total_sales,
                "balance": float(seller.balance),
                "created_at": seller.created_at.isoformat()
            }
            for seller in sellers
        ],
        "total": len(sellers),
        "skip": skip,
        "limit": limit
    }


@router.patch("/sellers/{seller_id}")
async def update_seller(
    seller_id: int,
    request: SellerUpdateRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve/suspend seller."""
    result = await db.execute(select(Seller).where(Seller.id == seller_id))
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    if request.status:
        old_status = seller.status
        seller.status = request.status
        
        # Audit log
        audit = AuditLog(
            admin_id=current_admin.id,
            action_type="seller_status_change",
            entity_type="seller",
            entity_id=seller_id,
            description=f"Status changed from {old_status} to {request.status}"
        )
        db.add(audit)
    
    if request.is_verified is not None:
        seller.is_verified = request.is_verified
    
    await db.commit()
    await db.refresh(seller)
    
    return {
        "id": seller.id,
        "status": seller.status,
        "is_verified": seller.is_verified
    }


# Lot moderation
@router.get("/lots")
async def get_all_lots(
    status: Optional[str] = None,
    seller_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all lots for moderation."""
    query = select(Lot).options(selectinload(Lot.seller))
    
    if status:
        query = query.where(Lot.status == status)
    
    if seller_id:
        query = query.where(Lot.seller_id == seller_id)
    
    query = query.order_by(desc(Lot.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    lots = result.scalars().all()
    
    return {
        "items": [
            {
                "id": lot.id,
                "seller_id": lot.seller_id,
                "title": lot.title,
                "price": float(lot.price),
                "status": lot.status,
                "delivery_type": lot.delivery_type,
                "views": lot.views,
                "sales": lot.sales,
                "created_at": lot.created_at.isoformat()
            }
            for lot in lots
        ],
        "total": len(lots),
        "skip": skip,
        "limit": limit
    }


@router.patch("/lots/{lot_id}")
async def moderate_lot(
    lot_id: int,
    request: LotModerationRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Moderate lot (approve/reject/suspend)."""
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    if request.status:
        old_status = lot.status
        lot.status = request.status
        
        # Audit log
        audit = AuditLog(
            admin_id=current_admin.id,
            action_type="lot_moderation",
            entity_type="lot",
            entity_id=lot_id,
            description=f"Status changed from {old_status} to {request.status}",
            metadata={"rejection_reason": request.rejection_reason} if request.rejection_reason else None
        )
        db.add(audit)
    
    await db.commit()
    await db.refresh(lot)
    
    return {
        "id": lot.id,
        "status": lot.status
    }


# Dispute management
@router.get("/disputes")
async def get_disputes(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get disputes list."""
    query = select(Dispute).options(selectinload(Dispute.deal))
    
    if status:
        query = query.where(Dispute.status == status)
    
    query = query.order_by(desc(Dispute.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    disputes = result.scalars().all()
    
    return {
        "items": [
            {
                "id": dispute.id,
                "deal_id": dispute.deal_id,
                "opened_by": dispute.opened_by,
                "reason": dispute.reason,
                "description": dispute.description,
                "status": dispute.status,
                "created_at": dispute.created_at.isoformat()
            }
            for dispute in disputes
        ],
        "total": len(disputes),
        "skip": skip,
        "limit": limit
    }


# Withdrawal management
@router.get("/withdrawals")
async def get_withdrawals(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get withdrawals list."""
    query = select(Withdrawal).options(selectinload(Withdrawal.seller))
    
    if status:
        query = query.where(Withdrawal.status == status)
    
    query = query.order_by(desc(Withdrawal.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    withdrawals = result.scalars().all()
    
    return {
        "items": [
            {
                "id": w.id,
                "seller_id": w.seller_id,
                "amount": float(w.amount),
                "payment_method": w.payment_method,
                "payment_details": w.payment_details,
                "status": w.status,
                "created_at": w.created_at.isoformat()
            }
            for w in withdrawals
        ],
        "total": len(withdrawals),
        "skip": skip,
        "limit": limit
    }


@router.patch("/withdrawals/{withdrawal_id}")
async def process_withdrawal(
    withdrawal_id: int,
    request: WithdrawalProcessRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Process withdrawal (complete/fail)."""
    result = await db.execute(
        select(Withdrawal).options(selectinload(Withdrawal.seller)).where(Withdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="Withdrawal already processed")
    
    withdrawal.status = request.status
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.admin_comment = request.comment
    
    # If failed, refund to seller balance
    if request.status == "failed":
        withdrawal.seller.balance += withdrawal.amount
    
    # Audit log
    audit = AuditLog(
        admin_id=current_admin.id,
        action_type="withdrawal_processed",
        entity_type="withdrawal",
        entity_id=withdrawal_id,
        description=f"Withdrawal {request.status}",
        metadata={"comment": request.comment} if request.comment else None
    )
    db.add(audit)
    
    await db.commit()
    
    return {
        "id": withdrawal.id,
        "status": withdrawal.status
    }


# Broadcasts
@router.post("/broadcasts")
async def create_broadcast(
    request: BroadcastCreateRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create broadcast message."""
    broadcast = Broadcast(
        admin_id=current_admin.id,
        message=request.message,
        scheduled_at=request.scheduled_at or datetime.utcnow(),
        status="pending"
    )
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)
    
    logger.info(f"Broadcast created: id={broadcast.id}, admin_id={current_admin.id}")
    
    return {
        "broadcast_id": broadcast.id,
        "status": "pending",
        "scheduled_at": broadcast.scheduled_at.isoformat()
    }


@router.get("/broadcasts")
async def get_broadcasts(
    skip: int = 0,
    limit: int = 20,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get broadcasts history."""
    result = await db.execute(
        select(Broadcast)
        .order_by(desc(Broadcast.created_at))
        .offset(skip)
        .limit(limit)
    )
    broadcasts = result.scalars().all()
    
    return {
        "items": [
            {
                "id": b.id,
                "message": b.message,
                "status": b.status,
                "scheduled_at": b.scheduled_at.isoformat(),
                "sent_at": b.sent_at.isoformat() if b.sent_at else None,
                "recipients_count": b.recipients_count,
                "created_at": b.created_at.isoformat()
            }
            for b in broadcasts
        ],
        "total": len(broadcasts),
        "skip": skip,
        "limit": limit
    }


# Audit logs
@router.get("/audit-logs")
async def get_audit_logs(
    action_type: Optional[str] = None,
    admin_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs."""
    query = select(AuditLog)
    
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    
    if admin_id:
        query = query.where(AuditLog.admin_id == admin_id)
    
    query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "action_type": log.action_type,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "description": log.description,
                "metadata": log.metadata,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "total": len(logs),
        "skip": skip,
        "limit": limit
    }
