"""Games router - simplified version."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.entities import Game

router = APIRouter()


@router.get("/games")
async def get_games(session: AsyncSession = Depends(get_db_session)):
    """Get all active games."""
    stmt = select(Game).where(Game.is_active == True, Game.is_deleted == False).order_by(Game.sort_order)
    result = await session.execute(stmt)
    games = result.scalars().all()
    
    return [
        {
            "id": game.id,
            "slug": game.slug,
            "title": game.title,
            "description": game.description,
            "image_id": game.image_id,
            "is_active": game.is_active,
            "sort_order": game.sort_order,
        }
        for game in games
    ]
