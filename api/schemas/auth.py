"""Authentication schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    """Request schema for Telegram authentication."""
    init_data: str = Field(..., description="Telegram initData string")


class UserProfile(BaseModel):
    """User profile embedded in auth response."""
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    balance: float
    referral_code: str
    language_code: str
    created_at: str


class AuthResponse(BaseModel):
    """Response schema for authentication."""
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
