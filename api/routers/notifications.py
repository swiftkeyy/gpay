"""Notifications router."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.db.session import get_db_session, get_db
from app.models.entities import Notification, User
from api.dependencies.auth import get_current_user, get_current_user_ws

router = APIRouter()
logger = logging.getLogger(__name__)


# Connection manager for WebSocket connections
class NotificationConnectionManager:
    """Manages WebSocket connections for notifications."""
    
    def __init__(self):
        # user_id -> websocket
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user to notification stream."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to notifications")
    
    def disconnect(self, user_id: int):
        """Disconnect a user from notification stream."""
        self.active_connections.pop(user_id, None)
        logger.info(f"User {user_id} disconnected from notifications")
    
    async def send_notification(self, user_id: int, notification: dict):
        """Send a notification to a specific user."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(notification)
                logger.info(f"Notification sent to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")
                self.disconnect(user_id)


notification_manager = NotificationConnectionManager()


@router.get("/notifications")
async def get_notifications(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get user notifications with pagination.
    
    Requirements: 16.8
    """
    if limit > 100:
        limit = 100
    
    offset = (page - 1) * limit
    
    # Get notifications
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    notifications = result.scalars().all()
    
    # Get total count
    result = await session.execute(
        select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
    )
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": notif.id,
                "type": notif.notification_type,
                "title": notif.title,
                "message": notif.message,
                "is_read": notif.is_read,
                "read_at": notif.read_at.isoformat() if notif.read_at else None,
                "reference_type": notif.reference_type,
                "reference_id": notif.reference_id,
                "created_at": notif.created_at.isoformat()
            }
            for notif in notifications
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.patch("/notifications/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Mark notification as read.
    
    Requirements: 16.9
    """
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await session.commit()
    
    return {
        "id": notification.id,
        "is_read": notification.is_read,
        "read_at": notification.read_at.isoformat()
    }


@router.post("/notifications/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Mark all notifications as read.
    
    Requirements: 16.9
    """
    now = datetime.utcnow()
    
    result = await session.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True, read_at=now)
    )
    
    await session.commit()
    
    return {
        "message": "All notifications marked as read",
        "updated_count": result.rowcount
    }


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get unread notification count.
    
    Requirements: 16.8
    """
    result = await session.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    )
    count = result.scalar() or 0
    
    return {"count": count}


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications.
    
    Requirements: 16.7
    
    Message types from server:
    - notification: {"type": "notification", "data": {...}}
    - order_status: {"type": "order_status", "data": {...}}
    - pong: {"type": "pong"}
    
    Message types from client:
    - ping: {"type": "ping"}
    - get_recent: {"type": "get_recent", "limit": 10}
    """
    # Authenticate user
    try:
        user = await get_current_user_ws(token, db)
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect user
    await notification_manager.connect(websocket, user.id)
    
    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "user_id": user.id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_type = message_data.get("type")
            
            if message_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
            
            elif message_type == "get_recent":
                # Client requests recent notifications
                limit = message_data.get("limit", 10)
                if limit > 50:
                    limit = 50
                
                result = await db.execute(
                    select(Notification)
                    .where(Notification.user_id == user.id)
                    .order_by(Notification.created_at.desc())
                    .limit(limit)
                )
                notifications = result.scalars().all()
                
                # Send recent notifications
                for notif in reversed(notifications):  # Send oldest first
                    await websocket.send_json({
                        "type": "notification",
                        "data": {
                            "id": notif.id,
                            "notification_type": notif.notification_type,
                            "title": notif.title,
                            "message": notif.message,
                            "is_read": notif.is_read,
                            "read_at": notif.read_at.isoformat() if notif.read_at else None,
                            "reference_type": notif.reference_type,
                            "reference_id": notif.reference_id,
                            "created_at": notif.created_at.isoformat()
                        }
                    })
                
                # Send sync complete
                await websocket.send_json({
                    "type": "sync_complete",
                    "count": len(notifications)
                })
    
    except WebSocketDisconnect:
        notification_manager.disconnect(user.id)
        logger.info(f"User {user.id} disconnected from notifications")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}")
        notification_manager.disconnect(user.id)


# Helper function to send notification via WebSocket (can be called from other services)
async def send_notification_to_user(
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    reference_type: str | None = None,
    reference_id: int | None = None,
    db: AsyncSession = None,
    bot_notification_data: dict | None = None
):
    """
    Send a notification to a user via WebSocket if connected.
    Also saves to database and sends bot push notification.
    
    This function can be imported and used by other services.
    
    Args:
        user_id: User ID to send notification to
        notification_type: Type of notification (new_order, order_status, etc.)
        title: Notification title
        message: Notification message
        reference_type: Type of referenced entity (order, deal, etc.)
        reference_id: ID of referenced entity
        db: Database session
        bot_notification_data: Additional data for bot push notification (optional)
    """
    # Save to database
    if db:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
            is_read=False
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        # Send via WebSocket if user is connected
        await notification_manager.send_notification(user_id, {
            "type": "notification",
            "data": {
                "id": notification.id,
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "read_at": None,
                "reference_type": notification.reference_type,
                "reference_id": notification.reference_id,
                "created_at": notification.created_at.isoformat()
            }
        })
        
        # Send bot push notification if data provided
        if bot_notification_data:
            try:
                # Get user's telegram_id
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user and user.telegram_id:
                    from app.services.bot_notifications import send_bot_notification
                    await send_bot_notification(
                        notification_type=notification_type,
                        user_telegram_id=user.telegram_id,
                        **bot_notification_data
                    )
            except Exception as e:
                logger.error(f"Error sending bot notification: {e}")
        
        return notification
    
    return None
