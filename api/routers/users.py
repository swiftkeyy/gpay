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
    created_at: str


class UpdateProfileRequest(BaseModel):
    language_code: str | None = None


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user(
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Get current user profile."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        balance=float(user.balance),
        referral_code=user.referral_code,
        language_code=user.language_code,
        created_at=user.created_at.isoformat()
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_current_user(
    request: UpdateProfileRequest,
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Update current user profile."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.language_code:
        user.language_code = request.language_code
    
    await session.commit()
    await session.refresh(user)
    
    return UserProfileResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        balance=float(user.balance),
        referral_code=user.referral_code,
        language_code=user.language_code,
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
    # TODO: Implement transaction repository
    return {
        "items": [],
        "total": 0,
        "page": page,
        "limit": limit
    }


@router.get("/me/referrals")
async def get_referrals(
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Get referral stats."""
    # TODO: Implement referral repository
    return {
        "referral_code": "ABC123",
        "invited_users": 0,
        "total_rewards": 0.00
    }
