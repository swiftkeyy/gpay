"""Authentication dependencies for API endpoints."""
from __future__ import annotations

import hmac
import hashlib
import json
from typing import Optional
from urllib.parse import parse_qs
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.core.database import get_db
from app.core.models import User
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Validate Telegram Mini App initData using HMAC-SHA256.
    
    Returns parsed user data if valid, raises HTTPException if invalid.
    """
    try:
        # Parse init_data
        params = parse_qs(init_data)
        
        # Extract hash
        received_hash = params.get('hash', [None])[0]
        if not received_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing hash in initData"
            )
        
        # Remove hash from params for validation
        data_check_string_parts = []
        for key in sorted(params.keys()):
            if key == 'hash':
                continue
            value = params[key][0]
            data_check_string_parts.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_string_parts)
        
        # Calculate secret key
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare hashes
        if not hmac.compare_digest(calculated_hash, received_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid initData hash"
            )
        
        # Parse user data
        user_data = json.loads(params.get('user', ['{}'])[0])
        
        return user_data
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"initData validation failed: {str(e)}"
        )


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm="HS256"
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> int:
    """Decode JWT access token and return user_id."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        user_id = int(payload.get("sub"))
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    user_id = decode_access_token(token)
    
    result = await db.execute(
        select(User).where(User.telegram_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked"
        )
    
    return user


async def get_current_user_ws(token: str, db: AsyncSession) -> User:
    """Get current authenticated user for WebSocket connections."""
    user_id = decode_access_token(token)
    
    result = await db.execute(
        select(User).where(User.telegram_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked"
        )
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user
