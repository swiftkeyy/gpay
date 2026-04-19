"""User management router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.users import UserRepository

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
async def get_current_user(
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Get current user profile."""
    from sqlalchemy import select
    from app.models import Admin, Seller
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is admin
    result = await session.execute(
        select(Admin).where(Admin.user_id == user_id)
    )
    is_admin = result.scalar_one_or_none() is not None
    
    # Check if user is seller
    result = await session.execute(
        select(Seller).where(Seller.user_id == user_id)
    )
    is_seller = result.scalar_one_or_none() is not None
    
    return UserProfileResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        balance=float(user.balance),
        referral_code=user.referral_code,
        language_code=user.language_code or "ru",
        is_admin=is_admin,
        is_seller=is_seller,
        created_at=user.created_at.isoformat()
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_current_user(
    request: UpdateProfileRequest,
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Update current user profile."""
    from sqlalchemy import select
    from app.models import Admin, Seller
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.language_code:
        user.language_code = request.language_code
    
    await session.commit()
    await session.refresh(user)
    
    # Check if user is admin
    result = await session.execute(
        select(Admin).where(Admin.user_id == user_id)
    )
    is_admin = result.scalar_one_or_none() is not None
    
    # Check if user is seller
    result = await session.execute(
        select(Seller).where(Seller.user_id == user_id)
    )
    is_seller = result.scalar_one_or_none() is not None
    
    return UserProfileResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        balance=float(user.balance),
        referral_code=user.referral_code,
        language_code=user.language_code or "ru",
        is_admin=is_admin,
        is_seller=is_seller,
        created_at=user.created_at.isoformat()
    )


@router.get("/me/balance")
async def get_balance(
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Get user balance."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"balance": float(user.balance), "currency": "RUB"}


@router.get("/me/transactions")
async def get_transactions(
    user_id: int = 1,  # TODO: Extract from auth token
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session)
):
    """Get user transaction history."""
    from sqlalchemy import select, func
    from app.models import Transaction
    
    if limit > 100:
        limit = 100
    
    offset = (page - 1) * limit
    
    # Get transactions
    result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    transactions = result.scalars().all()
    
    # Get total count
    result = await session.execute(
        select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
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
async def get_referrals(
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Get referral stats."""
    from sqlalchemy import select, func
    from app.models import User
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get total referrals count
    result = await session.execute(
        select(func.count(User.id)).where(User.referred_by_id == user_id)
    )
    total_referrals = result.scalar() or 0
    
    # Get total earned from referrals (from transactions)
    from app.models import Transaction
    from app.models.enums import TransactionType
    
    result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.REFERRAL_REWARD
        )
    )
    total_earned = float(result.scalar() or 0)
    
    return {
        "referral_code": user.referral_code,
        "total_referrals": total_referrals,
        "total_earned": total_earned
    }
