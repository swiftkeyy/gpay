"""Auth router - simplified version."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.entities import User

router = APIRouter()


class TelegramAuthRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    access_token: str
    user: dict


@router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(
    request: TelegramAuthRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Authenticate user via Telegram Mini App initData."""
    # В упрощенной версии просто создаем/получаем пользователя
    # В продакшене нужно валидировать initData через Telegram API
    
    # Парсим initData (упрощенно - берем user из query string)
    # Формат: user={"id":123,"first_name":"Test"}
    import json
    import urllib.parse
    
    try:
        params = dict(urllib.parse.parse_qsl(request.init_data))
        user_data = json.loads(params.get('user', '{}'))
        telegram_id = user_data.get('id')
        
        if not telegram_id:
            raise HTTPException(status_code=400, detail="Invalid initData")
        
        # Ищем или создаем пользователя
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=user_data.get('username'),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        # Генерируем токен (в упрощенной версии просто возвращаем user_id)
        token = f"simple_token_{user.id}"
        
        return AuthResponse(
            access_token=token,
            user={
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "balance": float(user.balance),
                "referral_code": user.referral_code or "",
                "language_code": "ru",
                "is_admin": False,
                "is_seller": False,
                "created_at": user.created_at.isoformat(),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Auth failed: {str(e)}")
