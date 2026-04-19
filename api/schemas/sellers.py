"""Seller management schemas."""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class SellerApplicationRequest(BaseModel):
    """Request to apply as a seller.
    
    Validates requirement 3.6: Shop name 3-120 characters.
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    shop_name: str = Field(..., min_length=3, max_length=120, description="Shop name (3-120 characters)")
    description: Optional[str] = Field(None, max_length=2000, description="Shop description")


class SellerProfileResponse(BaseModel):
    """Seller profile response."""
    id: int
    shop_name: str
    description: str | None
    status: str
    is_verified: bool
    rating: float
    total_sales: int
    balance: float
    created_at: str


class SellerProfileUpdate(BaseModel):
    """Request to update seller profile.
    
    Validates requirement 3.6: Shop name 3-120 characters.
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    shop_name: Optional[str] = Field(None, min_length=3, max_length=120, description="Shop name (3-120 characters)")
    description: Optional[str] = Field(None, max_length=2000, description="Shop description")


class BalanceBreakdown(BaseModel):
    """Seller balance breakdown."""
    available: float
    pending_withdrawals: float
    in_escrow: float


class PeriodStats(BaseModel):
    """Sales statistics for a period."""
    sales: int
    revenue: float


class PerformanceMetrics(BaseModel):
    """Seller performance metrics."""
    rating: float
    total_sales: int
    active_deals: int


class SellerDashboardResponse(BaseModel):
    """Seller dashboard with statistics."""
    balance: BalanceBreakdown
    today: PeriodStats
    week: PeriodStats
    month: PeriodStats
    all_time: PeriodStats
    performance: PerformanceMetrics


class LotCreateRequest(BaseModel):
    """Request to create a new lot.
    
    Validates:
    - Requirement 5.9: Lot title 3-255 characters
    - Requirement 5.10: Price positive with 2 decimal places
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(..., min_length=3, max_length=255, description="Lot title (3-255 characters)")
    description: str = Field(..., max_length=5000, description="Lot description")
    price: Decimal = Field(..., gt=0, description="Price (positive, 2 decimal places)")
    game_id: int = Field(..., gt=0)
    category_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    delivery_type: str = Field(..., pattern="^(auto|instant|manual)$", description="Delivery type")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Initial stock quantity")
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price is positive with max 2 decimal places (req 5.10)."""
        if v <= 0:
            raise ValueError('Price must be positive')
        # Round to 2 decimal places
        return round(v, 2)


class LotUpdateRequest(BaseModel):
    """Request to update a lot.
    
    Validates:
    - Requirement 5.9: Lot title 3-255 characters
    - Requirement 5.10: Price positive with 2 decimal places
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Lot title (3-255 characters)")
    description: Optional[str] = Field(None, max_length=5000, description="Lot description")
    price: Optional[Decimal] = Field(None, gt=0, description="Price (positive, 2 decimal places)")
    delivery_type: Optional[str] = Field(None, pattern="^(auto|instant|manual)$")
    status: Optional[str] = Field(None, pattern="^(draft|active|out_of_stock|suspended)$")
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal | None) -> Decimal | None:
        """Validate price is positive with max 2 decimal places (req 5.10)."""
        if v is not None:
            if v <= 0:
                raise ValueError('Price must be positive')
            # Round to 2 decimal places
            return round(v, 2)
        return v


class LotResponse(BaseModel):
    """Single lot response."""
    id: int
    title: str
    price: float
    status: str
    delivery_type: str
    views: int
    sales: int
    image_url: str
    created_at: str


class LotListResponse(BaseModel):
    """Paginated lot list response."""
    items: List[LotResponse]
    total: int
    skip: int
    limit: int


class StockItemAdd(BaseModel):
    """Request to add stock item for auto-delivery."""
    data: str = Field(..., max_length=10000, description="Stock item data (e.g., account credentials)")


class WithdrawalRequest(BaseModel):
    """Request to withdraw funds.
    
    Validates requirement 5.10: Amount positive with 2 decimal places.
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    amount: Decimal = Field(..., gt=0, description="Withdrawal amount (positive, 2 decimals)")
    payment_method: str = Field(..., pattern="^(card|qiwi|yoomoney|crypto)$")
    payment_details: str = Field(..., max_length=500, description="Payment details")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is positive with max 2 decimal places."""
        if v <= 0:
            raise ValueError('Amount must be positive')
        # Round to 2 decimal places
        return round(v, 2)


class WithdrawalResponse(BaseModel):
    """Withdrawal response."""
    id: int
    amount: float
    payment_method: str
    status: str
    created_at: str
    processed_at: str | None


class LotBoostRequest(BaseModel):
    """Request to boost a lot."""
    duration_hours: int = Field(..., ge=1, le=168, description="Boost duration (1-168 hours)")
