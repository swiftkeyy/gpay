"""Notifications router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_db_session

router = APIRouter()
logger = logging.getLogger(__name__)


def decode_simple_token(token: str) -> dict | None:
    """Decode simple token format: user_{user_id}_{telegram_id}"""
    try:
        parts = token.split("_")
        if len(parts) == 3 and parts[0] == "user":
            return {
                "user_id": int(parts[1]),
                "telegram_id": int(parts[2])
            }
    except Exception as e:
        logger.error(f"Token decode error: {e}")
    return None


@router.get("/notifications")
async def get_notifications(
    user_id: int = 1,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session)
):
    """Get user notifications."""
    # TODO: Implement notification retrieval
    return {"items": [], "total": 0}


@router.patch("/notifications/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Mark notification as read."""
    # TODO: Implement mark as read
    return {"message": "Marked as read"}


@router.post("/notifications/read-all")
async def mark_all_as_read(
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Mark all notifications as read."""
    # TODO: Implement mark all as read
    return {"message": "All marked as read"}


@router.get("/notifications/unread-count")
async def get_unread_count(
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Get unread notification count."""
    # TODO: Implement unread count
    return {"count": 0}


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time notifications."""
    try:
        # Verify token
        payload = decode_simple_token(token)
        if not payload or not payload.get("user_id"):
            logger.warning(f"WebSocket: Invalid token format: {token}")
            await websocket.close(code=1008, reason="Invalid token")
            return

        user_id = payload["user_id"]

        # Accept connection
        await websocket.accept()
        logger.info(f"WebSocket connected for user {user_id}")

        try:
            # Keep connection alive and listen for messages
            while True:
                # Wait for any message from client (ping/pong)
                data = await websocket.receive_text()
                # Echo back or handle as needed
                # For now, just keep connection alive
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
