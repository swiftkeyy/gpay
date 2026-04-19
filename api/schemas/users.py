"""User management schemas."""
from __future__ import annotations

from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    """User profile response."""
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
    """Request to update user profile."""
    language_code: str | None = Field(None, min_length=2, max_length=10)


class BalanceResponse(BaseModel):
    """User balance response."""
    balance: float
    currency: str = "RUB"


class TransactionResponse(BaseModel):
    """Single transaction response."""
    id: int
    type: str
    amount: float
    currency: str
    status: str
    description: str | None
    created_at: str


class TransactionListResponse(BaseModel):
    """Paginated transaction list response."""
    items: List[TransactionResponse]
    total: int
    page: int
    limit: int


class ReferralStatsResponse(BaseModel):
    """Referral statistics response."""
    referral_code: str
    total_referrals: int
    total_earned: float
