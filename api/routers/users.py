"""User management router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.users import UserRepository
from app.models.entities import User
from api.dependencies.auth import get_current_user

router = APIRouter()


class UserProfileResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    balance: float
    referral_code: str
    language_code: str
    is_admin: bool
    is_seller: bool
    created_at: str


class UpdateProfileRequest(BaseModel):
    language_code: str | None = None


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get current user profile.
    
    **Validates Requirements 2.1**: Returns user ID, Telegram ID, username, balance, 
    referral code, language preference, and creation date.
    """
    from sqlalchemy import select
    from app.models import Admin, Seller
    
    # Check if user is admin
    result = await session.execute(
        select(Admin).where(Admin.user_id == current_user.id)
    )
    is_admin = result.scalar_one_or_none() is not None
    
    # Check if user is seller
    result = await session.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    is_seller = result.scalar_one_or_none() is not None
    
    return UserProfileResponse(
        id=current_user.id,
        telegram_id=current_user.telegram_id,
        username=current_user.username,
        first_name=current_user.first_name,
        balance=float(current_user.balance),
        referral_code=current_user.referral_code,
        language_code=current_user.language_code or "ru",
        is_admin=is_admin,
        is_seller=is_seller,
        created_at=current_user.created_at.isoformat()
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Update current user profile.
    
    **Validates Requirements 2.2**: Saves new language code and returns updated profile.
    """
    from sqlalchemy import select
    from app.models import Admin, Seller
    
    if request.language_code:
        current_user.language_code = request.language_code
    
    await session.commit()
    await session.refresh(current_user)
    
    # Check if user is admin
    result = await session.execute(
        select(Admin).where(Admin.user_id == current_user.id)
    )
    is_admin = result.scalar_one_or_none() is not None
    
    # Check if user is seller
    result = await session.execute(
        select(Seller).where(Seller.user_id == current_user.id)
    )
    is_seller = result.scalar_one_or_none() is not None
    
    return UserProfileResponse(
        id=current_user.id,
        telegram_id=current_user.telegram_id,
        username=current_user.username,
        first_name=current_user.first_name,
        balance=float(current_user.balance),
        referral_code=current_user.referral_code,
        language_code=current_user.language_code or "ru",
        is_admin=is_admin,
        is_seller=is_seller,
        created_at=current_user.created_at.isoformat()
    )


@router.get("/me/balance")
async def get_user_balance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get user balance.
    
    **Validates Requirements 2.3**: Returns current balance with two decimal precision.
    """
    return {
        "balance": float(current_user.balance),
        "currency": "RUB"
    }


@router.get("/me/transactions")
async def get_user_transactions(
    current_user: User = Depends(get_current_user),
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session)
):
    """Get user transaction history.
    
    **Validates Requirements 2.4**: Returns paginated list of transactions with type, 
    amount, status, and timestamp.
    """
    from sqlalchemy import select, func
    from app.models import Transaction
    
    if limit > 100:
        limit = 100
    
    offset = (page - 1) * limit
    
    # Get transactions
    result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    transactions = result.scalars().all()
    
    # Get total count
    result = await session.execute(
        select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
    )
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": tx.id,
                "type": tx.transaction_type.value,
                "amount": float(tx.amount),
                "currency": tx.currency_code,
                "status": tx.status.value,
                "description": tx.description,
                "created_at": tx.created_at.isoformat()
            }
            for tx in transactions
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/me/referrals")
async def get_user_referrals(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get referral stats.
    
    **Validates Requirements 14.5**: Returns count of invited users and total rewards earned.
    """
    from sqlalchemy import select, func
    from app.models import User as UserModel
    
    # Get total referrals count (Requirement 14.5)
    result = await session.execute(
        select(func.count(UserModel.id)).where(UserModel.referred_by_user_id == current_user.id)
    )
    total_referrals = result.scalar() or 0
    
    # Get total earned from referrals (from transactions) (Requirement 14.5)
    from app.models import Transaction
    from app.models.enums import TransactionType
    
    result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == TransactionType.REFERRAL_REWARD
        )
    )
    total_earned = float(result.scalar() or 0)
    
    return {
        "referral_code": current_user.referral_code,
        "total_referrals": total_referrals,
        "total_earned": total_earned
    }



@router.get("/me/favorites")
async def get_user_favorites(
    current_user: User = Depends(get_current_user),
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session)
):
    """Get user's favorite lots.
    
    **Validates Requirements 21.3**: Returns all favorited lots with current price and availability.
    """
    from sqlalchemy import select, func
    from app.models import Favorite, Lot, Seller, LotImage, MediaFile
    from sqlalchemy.orm import selectinload
    
    if limit > 100:
        limit = 100
    
    offset = (page - 1) * limit
    
    # Get favorites with lot details
    result = await session.execute(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    favorites = result.scalars().all()
    
    # Get total count
    result = await session.execute(
        select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    )
    total = result.scalar() or 0
    
    # Fetch lot details for each favorite
    lot_ids = [fav.lot_id for fav in favorites]
    
    if not lot_ids:
        return {
            "items": [],
            "total": total,
            "page": page,
            "limit": limit
        }
    
    # Get lots with seller and images
    lots_result = await session.execute(
        select(Lot)
        .where(Lot.id.in_(lot_ids))
        .options(
            selectinload(Lot.seller),
            selectinload(Lot.images).selectinload(LotImage.media)
        )
    )
    lots_dict = {lot.id: lot for lot in lots_result.scalars().all()}
    
    # Build response with lot details
    items = []
    for favorite in favorites:
        lot = lots_dict.get(favorite.lot_id)
        if not lot:
            continue
        
        # Get first image
        image_url = None
        if lot.images:
            sorted_images = sorted(lot.images, key=lambda img: img.sort_order)
            if sorted_images:
                image_url = sorted_images[0].media.url
        
        # Check availability
        is_available = (
            lot.status.value == "active" and 
            not lot.is_deleted and
            (lot.delivery_type.value == "manual" or lot.stock_count > 0)
        )
        
        items.append({
            "favorite_id": favorite.id,
            "lot_id": lot.id,
            "title": lot.title,
            "description": lot.description,
            "price": float(lot.price),
            "currency_code": lot.currency_code,
            "delivery_type": lot.delivery_type.value,
            "stock_count": lot.stock_count,
            "status": lot.status.value,
            "is_available": is_available,
            "image_url": image_url,
            "seller": {
                "id": lot.seller.id,
                "shop_name": lot.seller.shop_name,
                "rating": float(lot.seller.rating) if lot.seller.rating else 0.0
            },
            "favorited_at": favorite.created_at.isoformat()
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }
