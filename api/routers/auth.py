"""Authentication router for Telegram Mini App."""
from __future__ import annotations

import hashlib
import hmac
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.models import User
from app.repositories.users import UserRepository

router = APIRouter()
settings = get_settings()


class TelegramAuthRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """Validate Telegram initData using HMAC-SHA256."""
    try:
        parsed_data = dict(parse_qsl(init_data))
        hash_value = parsed_data.pop("hash", None)
        
        if not hash_value:
            return None
        
        # Create data check string
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_arr)
        
        # Calculate secret key
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != hash_value:
            return None
        
        return parsed_data
    except Exception:
        return None


@router.post("/telegram", response_model=AuthResponse)
async def authenticate_telegram(
    request: TelegramAuthRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Authenticate user via Telegram initData."""
    # Validate initData
    user_data = validate_telegram_init_data(request.init_data, settings.bot_token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication data")
    
    # Extract user info
    user_json = user_data.get("user")
    if not user_json:
        raise HTTPException(status_code=401, detail="User data not found")
    
    import json
    user_info = json.loads(user_json)
    telegram_id = user_info.get("id")
    username = user_info.get("username")
    first_name = user_info.get("first_name")
    
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Telegram ID not found")
    
    # Get or create user
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_id)
    
    if not user:
        # Create new user
        import secrets
        referral_code = secrets.token_urlsafe(8)[:12]
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            balance=0.00,
            referral_code=referral_code,
            language_code=user_info.get("language_code", "en")
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    # Generate access token (simplified - in production use JWT)
    access_token = f"user_{user.id}_{user.telegram_id}"
    
    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": float(user.balance),
            "referral_code": user.referral_code,
            "language_code": user.language_code,
            "created_at": user.created_at.isoformat()
        }
    )
