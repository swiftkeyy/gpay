"""Admin panel router."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.entities import (
    User, Admin, Seller, Lot, Deal, DealDispute, DealMessage, SellerWithdrawal, Order,
    PromoCode, PromoCodeUsage, Game, Product, Transaction
)
from app.models.enums import DealStatus
from api.schemas.admin import SellerApprovalRequest
from api.services.cache import get_cache_service

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
    start_date: datetime | None = Query(None, description="Start date for stats (default: all time)"),
    end_date: datetime | None = Query(None, description="End date for stats (default: now)"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get admin dashboard stats with optional date range filtering."""
    await require_admin(user_id, session)
    
    # Set default date range if not provided
    if end_date is None:
        end_date = datetime.utcnow()
    
    # Check cache first (only for all-time stats without date filter)
    cache_service = get_cache_service()
    if start_date is None:
        cache_key = "admin:dashboard:all_time"
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            return cached_data
    
    # Build date filter condition
    date_filter = True
    if start_date:
        date_filter = and_(
            Deal.created_at >= start_date,
            Deal.created_at <= end_date
        )
    
    # Total users
    result = await session.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0
    
    # Total sellers
    result = await session.execute(select(func.count(Seller.id)))
    total_sellers = result.scalar() or 0
    
    # Active sellers (sellers with at least one completed deal in the period)
    if start_date:
        result = await session.execute(
            select(func.count(func.distinct(Deal.seller_id)))
            .where(
                and_(
                    Deal.status == DealStatus.COMPLETED,
                    Deal.created_at >= start_date,
                    Deal.created_at <= end_date
                )
            )
        )
    else:
        result = await session.execute(
            select(func.count(func.distinct(Deal.seller_id)))
            .where(Deal.status == DealStatus.COMPLETED)
        )
    active_sellers = result.scalar() or 0
    
    # Total lots
    result = await session.execute(select(func.count(Lot.id)))
    total_lots = result.scalar() or 0
    
    # Active lots
    result = await session.execute(
        select(func.count(Lot.id)).where(Lot.status == "active")
    )
    active_lots = result.scalar() or 0
    
    # Total orders (with date filter if provided)
    if start_date:
        result = await session.execute(
            select(func.count(Order.id))
            .where(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
        )
    else:
        result = await session.execute(select(func.count(Order.id)))
    total_orders = result.scalar() or 0
    
    # Total deals (with date filter)
    if start_date:
        result = await session.execute(
            select(func.count(Deal.id))
            .where(
                and_(
                    Deal.created_at >= start_date,
                    Deal.created_at <= end_date
                )
            )
        )
    else:
        result = await session.execute(select(func.count(Deal.id)))
    total_deals = result.scalar() or 0
    
    # Completed deals (with date filter)
    if start_date:
        result = await session.execute(
            select(func.count(Deal.id))
            .where(
                and_(
                    Deal.status == DealStatus.COMPLETED,
                    Deal.created_at >= start_date,
                    Deal.created_at <= end_date
                )
            )
        )
    else:
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
    
    # Total revenue (commission) with date filter
    if start_date:
        result = await session.execute(
            select(func.coalesce(func.sum(Deal.commission_amount), 0))
            .where(
                and_(
                    Deal.status == DealStatus.COMPLETED,
                    Deal.created_at >= start_date,
                    Deal.created_at <= end_date
                )
            )
        )
    else:
        result = await session.execute(
            select(func.coalesce(func.sum(Deal.commission_amount), 0)).where(
                Deal.status == DealStatus.COMPLETED
            )
        )
    total_revenue = result.scalar() or 0
    
    response = {
        "date_range": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat()
        },
        "users": {
            "total": total_users,
            "sellers": total_sellers,
            "active_sellers": active_sellers
        },
        "lots": {
            "total": total_lots,
            "active": active_lots
        },
        "orders": {
            "total": total_orders
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
    
    # Cache for 15 minutes (only for all-time stats)
    if start_date is None:
        await cache_service.set(cache_key, response, ttl=900)
    
    return response


# Revenue Analytics
@router.get("/revenue-analytics")
async def get_revenue_analytics(
    user_id: int = 1,
    group_by: Literal["day", "week", "month"] = Query("day", description="Group revenue by day, week, or month"),
    start_date: datetime | None = Query(None, description="Start date for analytics (default: 30 days ago)"),
    end_date: datetime | None = Query(None, description="End date for analytics (default: now)"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get revenue analytics grouped by date."""
    await require_admin(user_id, session)
    
    # Set default date range if not provided
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Check cache first
    cache_service = get_cache_service()
    cache_key = f"admin:revenue_analytics:{group_by}:{start_date.date()}:{end_date.date()}"
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    # Determine date truncation based on group_by
    if group_by == "day":
        date_trunc = func.date_trunc('day', Deal.created_at)
    elif group_by == "week":
        date_trunc = func.date_trunc('week', Deal.created_at)
    else:  # month
        date_trunc = func.date_trunc('month', Deal.created_at)
    
    # Query revenue grouped by date
    result = await session.execute(
        select(
            date_trunc.label('period'),
            func.count(Deal.id).label('deal_count'),
            func.sum(Deal.amount).label('total_amount'),
            func.sum(Deal.commission_amount).label('total_commission')
        )
        .where(
            and_(
                Deal.status == DealStatus.COMPLETED,
                Deal.created_at >= start_date,
                Deal.created_at <= end_date
            )
        )
        .group_by('period')
        .order_by('period')
    )
    
    analytics_data = []
    for row in result:
        analytics_data.append({
            "period": row.period.isoformat() if row.period else None,
            "deal_count": row.deal_count or 0,
            "total_amount": float(row.total_amount or 0),
            "total_commission": float(row.total_commission or 0)
        })
    
    response = {
        "group_by": group_by,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "data": analytics_data
    }
    
    # Cache for 15 minutes
    await cache_service.set(cache_key, response, ttl=900)
    
    return response


# Top Sellers
@router.get("/top-sellers")
async def get_top_sellers(
    user_id: int = 1,
    limit: int = Query(10, ge=1, le=100, description="Number of top sellers to return"),
    start_date: datetime | None = Query(None, description="Start date for ranking (default: 30 days ago)"),
    end_date: datetime | None = Query(None, description="End date for ranking (default: now)"),
    rank_by: Literal["sales_count", "revenue"] = Query("revenue", description="Rank by sales count or revenue"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get top sellers ranked by sales count or revenue."""
    await require_admin(user_id, session)
    
    # Set default date range if not provided
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Check cache first
    cache_service = get_cache_service()
    cache_key = f"admin:top_sellers:{rank_by}:{limit}:{start_date.date()}:{end_date.date()}"
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    # Determine ranking metric
    if rank_by == "sales_count":
        rank_metric = func.count(Deal.id).label('metric')
    else:  # revenue
        rank_metric = func.sum(Deal.seller_amount).label('metric')
    
    # Query top sellers
    result = await session.execute(
        select(
            Seller.id,
            Seller.shop_name,
            Seller.rating,
            User.username,
            func.count(Deal.id).label('sales_count'),
            func.sum(Deal.seller_amount).label('total_revenue')
        )
        .join(Deal, Deal.seller_id == Seller.id)
        .join(User, User.id == Seller.user_id)
        .where(
            and_(
                Deal.status == DealStatus.COMPLETED,
                Deal.created_at >= start_date,
                Deal.created_at <= end_date
            )
        )
        .group_by(Seller.id, Seller.shop_name, Seller.rating, User.username)
        .order_by(desc(rank_metric))
        .limit(limit)
    )
    
    top_sellers = []
    for row in result:
        top_sellers.append({
            "seller_id": row.id,
            "shop_name": row.shop_name,
            "username": row.username,
            "rating": float(row.rating or 0),
            "sales_count": row.sales_count or 0,
            "total_revenue": float(row.total_revenue or 0)
        })
    
    response = {
        "rank_by": rank_by,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "limit": limit,
        "sellers": top_sellers
    }
    
    # Cache for 15 minutes
    await cache_service.set(cache_key, response, ttl=900)
    
    return response


# Top Products
@router.get("/top-products")
async def get_top_products(
    user_id: int = 1,
    limit: int = Query(10, ge=1, le=100, description="Number of top products to return"),
    start_date: datetime | None = Query(None, description="Start date for ranking (default: 30 days ago)"),
    end_date: datetime | None = Query(None, description="End date for ranking (default: now)"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get top products ranked by sales count."""
    await require_admin(user_id, session)
    
    # Set default date range if not provided
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Check cache first
    cache_service = get_cache_service()
    cache_key = f"admin:top_products:{limit}:{start_date.date()}:{end_date.date()}"
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    # Query top products (via lots)
    result = await session.execute(
        select(
            Lot.product_id,
            Product.name,
            Game.name.label('game_name'),
            func.count(Deal.id).label('sales_count'),
            func.sum(Deal.amount).label('total_revenue')
        )
        .join(Deal, Deal.lot_id == Lot.id)
        .join(Product, Product.id == Lot.product_id)
        .join(Game, Game.id == Product.game_id)
        .where(
            and_(
                Deal.status == DealStatus.COMPLETED,
                Deal.created_at >= start_date,
                Deal.created_at <= end_date,
                Lot.product_id.isnot(None)
            )
        )
        .group_by(Lot.product_id, Product.name, Game.name)
        .order_by(desc(func.count(Deal.id)))
        .limit(limit)
    )
    
    top_products = []
    for row in result:
        top_products.append({
            "product_id": row.product_id,
            "product_name": row.name,
            "game_name": row.game_name,
            "sales_count": row.sales_count or 0,
            "total_revenue": float(row.total_revenue or 0)
        })
    
    response = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "limit": limit,
        "products": top_products
    }
    
    # Cache for 15 minutes
    await cache_service.set(cache_key, response, ttl=900)
    
    return response


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
                "status": seller.status.value,
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
    """Approve seller application.
    
    Requirements: 3.2, 3.3
    - Updates seller status to active
    - Sets is_verified flag to true
    - Sets verified_at timestamp
    - Sends notification to user
    """
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(Seller).options(selectinload(Seller.user)).where(Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    if seller.status == "active":
        raise HTTPException(status_code=400, detail="Seller already approved")
    
    # Update seller status and verification
    seller.status = "active"
    seller.is_verified = True
    seller.verified_at = datetime.utcnow()
    
    # Create notification for user
    from app.models.entities import Notification
    from app.models.enums import NotificationType
    
    notification = Notification(
        user_id=seller.user_id,
        notification_type=NotificationType.SELLER_APPROVED,
        title="Seller Application Approved",
        message=f"Congratulations! Your seller application for '{seller.shop_name}' has been approved. You can now start creating listings.",
        reference_type="seller",
        reference_id=seller.id
    )
    session.add(notification)
    
    await session.commit()
    
    return {
        "message": "Seller approved",
        "seller_id": seller.id,
        "status": "active",
        "is_verified": True
    }


@router.post("/sellers/{seller_id}/reject")
async def reject_seller(
    seller_id: int,
    rejection_reason: str | None = None,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Reject seller application.
    
    Requirements: 3.2, 3.4
    - Updates seller status to rejected
    - Sends notification to user with rejection reason
    """
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(Seller).options(selectinload(Seller.user)).where(Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    if seller.status == "rejected":
        raise HTTPException(status_code=400, detail="Seller already rejected")
    
    # Update seller status
    seller.status = "rejected"
    
    # Create notification for user
    from app.models.entities import Notification
    from app.models.enums import NotificationType
    
    message = f"Your seller application for '{seller.shop_name}' has been rejected."
    if rejection_reason:
        message += f"\n\nReason: {rejection_reason}"
    
    notification = Notification(
        user_id=seller.user_id,
        notification_type=NotificationType.SELLER_REJECTED,
        title="Seller Application Rejected",
        message=message,
        reference_type="seller",
        reference_id=seller.id
    )
    session.add(notification)
    
    await session.commit()
    
    return {
        "message": "Seller rejected",
        "seller_id": seller.id,
        "status": "rejected"
    }


@router.patch("/sellers/{seller_id}")
async def update_seller_status(
    seller_id: int,
    request: SellerApprovalRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Update seller status (approve/reject/suspend).
    
    Requirements: 3.2, 3.3, 3.4, 3.5
    - Updates seller status and verified flag
    - Sends notification to user
    - Supports approval, rejection, and suspension
    """
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(Seller).options(selectinload(Seller.user)).where(Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    old_status = seller.status
    new_status = request.status
    
    # Update seller status
    seller.status = new_status
    
    # Handle approval
    if new_status == "active" and old_status != "active":
        seller.is_verified = True
        seller.verified_at = datetime.utcnow()
        
        # Create notification
        from app.models.entities import Notification
        from app.models.enums import NotificationType
        
        notification = Notification(
            user_id=seller.user_id,
            notification_type=NotificationType.SELLER_APPROVED,
            title="Seller Application Approved",
            message=f"Congratulations! Your seller application for '{seller.shop_name}' has been approved. You can now start creating listings.",
            reference_type="seller",
            reference_id=seller.id
        )
        session.add(notification)
    
    # Handle rejection
    elif new_status == "rejected":
        from app.models.entities import Notification
        from app.models.enums import NotificationType
        
        message = f"Your seller application for '{seller.shop_name}' has been rejected."
        if request.rejection_reason:
            message += f"\n\nReason: {request.rejection_reason}"
        
        notification = Notification(
            user_id=seller.user_id,
            notification_type=NotificationType.SELLER_REJECTED,
            title="Seller Application Rejected",
            message=message,
            reference_type="seller",
            reference_id=seller.id
        )
        session.add(notification)
    
    # Handle suspension
    elif new_status == "suspended":
        from app.models.entities import Notification
        from app.models.enums import NotificationType
        
        message = f"Your seller account '{seller.shop_name}' has been suspended."
        if request.rejection_reason:
            message += f"\n\nReason: {request.rejection_reason}"
        
        notification = Notification(
            user_id=seller.user_id,
            notification_type=NotificationType.SYSTEM,
            title="Seller Account Suspended",
            message=message,
            reference_type="seller",
            reference_id=seller.id
        )
        session.add(notification)
    
    await session.commit()
    
    return {
        "message": f"Seller status updated to {new_status}",
        "seller_id": seller.id,
        "status": seller.status,
        "is_verified": seller.is_verified
    }


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
                "status": lot.status.value,
                "stock_count": lot.stock_count,
                "sold_count": lot.sold_count,
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
                "status": withdrawal.status.value,
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
    """Approve withdrawal and mark as completed.
    
    Requirements: 13.4
    - Updates withdrawal status to completed
    - Updates transaction status to completed
    - Records admin who processed it
    """
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(SellerWithdrawal).where(SellerWithdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="Withdrawal is not pending")
    
    # Update withdrawal status
    withdrawal.status = "completed"
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.processed_by_admin_id = user_id
    
    # Update associated transaction status
    result = await session.execute(
        select(Transaction).where(
            and_(
                Transaction.reference_type == "withdrawal",
                Transaction.reference_id == withdrawal_id
            )
        )
    )
    transaction = result.scalar_one_or_none()
    
    if transaction:
        from app.models.enums import TransactionStatus
        transaction.status = TransactionStatus.COMPLETED
    
    await session.commit()
    
    return {"message": "Withdrawal approved"}


@router.post("/withdrawals/{withdrawal_id}/reject")
async def reject_withdrawal(
    withdrawal_id: int,
    rejection_reason: str | None = None,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Reject withdrawal and refund amount to seller balance.
    
    Requirements: 13.4, 13.5
    - Updates withdrawal status to rejected
    - Refunds amount to seller balance
    - Updates transaction status to failed
    - Creates refund transaction record
    """
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(SellerWithdrawal).where(SellerWithdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="Withdrawal is not pending")
    
    # Requirement 13.5: Refund amount to seller balance
    result = await session.execute(
        select(Seller).where(Seller.id == withdrawal.seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if seller:
        balance_before = seller.balance
        seller.balance += withdrawal.amount
        balance_after = seller.balance
        
        # Create refund transaction record
        from app.models.enums import TransactionType, TransactionStatus
        
        refund_transaction = Transaction(
            user_id=seller.user_id,
            transaction_type=TransactionType.REFUND,
            amount=withdrawal.amount,  # Positive because it's returning to account
            currency_code=withdrawal.currency_code,
            status=TransactionStatus.COMPLETED,
            balance_before=balance_before,
            balance_after=balance_after,
            description=f"Withdrawal #{withdrawal_id} rejected - refund",
            reference_type="withdrawal",
            reference_id=withdrawal_id,
            metadata_json={
                "withdrawal_id": withdrawal_id,
                "rejection_reason": rejection_reason,
                "original_amount": float(withdrawal.amount)
            }
        )
        session.add(refund_transaction)
    
    # Update withdrawal status
    withdrawal.status = "rejected"
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.processed_by_admin_id = user_id
    withdrawal.rejection_reason = rejection_reason
    
    # Update original withdrawal transaction status to failed
    result = await session.execute(
        select(Transaction).where(
            and_(
                Transaction.reference_type == "withdrawal",
                Transaction.reference_id == withdrawal_id,
                Transaction.transaction_type == TransactionType.WITHDRAWAL
            )
        )
    )
    original_transaction = result.scalar_one_or_none()
    
    if original_transaction:
        from app.models.enums import TransactionStatus
        original_transaction.status = TransactionStatus.FAILED
    
    await session.commit()
    
    return {"message": "Withdrawal rejected, funds returned"}


# Disputes management
@router.get("/disputes")
async def get_disputes(
    user_id: int = 1,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get disputes list.
    
    Validates: Requirement 10.4
    - Provide access to deal details, chat history, and user information
    """
    await require_admin(user_id, session)
    
    offset = (page - 1) * limit
    
    query = select(DealDispute).options(
        selectinload(DealDispute.deal).selectinload(Deal.buyer),
        selectinload(DealDispute.deal).selectinload(Deal.seller).selectinload(Seller.user),
        selectinload(DealDispute.initiator)
    )
    
    if status:
        from app.models.enums import DisputeStatus
        query = query.where(DealDispute.status == status)
    
    query = query.order_by(DealDispute.created_at.desc()).offset(offset).limit(limit)
    
    result = await session.execute(query)
    disputes = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(DealDispute.id))
    if status:
        from app.models.enums import DisputeStatus
        count_query = count_query.where(DealDispute.status == status)
    
    result = await session.execute(count_query)
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": dispute.id,
                "deal_id": dispute.deal_id,
                "deal_amount": float(dispute.deal.amount) if dispute.deal else 0,
                "buyer_username": dispute.deal.buyer.username if dispute.deal and dispute.deal.buyer else "Unknown",
                "seller_username": dispute.deal.seller.user.username if dispute.deal and dispute.deal.seller and dispute.deal.seller.user else "Unknown",
                "initiator_username": dispute.initiator.username if dispute.initiator else "Unknown",
                "reason": dispute.reason,
                "status": dispute.status.value,
                "created_at": dispute.created_at.isoformat(),
                "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None
            }
            for dispute in disputes
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/disputes/{dispute_id}")
async def get_dispute_details(
    dispute_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Get dispute details with deal info and chat history.
    
    Validates: Requirement 10.4
    - Provide access to deal details, chat history, and user information
    """
    await require_admin(user_id, session)
    
    # Get dispute with all related data
    result = await session.execute(
        select(DealDispute)
        .options(
            selectinload(DealDispute.deal).selectinload(Deal.buyer),
            selectinload(DealDispute.deal).selectinload(Deal.seller).selectinload(Seller.user),
            selectinload(DealDispute.deal).selectinload(Deal.lot),
            selectinload(DealDispute.deal).selectinload(Deal.messages).selectinload(DealMessage.sender),
            selectinload(DealDispute.initiator)
        )
        .where(DealDispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    deal = dispute.deal
    
    # Get chat messages
    from app.models.entities import DealMessage
    result = await session.execute(
        select(DealMessage)
        .options(selectinload(DealMessage.sender))
        .where(DealMessage.deal_id == deal.id)
        .order_by(DealMessage.created_at.asc())
    )
    messages = result.scalars().all()
    
    return {
        "dispute": {
            "id": dispute.id,
            "reason": dispute.reason,
            "description": dispute.description,
            "status": dispute.status.value,
            "resolution": dispute.resolution,
            "admin_comment": dispute.admin_comment,
            "created_at": dispute.created_at.isoformat(),
            "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None
        },
        "deal": {
            "id": deal.id,
            "status": deal.status.value,
            "amount": float(deal.amount),
            "commission_amount": float(deal.commission_amount),
            "seller_amount": float(deal.seller_amount),
            "escrow_released": deal.escrow_released,
            "created_at": deal.created_at.isoformat(),
            "delivered_at": deal.delivered_at.isoformat() if deal.delivered_at else None,
            "completed_at": deal.completed_at.isoformat() if deal.completed_at else None
        },
        "buyer": {
            "id": deal.buyer.id,
            "username": deal.buyer.username,
            "first_name": deal.buyer.first_name,
            "telegram_id": deal.buyer.telegram_id,
            "balance": float(deal.buyer.balance),
            "is_blocked": deal.buyer.is_blocked
        },
        "seller": {
            "id": deal.seller.id,
            "user_id": deal.seller.user_id,
            "username": deal.seller.user.username if deal.seller.user else None,
            "shop_name": deal.seller.shop_name,
            "rating": float(deal.seller.rating),
            "total_sales": deal.seller.total_sales,
            "balance": float(deal.seller.balance)
        },
        "lot": {
            "id": deal.lot.id,
            "title": deal.lot.title,
            "price": float(deal.lot.price)
        },
        "chat_history": [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "sender_username": msg.sender.username if msg.sender else "Unknown",
                "message_text": msg.message_text,
                "is_system": msg.is_system,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "initiator": {
            "id": dispute.initiator.id,
            "username": dispute.initiator.username,
            "first_name": dispute.initiator.first_name
        }
    }


# Promo Codes management
@router.get("/promo-codes")
async def get_promo_codes(
    user_id: int = 1,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get promo codes list with filters.
    
    Validates: Requirement 15 (Admin promo code management)
    - List all promo codes with pagination
    - Filter by active status
    - Show usage statistics
    """
    await require_admin(user_id, session)
    
    offset = (page - 1) * limit
    
    query = select(PromoCode).where(PromoCode.is_deleted == False)
    
    if is_active is not None:
        query = query.where(PromoCode.is_active == is_active)
    
    query = query.order_by(PromoCode.created_at.desc()).offset(offset).limit(limit)
    
    result = await session.execute(query)
    promo_codes = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(PromoCode.id)).where(PromoCode.is_deleted == False)
    if is_active is not None:
        count_query = count_query.where(PromoCode.is_active == is_active)
    
    result = await session.execute(count_query)
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": promo.id,
                "code": promo.code,
                "promo_type": promo.promo_type.value,
                "value": float(promo.value),
                "max_usages": promo.max_usages,
                "used_count": promo.used_count,
                "starts_at": promo.starts_at.isoformat() if promo.starts_at else None,
                "ends_at": promo.ends_at.isoformat() if promo.ends_at else None,
                "is_active": promo.is_active,
                "only_new_users": promo.only_new_users,
                "game_id": promo.game_id,
                "product_id": promo.product_id,
                "created_at": promo.created_at.isoformat()
            }
            for promo in promo_codes
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/promo-codes/{promo_id}")
async def get_promo_code(
    promo_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Get promo code details.
    
    Validates: Requirement 15 (Admin promo code management)
    - Get detailed promo code information
    - Show usage history
    """
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(PromoCode).where(
            and_(
                PromoCode.id == promo_id,
                PromoCode.is_deleted == False
            )
        )
    )
    promo = result.scalar_one_or_none()
    
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    # Get usage history
    result = await session.execute(
        select(PromoCodeUsage)
        .options(selectinload(PromoCodeUsage.user))
        .where(PromoCodeUsage.promo_code_id == promo_id)
        .order_by(PromoCodeUsage.created_at.desc())
        .limit(50)
    )
    usages = result.scalars().all()
    
    return {
        "id": promo.id,
        "code": promo.code,
        "promo_type": promo.promo_type.value,
        "value": float(promo.value),
        "max_usages": promo.max_usages,
        "used_count": promo.used_count,
        "starts_at": promo.starts_at.isoformat() if promo.starts_at else None,
        "ends_at": promo.ends_at.isoformat() if promo.ends_at else None,
        "is_active": promo.is_active,
        "only_new_users": promo.only_new_users,
        "game_id": promo.game_id,
        "product_id": promo.product_id,
        "created_at": promo.created_at.isoformat(),
        "updated_at": promo.updated_at.isoformat(),
        "usage_history": [
            {
                "id": usage.id,
                "user_id": usage.user_id,
                "username": usage.user.username if usage.user else None,
                "order_id": usage.order_id,
                "created_at": usage.created_at.isoformat()
            }
            for usage in usages
        ]
    }


class CreatePromoCodeRequest(BaseModel):
    code: str
    promo_type: str  # "percent" or "fixed"
    value: Decimal
    max_usages: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    game_id: int | None = None
    product_id: int | None = None
    only_new_users: bool = False
    is_active: bool = True


@router.post("/promo-codes")
async def create_promo_code(
    request: CreatePromoCodeRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Create new promo code.
    
    Validates: Requirement 15 (Admin promo code management)
    - Create promo code with validation
    - Set expiration dates, usage limits, and eligibility rules
    - Support percentage and fixed amount discounts
    """
    await require_admin(user_id, session)
    
    # Validate promo type
    from app.models.enums import PromoType
    
    try:
        promo_type_enum = PromoType(request.promo_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid promo type. Must be 'percent' or 'fixed'"
        )
    
    # Validate value
    if request.value <= 0:
        raise HTTPException(status_code=400, detail="Value must be positive")
    
    if promo_type_enum == PromoType.PERCENT and request.value > 100:
        raise HTTPException(status_code=400, detail="Percentage value cannot exceed 100")
    
    # Validate code format (uppercase, alphanumeric)
    code_upper = request.code.upper().strip()
    if not code_upper or len(code_upper) < 3 or len(code_upper) > 64:
        raise HTTPException(
            status_code=400,
            detail="Code must be between 3 and 64 characters"
        )
    
    # Check if code already exists
    result = await session.execute(
        select(PromoCode).where(
            and_(
                PromoCode.code == code_upper,
                PromoCode.is_deleted == False
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Promo code already exists")
    
    # Validate dates
    if request.starts_at and request.ends_at and request.starts_at >= request.ends_at:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before end date"
        )
    
    # Validate game_id if provided
    if request.game_id:
        result = await session.execute(
            select(Game).where(Game.id == request.game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
    
    # Validate product_id if provided
    if request.product_id:
        result = await session.execute(
            select(Product).where(Product.id == request.product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    
    # Create promo code
    promo = PromoCode(
        code=code_upper,
        promo_type=promo_type_enum,
        value=request.value,
        max_usages=request.max_usages,
        starts_at=request.starts_at,
        ends_at=request.ends_at,
        game_id=request.game_id,
        product_id=request.product_id,
        only_new_users=request.only_new_users,
        is_active=request.is_active
    )
    session.add(promo)
    await session.commit()
    await session.refresh(promo)
    
    return {
        "message": "Promo code created",
        "promo_code": {
            "id": promo.id,
            "code": promo.code,
            "promo_type": promo.promo_type.value,
            "value": float(promo.value),
            "max_usages": promo.max_usages,
            "is_active": promo.is_active
        }
    }


class UpdatePromoCodeRequest(BaseModel):
    value: Decimal | None = None
    max_usages: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None


@router.patch("/promo-codes/{promo_id}")
async def update_promo_code(
    promo_id: int,
    request: UpdatePromoCodeRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Update promo code.
    
    Validates: Requirement 15 (Admin promo code management)
    - Update promo code settings
    - Modify expiration dates, usage limits
    - Activate/deactivate promo codes
    """
    await require_admin(user_id, session)
    
    from app.models.enums import PromoType
    
    result = await session.execute(
        select(PromoCode).where(
            and_(
                PromoCode.id == promo_id,
                PromoCode.is_deleted == False
            )
        )
    )
    promo = result.scalar_one_or_none()
    
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    # Update fields if provided
    if request.value is not None:
        if request.value <= 0:
            raise HTTPException(status_code=400, detail="Value must be positive")
        
        if promo.promo_type == PromoType.PERCENT and request.value > 100:
            raise HTTPException(
                status_code=400,
                detail="Percentage value cannot exceed 100"
            )
        
        promo.value = request.value
    
    if request.max_usages is not None:
        promo.max_usages = request.max_usages
    
    if request.starts_at is not None:
        promo.starts_at = request.starts_at
    
    if request.ends_at is not None:
        promo.ends_at = request.ends_at
    
    # Validate dates if both are set
    if promo.starts_at and promo.ends_at and promo.starts_at >= promo.ends_at:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before end date"
        )
    
    if request.is_active is not None:
        promo.is_active = request.is_active
    
    promo.updated_at = datetime.utcnow()
    
    await session.commit()
    
    return {
        "message": "Promo code updated",
        "promo_code": {
            "id": promo.id,
            "code": promo.code,
            "promo_type": promo.promo_type.value,
            "value": float(promo.value),
            "max_usages": promo.max_usages,
            "is_active": promo.is_active,
            "starts_at": promo.starts_at.isoformat() if promo.starts_at else None,
            "ends_at": promo.ends_at.isoformat() if promo.ends_at else None
        }
    }


@router.delete("/promo-codes/{promo_id}")
async def delete_promo_code(
    promo_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Soft delete (deactivate) promo code.
    
    Validates: Requirement 15 (Admin promo code management)
    - Deactivate promo code (soft delete)
    - Preserve usage history
    """
    await require_admin(user_id, session)
    
    result = await session.execute(
        select(PromoCode).where(
            and_(
                PromoCode.id == promo_id,
                PromoCode.is_deleted == False
            )
        )
    )
    promo = result.scalar_one_or_none()
    
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    # Soft delete
    promo.is_deleted = True
    promo.is_active = False
    promo.updated_at = datetime.utcnow()
    
    await session.commit()
    
    return {"message": "Promo code deleted"}
