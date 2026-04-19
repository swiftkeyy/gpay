"""Payment schemas."""
from __future__ import annotations

from decimal import Decimal
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class PaymentMethodResponse(BaseModel):
    """Available payment method."""
    id: str
    name: str
    icon_url: str | None
    is_enabled: bool
    min_amount: Decimal | None
    max_amount: Decimal | None


class PaymentMethodListResponse(BaseModel):
    """List of available payment methods."""
    methods: list[PaymentMethodResponse]


class CreatePaymentRequest(BaseModel):
    """Request to create payment."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    order_id: int = Field(..., gt=0)
    payment_method: str = Field(..., min_length=1, max_length=50)
    return_url: Optional[str] = Field(None, max_length=500)


class PaymentResponse(BaseModel):
    """Payment details response."""
    id: int
    order_id: int
    payment_method: str
    amount: Decimal
    currency: str
    status: str
    payment_url: str | None
    provider_payment_id: str | None
    created_at: str
    confirmed_at: str | None


class WebhookPayload(BaseModel):
    """Generic webhook payload."""
    provider: str
    event_type: str
    payment_id: str
    order_id: int | None
    status: str
    amount: Decimal | None
    currency: str | None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookResponse(BaseModel):
    """Webhook processing response."""
    success: bool
    message: str
    payment_id: str | None = None


class RefundRequest(BaseModel):
    """Request to refund payment.
    
    Validates requirement 5.10: Amount positive with 2 decimal places.
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    payment_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0, description="Refund amount (positive, 2 decimals)")
    reason: str = Field(..., min_length=1, max_length=500)
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is positive with max 2 decimal places."""
        if v <= 0:
            raise ValueError('Amount must be positive')
        # Round to 2 decimal places
        return round(v, 2)


class RefundResponse(BaseModel):
    """Refund response."""
    id: int
    payment_id: int
    amount: Decimal
    status: str
    reason: str
    created_at: str
