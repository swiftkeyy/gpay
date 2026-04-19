"""Notification schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    """Single notification response."""
    id: int
    user_id: int
    notification_type: str
    title: str
    message: str
    reference_type: str | None
    reference_id: int | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated notification list."""
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    limit: int


class UnreadCountResponse(BaseModel):
    """Unread notifications count."""
    unread_count: int


class MarkReadRequest(BaseModel):
    """Request to mark notification as read."""
    notification_id: int = Field(..., gt=0)


class NotificationPreferencesRequest(BaseModel):
    """Request to update notification preferences."""
    email_enabled: bool = True
    push_enabled: bool = True
    telegram_enabled: bool = True
    new_order: bool = True
    order_status_change: bool = True
    new_message: bool = True
    payment_received: bool = True
    new_review: bool = True
    withdrawal_processed: bool = True


class NotificationPreferencesResponse(BaseModel):
    """Notification preferences response."""
    email_enabled: bool
    push_enabled: bool
    telegram_enabled: bool
    new_order: bool
    order_status_change: bool
    new_message: bool
    payment_received: bool
    new_review: bool
    withdrawal_processed: bool
