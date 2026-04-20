"""Authentication router for Telegram Mini App.

This router handles Telegram authentication endpoints using the AuthService
for secure initData validation.

Requirements: 1.1, 1.2, 1.3, 1.6, 1.7
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.auth import AuthService
from app.core.config import get_settings
from app.db.session import get_db_session

router = APIRouter()
settings = get_settings()


class TelegramAuthRequest(BaseModel):
    """Request model for Telegram authentication.
    
    Requirements: 1.1
    """
    init_data: str


class UserProfile(BaseModel):
    """User profile data returned in auth response.
    
    Requirements: 1.6
    """
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    balance: float
    referral_code: str | None
    created_at: str
    photo_url: str | None = None


class AuthResponse(BaseModel):
    """Response model for successful authentication.
    
    Requirements: 1.6
    """
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


@router.post("/telegram", response_model=AuthResponse)
async def authenticate_telegram(
    request: TelegramAuthRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Authenticate user via Telegram initData.
    
    This endpoint validates the Telegram initData using HMAC-SHA256 and
    creates or retrieves the user account. Returns an access token and
    user profile on success.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
    
    Args:
        request: Authentication request with initData
        session: Database session
        
    Returns:
        AuthResponse with access token and user profile
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    # Initialize auth service
    auth_service = AuthService(session, settings.bot_token)
    
    try:
        # Authenticate user (validates initData and creates/retrieves user)
        user, is_new_user, photo_url = await auth_service.authenticate_user(request.init_data)
    except ValueError as e:
        # Requirement 1.3: Return 401 for invalid hash
        raise HTTPException(status_code=401, detail=str(e))
    
    # Generate access token (Requirement 1.6)
    access_token = auth_service.generate_access_token(user)
    
    # Return access token and user profile (Requirement 1.6, 1.7)
    return AuthResponse(
        access_token=access_token,
        user=UserProfile(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            balance=float(user.balance),
            referral_code=user.referral_code,
            created_at=user.created_at.isoformat(),
            photo_url=photo_url
        )
    )
