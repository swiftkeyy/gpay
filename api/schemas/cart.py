"""Shopping cart schemas."""
from __future__ import annotations

from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, ConfigDict


class AddToCartRequest(BaseModel):
    """Request to add item to cart."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(1, ge=1, description="Quantity (minimum 1)")


class UpdateCartItemRequest(BaseModel):
    """Request to update cart item quantity."""
    quantity: int = Field(..., ge=1, description="New quantity (minimum 1)")


class CartItemResponse(BaseModel):
    """Single cart item response."""
    id: int
    product_id: int
    product_title: str
    product_price: Decimal
    product_image_url: str | None
    quantity: int
    subtotal: Decimal
    seller_name: str
    delivery_type: str
    stock_available: int


class CartResponse(BaseModel):
    """Cart with all items."""
    items: List[CartItemResponse]
    subtotal: Decimal
    total: Decimal
    items_count: int


class ValidationError(BaseModel):
    """Cart validation error."""
    item_id: int
    lot_id: int
    error: str


class CartValidationResponse(BaseModel):
    """Cart validation result."""
    valid: bool
    errors: List[ValidationError]


class PromoCodeRequest(BaseModel):
    """Request to apply promo code."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    promo_code: str = Field(..., min_length=1, max_length=50, description="Promo code")


class CartOperationResponse(BaseModel):
    """Generic cart operation response."""
    message: str
    product_id: int | None = None
    quantity: int | None = None
