"""Chat and messaging schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class ChatMessageRequest(BaseModel):
    """Request to send chat message."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    text: str = Field(..., min_length=1, max_length=5000, description="Message text")
    media_url: Optional[str] = Field(None, max_length=500, description="Optional media URL")


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: int
    deal_id: int
    sender_id: int
    sender_username: str | None
    text: str
    media_url: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class ChatMessageListResponse(BaseModel):
    """Paginated chat messages."""
    items: List[ChatMessageResponse]
    total: int
    page: int
    limit: int


class TypingIndicatorRequest(BaseModel):
    """WebSocket typing indicator."""
    is_typing: bool


class ReadReceiptRequest(BaseModel):
    """WebSocket read receipt."""
    message_id: int = Field(..., gt=0)


class ChatInfoResponse(BaseModel):
    """Chat information."""
    deal_id: int
    buyer_id: int
    buyer_username: str | None
    seller_id: int
    seller_username: str | None
    lot_title: str
    deal_status: str
    unread_count: int
