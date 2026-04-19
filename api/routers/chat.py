"""WebSocket chat router for real-time buyer-seller communication."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.db.session import get_db
from app.models.entities import User, Deal, DealMessage
from api.dependencies.auth import get_current_user_ws

router = APIRouter()
logger = logging.getLogger(__name__)

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for chat."""
    
    def __init__(self):
        # deal_id -> {user_id -> websocket}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # user_id -> set of deal_ids they're connected to
        self.user_connections: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, deal_id: int, user_id: int):
        """Connect a user to a deal chat."""
        await websocket.accept()
        
        if deal_id not in self.active_connections:
            self.active_connections[deal_id] = {}
        
        self.active_connections[deal_id][user_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(deal_id)
        
        logger.info(f"User {user_id} connected to deal {deal_id} chat")
    
    def disconnect(self, deal_id: int, user_id: int):
        """Disconnect a user from a deal chat."""
        if deal_id in self.active_connections:
            self.active_connections[deal_id].pop(user_id, None)
            if not self.active_connections[deal_id]:
                del self.active_connections[deal_id]
        
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(deal_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"User {user_id} disconnected from deal {deal_id} chat")
    
    async def send_personal_message(self, message: dict, deal_id: int, user_id: int):
        """Send a message to a specific user in a deal."""
        if deal_id in self.active_connections and user_id in self.active_connections[deal_id]:
            websocket = self.active_connections[deal_id][user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
    
    async def broadcast_to_deal(self, message: dict, deal_id: int, exclude_user: Optional[int] = None):
        """Broadcast a message to all users in a deal chat."""
        if deal_id not in self.active_connections:
            return
        
        for user_id, websocket in list(self.active_connections[deal_id].items()):
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")


manager = ConnectionManager()


@router.websocket("/ws/chat/{deal_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    deal_id: int,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat.
    
    Query params:
    - token: JWT access token for authentication
    
    Message types:
    - text: {"type": "text", "content": "message text"}
    - typing: {"type": "typing", "is_typing": true/false}
    - read: {"type": "read", "message_id": 123}
    - read_all: {"type": "read_all"}
    """
    # Authenticate user
    try:
        user = await get_current_user_ws(token, db)
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Verify deal exists and user is participant
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Check if user is buyer or seller
    if user.id != deal.buyer_id and user.id != deal.seller_id:
        logger.warning(f"User {user.id} tried to access deal {deal_id} chat without permission")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect user
    await manager.connect(websocket, deal_id, user.id)
    
    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "deal_id": deal_id,
        "user_id": user.id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_type = message_data.get("type")
            
            if message_type == "text":
                # Save message to database
                content = message_data.get("content", "").strip()
                if not content:
                    continue
                
                new_message = DealMessage(
                    deal_id=deal_id,
                    sender_id=user.id,
                    content=content,
                    is_read=False
                )
                db.add(new_message)
                await db.commit()
                await db.refresh(new_message)
                
                # Broadcast to other party
                response = {
                    "type": "message",
                    "message_id": new_message.id,
                    "deal_id": deal_id,
                    "sender_id": user.id,
                    "content": content,
                    "is_read": False,
                    "created_at": new_message.created_at.isoformat()
                }
                
                # Send to sender (confirmation)
                await manager.send_personal_message(response, deal_id, user.id)
                
                # Send to other party
                other_user_id = deal.seller_id if user.id == deal.buyer_id else deal.buyer_id
                await manager.send_personal_message(response, deal_id, other_user_id)
                
                logger.info(f"Message {new_message.id} sent in deal {deal_id} by user {user.id}")
            
            elif message_type == "typing":
                # Broadcast typing indicator to other party
                is_typing = message_data.get("is_typing", False)
                other_user_id = deal.seller_id if user.id == deal.buyer_id else deal.buyer_id
                
                await manager.send_personal_message({
                    "type": "typing",
                    "deal_id": deal_id,
                    "user_id": user.id,
                    "is_typing": is_typing
                }, deal_id, other_user_id)
            
            elif message_type == "read":
                # Mark specific message as read
                message_id = message_data.get("message_id")
                if message_id:
                    result = await db.execute(
                        select(DealMessage).where(
                            and_(
                                DealMessage.id == message_id,
                                DealMessage.deal_id == deal_id,
                                DealMessage.sender_id != user.id  # Can't mark own messages as read
                            )
                        )
                    )
                    msg = result.scalar_one_or_none()
                    if msg:
                        msg.is_read = True
                        msg.read_at = datetime.utcnow()
                        await db.commit()
                        
                        # Notify sender
                        await manager.send_personal_message({
                            "type": "read_receipt",
                            "message_id": message_id,
                            "read_by": user.id,
                            "read_at": msg.read_at.isoformat()
                        }, deal_id, msg.sender_id)
            
            elif message_type == "read_all":
                # Mark all messages from other party as read
                result = await db.execute(
                    select(DealMessage).where(
                        and_(
                            DealMessage.deal_id == deal_id,
                            DealMessage.sender_id != user.id,
                            DealMessage.is_read == False
                        )
                    )
                )
                messages = result.scalars().all()
                
                now = datetime.utcnow()
                for msg in messages:
                    msg.is_read = True
                    msg.read_at = now
                
                await db.commit()
                
                # Notify other party
                other_user_id = deal.seller_id if user.id == deal.buyer_id else deal.buyer_id
                await manager.send_personal_message({
                    "type": "read_all_receipt",
                    "read_by": user.id,
                    "count": len(messages),
                    "read_at": now.isoformat()
                }, deal_id, other_user_id)
            
            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(deal_id, user.id)
        logger.info(f"User {user.id} disconnected from deal {deal_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id} in deal {deal_id}: {e}")
        manager.disconnect(deal_id, user.id)


@router.get("/deals/{deal_id}/messages")
async def get_deal_messages(
    deal_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat messages for a deal.
    
    Returns messages in reverse chronological order (newest first).
    """
    # Verify deal exists and user is participant
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if current_user.id != deal.buyer_id and current_user.id != deal.seller_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get messages
    result = await db.execute(
        select(DealMessage)
        .where(DealMessage.deal_id == deal_id)
        .order_by(DealMessage.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return {
        "deal_id": deal_id,
        "messages": [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "content": msg.content,
                "is_read": msg.is_read,
                "read_at": msg.read_at.isoformat() if msg.read_at else None,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "total": len(messages),
        "skip": skip,
        "limit": limit
    }


@router.get("/deals/{deal_id}/unread-count")
async def get_unread_count(
    deal_id: int,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread messages in a deal."""
    # Verify deal exists and user is participant
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if current_user.id != deal.buyer_id and current_user.id != deal.seller_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Count unread messages from other party
    result = await db.execute(
        select(DealMessage).where(
            and_(
                DealMessage.deal_id == deal_id,
                DealMessage.sender_id != current_user.id,
                DealMessage.is_read == False
            )
        )
    )
    unread_messages = result.scalars().all()
    
    return {
        "deal_id": deal_id,
        "unread_count": len(unread_messages)
    }
