"""Deal and dispute schemas."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class DealResponse(BaseModel):
    """Deal details response."""
    id: int
    order_id: int
    buyer_id: int
    seller_id: int
    lot_id: int
    status: str
    amount: Decimal
    commission_amount: Decimal
    seller_amount: Decimal
    escrow_released: bool
    escrow_released_at: datetime | None
    auto_complete_at: datetime | None
    completed_at: datetime | None
    buyer_confirmed: bool
    buyer_confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DealMessageRequest(BaseModel):
    """Request to send message in deal chat."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    text: str = Field(..., min_length=1, max_length=5000, description="Message text")
    media_id: Optional[int] = Field(None, description="Optional media attachment ID")


class DealMessageResponse(BaseModel):
    """Deal chat message response."""
    id: int
    deal_id: int
    sender_id: int
    text: str
    media_id: int | None
    is_read: bool
    created_at: datetime


class DealMessageListResponse(BaseModel):
    """Paginated deal messages."""
    items: List[DealMessageResponse]
    total: int
    page: int
    limit: int


class DisputeRequest(BaseModel):
    """Request to open dispute."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    reason: str = Field(..., min_length=10, max_length=2000, description="Dispute reason (10-2000 characters)")


class DisputeResponse(BaseModel):
    """Dispute details response."""
    id: int
    deal_id: int
    initiator_id: int
    reason: str
    status: str
    resolution: str | None
    admin_id: int | None
    resolved_at: datetime | None
    created_at: datetime


class DealConfirmationResponse(BaseModel):
    """Response for deal confirmation actions."""
    message: str
    deal_id: int
    new_status: str


class DealDeliveryRequest(BaseModel):
    """Request to deliver goods (manual delivery)."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    delivery_data: str = Field(..., min_length=1, max_length=10000, description="Delivery data/instructions")
