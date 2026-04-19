"""Seller management router."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.entities import User, Seller, Lot, Deal, Transaction
from api.dependencies.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models
class SellerApplicationRequest(BaseModel):
    shop_name: str = Field(..., min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)


class SellerProfileUpdate(BaseModel):
    shop_name: Optional[str] = Field(None, min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)


class LotCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., max_length=5000)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    game_id: int
    category_id: int
    product_id: int
    delivery_type: str = Field(..., pattern="^(auto|instant|manual)$")
    stock_quantity: Optional[int] = Field(None, ge=0)
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return round(v, 2)


class LotUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    delivery_type: Optional[str] = Field(None, pattern="^(auto|instant|manual)$")
    status: Optional[str] = Field(None, pattern="^(draft|active|out_of_stock|suspended)$")


class StockItemAdd(BaseModel):
    data: str = Field(..., max_length=10000)


class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: str = Field(..., pattern="^(card|qiwi|yoomoney|crypto)$")
    payment_details: str = Field(..., max_length=500)


class LotBoostRequest(BaseModel):
    duration_hours: int = Field(..., ge=1, le=168)  # 1 hour to 7 days


# Seller application
@router.post("/apply")
async def apply_to_become_seller(
    request: SellerApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply to become a seller."""
    # Check if already a seller
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    existing_seller = result.scalar_one_or_none()
    
    if existing_seller:
        if existing_seller.status == "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application already pending"
            )
        elif existing_seller.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already a seller"
            )
    
    # Create seller application
    new_seller = Seller(
        user_id=current_user.id,
        shop_name=request.shop_name,
        description=request.description,
        status="pending",
        is_verified=False,
        rating=0.0,
        total_sales=0,
        balance=Decimal("0.00")
    )
    db.add(new_seller)
    await db.commit()
    await db.refresh(new_seller)
    
    logger.info(f"Seller application created: user_id={current_user.id}, seller_id={new_seller.id}")
    
    return {
        "seller_id": new_seller.id,
        "status": "pending",
        "message": "Application submitted successfully"
    }


# Seller profile
@router.get("/me")
async def get_seller_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get seller profile."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    return {
        "id": seller.id,
        "shop_name": seller.shop_name,
        "description": seller.description,
        "status": seller.status,
        "is_verified": seller.is_verified,
        "rating": float(seller.rating),
        "total_sales": seller.total_sales,
        "balance": float(seller.balance),
        "created_at": seller.created_at.isoformat()
    }


@router.patch("/me")
async def update_seller_profile(
    request: SellerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update seller profile."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    if request.shop_name:
        seller.shop_name = request.shop_name
    if request.description is not None:
        seller.description = request.description
    
    await db.commit()
    await db.refresh(seller)
    
    return {
        "id": seller.id,
        "shop_name": seller.shop_name,
        "description": seller.description
    }


# Dashboard
@router.get("/me/dashboard")
async def get_seller_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get seller dashboard with stats."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    # Today stats
    result = await db.execute(
        select(
            func.count(Deal.id).label('sales'),
            func.coalesce(func.sum(Deal.seller_amount), 0).label('revenue')
        ).where(
            and_(
                Deal.seller_id == seller.id,
                Deal.status == 'completed',
                Deal.completed_at >= today_start
            )
        )
    )
    today_stats = result.one()
    
    # Week stats
    result = await db.execute(
        select(
            func.count(Deal.id).label('sales'),
            func.coalesce(func.sum(Deal.seller_amount), 0).label('revenue')
        ).where(
            and_(
                Deal.seller_id == seller.id,
                Deal.status == 'completed',
                Deal.completed_at >= week_start
            )
        )
    )
    week_stats = result.one()
    
    # Month stats
    result = await db.execute(
        select(
            func.count(Deal.id).label('sales'),
            func.coalesce(func.sum(Deal.seller_amount), 0).label('revenue')
        ).where(
            and_(
                Deal.seller_id == seller.id,
                Deal.status == 'completed',
                Deal.completed_at >= month_start
            )
        )
    )
    month_stats = result.one()
    
    # All time stats
    result = await db.execute(
        select(
            func.count(Deal.id).label('sales'),
            func.coalesce(func.sum(Deal.seller_amount), 0).label('revenue')
        ).where(
            and_(
                Deal.seller_id == seller.id,
                Deal.status == 'completed'
            )
        )
    )
    all_time_stats = result.one()
    
    # Active deals
    result = await db.execute(
        select(func.count(Deal.id)).where(
            and_(
                Deal.seller_id == seller.id,
                Deal.status.in_(['paid', 'in_progress', 'waiting_confirmation'])
            )
        )
    )
    active_deals = result.scalar()
    
    # Pending withdrawals
    result = await db.execute(
        select(func.coalesce(func.sum(Withdrawal.amount), 0)).where(
            and_(
                Withdrawal.seller_id == seller.id,
                Withdrawal.status == 'pending'
            )
        )
    )
    pending_withdrawals = result.scalar()
    
    return {
        "balance": {
            "available": float(seller.balance),
            "pending_withdrawals": float(pending_withdrawals),
            "in_escrow": 0.00  # TODO: calculate from active deals
        },
        "today": {
            "sales": today_stats.sales,
            "revenue": float(today_stats.revenue)
        },
        "week": {
            "sales": week_stats.sales,
            "revenue": float(week_stats.revenue)
        },
        "month": {
            "sales": month_stats.sales,
            "revenue": float(month_stats.revenue)
        },
        "all_time": {
            "sales": all_time_stats.sales,
            "revenue": float(all_time_stats.revenue)
        },
        "performance": {
            "rating": float(seller.rating),
            "total_sales": seller.total_sales,
            "active_deals": active_deals
        }
    }


# Lot management
@router.get("/me/lots")
async def get_seller_lots(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get seller lots."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    query = select(Lot).where(Lot.seller_id == seller.id)
    
    if status:
        query = query.where(Lot.status == status)
    
    query = query.order_by(Lot.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    lots = result.scalars().all()
    
    return {
        "items": [
            {
                "id": lot.id,
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


@router.post("/me/lots")
async def create_lot(
    request: LotCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new lot."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    if seller.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller account not active"
        )
    
    # Create lot
    new_lot = Lot(
        seller_id=seller.id,
        game_id=request.game_id,
        category_id=request.category_id,
        product_id=request.product_id,
        title=request.title,
        description=request.description,
        price=request.price,
        delivery_type=request.delivery_type,
        status="draft",
        views=0,
        sales=0,
        rating=0.0
    )
    db.add(new_lot)
    await db.commit()
    await db.refresh(new_lot)
    
    logger.info(f"Lot created: lot_id={new_lot.id}, seller_id={seller.id}")
    
    return {
        "lot_id": new_lot.id,
        "status": "draft",
        "message": "Lot created successfully"
    }


@router.patch("/me/lots/{lot_id}")
async def update_lot(
    lot_id: int,
    request: LotUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update lot."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    result = await db.execute(
        select(Lot).where(and_(Lot.id == lot_id, Lot.seller_id == seller.id))
    )
    lot = result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lot not found"
        )
    
    if request.title:
        lot.title = request.title
    if request.description:
        lot.description = request.description
    if request.price:
        lot.price = request.price
    if request.delivery_type:
        lot.delivery_type = request.delivery_type
    if request.status:
        lot.status = request.status
    
    await db.commit()
    await db.refresh(lot)
    
    return {
        "lot_id": lot.id,
        "message": "Lot updated successfully"
    }


@router.delete("/me/lots/{lot_id}")
async def delete_lot(
    lot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete lot (soft delete)."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    result = await db.execute(
        select(Lot).where(and_(Lot.id == lot_id, Lot.seller_id == seller.id))
    )
    lot = result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lot not found"
        )
    
    lot.status = "deleted"
    await db.commit()
    
    return {"message": "Lot deleted successfully"}


# Stock management
@router.post("/me/lots/{lot_id}/stock")
async def add_stock_items(
    lot_id: int,
    items: List[StockItemAdd],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add stock items for auto-delivery."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    result = await db.execute(
        select(Lot).where(and_(Lot.id == lot_id, Lot.seller_id == seller.id))
    )
    lot = result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lot not found"
        )
    
    if lot.delivery_type != "auto":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock items only for auto-delivery lots"
        )
    
    # Add stock items
    for item in items:
        stock_item = LotStockItem(
            lot_id=lot_id,
            data=item.data,
            is_sold=False
        )
        db.add(stock_item)
    
    # Update lot status
    if lot.status == "out_of_stock":
        lot.status = "active"
    
    await db.commit()
    
    return {
        "message": f"{len(items)} stock items added",
        "lot_status": lot.status
    }


# Lot boosting
@router.post("/me/lots/{lot_id}/boost")
async def boost_lot(
    lot_id: int,
    request: LotBoostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Boost lot to top of search results."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    result = await db.execute(
        select(Lot).where(and_(Lot.id == lot_id, Lot.seller_id == seller.id))
    )
    lot = result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lot not found"
        )
    
    # Calculate boost cost (e.g., 10 RUB per hour)
    boost_cost = Decimal(str(request.duration_hours * 10))
    
    if seller.balance < boost_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Deduct cost
    seller.balance -= boost_cost
    
    # Set boost expiration
    lot.boosted_until = datetime.utcnow() + timedelta(hours=request.duration_hours)
    
    # Create transaction
    transaction = Transaction(
        user_id=current_user.id,
        type="boost",
        amount=-boost_cost,
        description=f"Boost lot #{lot_id} for {request.duration_hours} hours"
    )
    db.add(transaction)
    
    await db.commit()
    
    return {
        "message": "Lot boosted successfully",
        "boosted_until": lot.boosted_until.isoformat(),
        "cost": float(boost_cost),
        "new_balance": float(seller.balance)
    }


# Withdrawals
@router.post("/me/withdrawals")
async def request_withdrawal(
    request: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request withdrawal."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    if seller.balance < request.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Minimum withdrawal amount
    if request.amount < Decimal("100.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum withdrawal amount is 100 RUB"
        )
    
    # Deduct amount
    seller.balance -= request.amount
    
    # Create withdrawal
    withdrawal = Withdrawal(
        seller_id=seller.id,
        amount=request.amount,
        payment_method=request.payment_method,
        payment_details=request.payment_details,
        status="pending"
    )
    db.add(withdrawal)
    
    await db.commit()
    await db.refresh(withdrawal)
    
    logger.info(f"Withdrawal requested: withdrawal_id={withdrawal.id}, seller_id={seller.id}, amount={request.amount}")
    
    return {
        "withdrawal_id": withdrawal.id,
        "amount": float(request.amount),
        "status": "pending",
        "message": "Withdrawal request submitted"
    }


@router.get("/me/withdrawals")
async def get_withdrawals(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get withdrawal history."""
    result = await db.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a seller"
        )
    
    result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.seller_id == seller.id)
        .order_by(Withdrawal.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    withdrawals = result.scalars().all()
    
    return {
        "items": [
            {
                "id": w.id,
                "amount": float(w.amount),
                "payment_method": w.payment_method,
                "status": w.status,
                "created_at": w.created_at.isoformat(),
                "processed_at": w.processed_at.isoformat() if w.processed_at else None
            }
            for w in withdrawals
        ],
        "total": len(withdrawals),
        "skip": skip,
        "limit": limit
    }
