"""Admin panel router."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.entities import (
    User, Admin, Seller, Lot, Deal, DealDispute, SellerWithdrawal, Order
)
from app.models.enums import DealStatus

router = APIRouter()


# Helper function to check admin access
async def require_admin(user_id: int, session: AsyncSession):
    """Check if user is admin."""
    result = await session.execute(
        select(Admin).where(Admin.user_id == user_id)
    )
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return admin


# Dashboard
@router.get("/dashboard")
async def get_dashboard(
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Get admin dashboard stats."""
    await require_admin(user_id, session)
    
    # Total users
    result = await session.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0
    
    # Total sellers
    result = await session.execute(select(func.count(Seller.id)))
    total_sellers = result.scalar() or 0
    
    # Total lots
    result = await session.execute(select(func.count(Lot.id)))
    total_lots = result.scalar() or 0
    
    # Active lots
    result = await session.execute(
        select(func.count(Lot.id)).where(Lot.status == "active")
    )
    active_lots = result.scalar() or 0
    
    # Total deals
    result = await session.execute(select(func.count(Deal.id)))
    total_deals = result.scalar() or 0
    
    # Completed deals
    result = await session.execute(
        select(func.count(Deal.id)).where(Deal.status == DealStatus.COMPLETED)
    )
    completed_deals = result.scalar() or 0
    
    # Open disputes
    result = await session.execute(
        select(func.count(DealDispute.id)).where(DealDispute.status == "open")
    )
    open_disputes = result.scalar() or 0
    
    # Pending withdrawals
    result = await session.execute(
        select(func.count(SellerWithdrawal.id)).where(SellerWithdrawal.status == "pending")
    )
    pending_withdrawals = result.scalar() or 0
    
    # Total revenue (commission)
    result = await session.execute(
        select(func.coalesce(func.sum(Deal.commission_amount), 0)).where(
            Deal.status == DealStatus.COMPLETED
        )
    )
    total_revenue = result.scalar() or 0
    
    return {
        "users": {
            "total": total_users,
            "sellers": total_sellers
        },
        "lots": {
            "total": total_lots,
            "active": active_lots
        },
        "deals": {
            "total": total_deals,
            "completed": completed_deals
        },
        "disputes": {
            "open": open_disputes
        },
        "withdrawals": {
            "pending": pending_withdrawals
        },
        "revenue": {
            "total": float(total_revenue)
        }
    }


# Users management
@router.get("/users")
async def get_users(
    user_id: int = 1,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get users list."""
    await require_admin(user_id, session)
    
    offset = (page - 1) * limit
    
    query = select(User)
    
    if search:
        query = query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%")
            )
        )
    
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    
    result = await session.execute(query)
    users = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(User.id))
    if search:
        count_query = count_query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%")
            )
        )
    
    result = await session.execute(count_query)
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "balance": float(user.balance),
                "is_blocked": user.is_blocked,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/users/{user_id}/block")
async def block_user(
    target_user_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Block user."""
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(User).where(User.id == target_user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_blocked = True
    await session.commit()
    
    return {"message": "User blocked"}


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    target_user_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Unblock user."""
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(User).where(User.id == target_user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_blocked = False
    await session.commit()
    
    return {"message": "User unblocked"}


# Sellers management
@router.get("/sellers")
async def get_sellers(
    user_id: int = 1,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get sellers list."""
    await require_admin(user_id, session)
    
    offset = (page - 1) * limit
    
    query = select(Seller).options(selectinload(Seller.user))
    
    if status:
        query = query.where(Seller.status == status)
    
    query = query.order_by(Seller.created_at.desc()).offset(offset).limit(limit)
    
    result = await session.execute(query)
    sellers = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(Seller.id))
    if status:
        count_query = count_query.where(Seller.status == status)
    
    result = await session.execute(count_query)
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": seller.id,
                "user_id": seller.user_id,
                "username": seller.user.username if seller.user else None,
                "status": seller.status,
                "rating": float(seller.rating),
                "total_sales": seller.total_sales,
                "balance": float(seller.balance),
                "created_at": seller.created_at.isoformat()
            }
            for seller in sellers
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/sellers/{seller_id}/approve")
async def approve_seller(
    seller_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Approve seller application."""
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(Seller).where(Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    seller.status = "active"
    await session.commit()
    
    return {"message": "Seller approved"}


@router.post("/sellers/{seller_id}/reject")
async def reject_seller(
    seller_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Reject seller application."""
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(Seller).where(Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    seller.status = "rejected"
    await session.commit()
    
    return {"message": "Seller rejected"}


# Lots management
@router.get("/lots")
async def get_lots(
    user_id: int = 1,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get lots list."""
    await require_admin(user_id, session)
    
    offset = (page - 1) * limit
    
    query = select(Lot).options(selectinload(Lot.seller).selectinload(Seller.user))
    
    if status:
        query = query.where(Lot.status == status)
    
    query = query.order_by(Lot.created_at.desc()).offset(offset).limit(limit)
    
    result = await session.execute(query)
    lots = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(Lot.id))
    if status:
        count_query = count_query.where(Lot.status == status)
    
    result = await session.execute(count_query)
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": lot.id,
                "title": lot.title,
                "price": float(lot.price),
                "seller_name": lot.seller.user.username if lot.seller and lot.seller.user else "Unknown",
                "status": lot.status,
                "stock_count": lot.stock_count,
                "views": lot.views,
                "sales": lot.sales,
                "created_at": lot.created_at.isoformat()
            }
            for lot in lots
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/lots/{lot_id}/approve")
async def approve_lot(
    lot_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Approve lot."""
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(Lot).where(Lot.id == lot_id)
    )
    lot = result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    lot.status = "active"
    await session.commit()
    
    return {"message": "Lot approved"}


@router.post("/lots/{lot_id}/reject")
async def reject_lot(
    lot_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Reject lot."""
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(Lot).where(Lot.id == lot_id)
    )
    lot = result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    lot.status = "rejected"
    await session.commit()
    
    return {"message": "Lot rejected"}


# Withdrawals management
@router.get("/withdrawals")
async def get_withdrawals(
    user_id: int = 1,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get withdrawals list."""
    await require_admin(user_id, session)
    
    offset = (page - 1) * limit
    
    query = select(SellerWithdrawal).options(
        selectinload(SellerWithdrawal.seller).selectinload(Seller.user)
    )
    
    if status:
        query = query.where(SellerWithdrawal.status == status)
    
    query = query.order_by(SellerWithdrawal.created_at.desc()).offset(offset).limit(limit)
    
    result = await session.execute(query)
    withdrawals = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(SellerWithdrawal.id))
    if status:
        count_query = count_query.where(SellerWithdrawal.status == status)
    
    result = await session.execute(count_query)
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": withdrawal.id,
                "seller_name": withdrawal.seller.user.username if withdrawal.seller and withdrawal.seller.user else "Unknown",
                "amount": float(withdrawal.amount),
                "payment_method": withdrawal.payment_method,
                "status": withdrawal.status,
                "created_at": withdrawal.created_at.isoformat()
            }
            for withdrawal in withdrawals
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/withdrawals/{withdrawal_id}/approve")
async def approve_withdrawal(
    withdrawal_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Approve withdrawal."""
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(SellerWithdrawal).where(SellerWithdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="Withdrawal is not pending")
    
    withdrawal.status = "completed"
    withdrawal.processed_at = datetime.utcnow()
    await session.commit()
    
    return {"message": "Withdrawal approved"}


@router.post("/withdrawals/{withdrawal_id}/reject")
async def reject_withdrawal(
    withdrawal_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Reject withdrawal."""
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(SellerWithdrawal).where(SellerWithdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="Withdrawal is not pending")
    
    # Return funds to seller
    result = await session.execute(
        select(Seller).where(Seller.id == withdrawal.seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if seller:
        seller.balance += withdrawal.amount
    
    withdrawal.status = "rejected"
    withdrawal.processed_at = datetime.utcnow()
    await session.commit()
    
    return {"message": "Withdrawal rejected, funds returned"}
