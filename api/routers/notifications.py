"""Notifications router."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

router = APIRouter()


@router.get("")
async def get_notifications(
    user_id: int = 1,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_session)
):
    """Get user notifications."""
    # TODO: Implement notification retrieval
    return {"items": [], "total": 0}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Mark notification as read."""
    # TODO: Implement mark as read
    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_as_read(
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Mark all notifications as read."""
    # TODO: Implement mark all as read
    return {"message": "All marked as read"}


@router.get("/unread-count")
async def get_unread_count(
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Get unread notification count."""
    # TODO: Implement unread count
    return {"count": 0}
