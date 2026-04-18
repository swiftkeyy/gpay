"""Categories router - simplified version."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.entities import Category

router = APIRouter()


@router.get("/categories")
async def get_categories(
    game_id: int = Query(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Get categories, optionally filtered by game."""
    stmt = select(Category).where(Category.is_active == True, Category.is_deleted == False)
    
    if game_id:
        stmt = stmt.where(Category.game_id == game_id)
    
    stmt = stmt.order_by(Category.sort_order)
    result = await session.execute(stmt)
    categories = result.scalars().all()
    
    return [
        {
            "id": cat.id,
            "game_id": cat.game_id,
            "slug": cat.slug,
            "title": cat.title,
            "description": cat.description,
            "image_id": cat.image_id,
            "is_active": cat.is_active,
            "sort_order": cat.sort_order,
        }
        for cat in categories
    ]
