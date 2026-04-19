"""Order and deal schemas."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class CreateOrderRequest(BaseModel):
    """Request to create order from cart."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    idempotency_key: str = Field(..., min_length=1, max_length=255, description="Idempotency key to prevent duplicates")
    promo_code: Optional[str] = Field(None, max_length=50, description="Optional promo code")


class OrderItemResponse(BaseModel):
    """Single order item."""
    id: int
    lot_id: int
    lot_title: str
    lot_image_url: str
    quantity: int
    price_per_item: Decimal
    subtotal: Decimal
    seller_id: int
    seller_name: str


class OrderResponse(BaseModel):
    """Detailed order response."""
    id: int
    status: str
    total_amount: Decimal
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderListItem(BaseModel):
    """Order item in list view."""
    id: int
    status: str
    total_amount: Decimal
    items_count: int
    created_at: datetime


class OrderListResponse(BaseModel):
    """Paginated order list."""
    items: List[OrderListItem]
    total: int
    page: int
    limit: int


class PaymentInitiationRequest(BaseModel):
    """Request to initiate payment."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    payment_method: str = Field(..., pattern="^(yookassa|tinkoff|cloudpayments|cryptobot|telegram_stars)$")


class PaymentInitiationResponse(BaseModel):
    """Payment initiation response."""
    payment_url: str
    payment_id: str
    order_id: int
    amount: float
    currency: str
    payment_method: str
