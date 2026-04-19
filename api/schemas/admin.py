"""Admin panel schemas."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class DashboardStatsResponse(BaseModel):
    """Admin dashboard statistics."""
    total_users: int
    active_sellers: int
    total_orders: int
    total_revenue: Decimal
    pending_disputes: int
    pending_withdrawals: int


class RevenueDataPoint(BaseModel):
    """Single revenue data point."""
    date: str
    revenue: Decimal
    orders_count: int


class RevenueAnalyticsResponse(BaseModel):
    """Revenue analytics with chart data."""
    data_points: List[RevenueDataPoint]
    total_revenue: Decimal
    total_orders: int
    period_start: str
    period_end: str


class TopSellerItem(BaseModel):
    """Top seller statistics."""
    seller_id: int
    shop_name: str
    total_sales: int
    total_revenue: Decimal
    rating: float


class TopProductItem(BaseModel):
    """Top product statistics."""
    product_id: int
    title: str
    total_sales: int
    total_revenue: Decimal
    rating: float


class UserListItem(BaseModel):
    """User item in admin list."""
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    balance: Decimal
    is_blocked: bool
    is_seller: bool
    created_at: str


class UserListResponse(BaseModel):
    """Paginated user list."""
    items: List[UserListItem]
    total: int
    page: int
    limit: int


class SellerApprovalRequest(BaseModel):
    """Request to approve/reject seller application."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    status: str = Field(..., pattern="^(active|rejected|suspended)$", description="New seller status")
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Reason for rejection")


class UserBlockRequest(BaseModel):
    """Request to block/unblock user."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    is_blocked: bool
    reason: Optional[str] = Field(None, max_length=500, description="Reason for blocking")


class GrantBalanceRequest(BaseModel):
    """Request to grant balance to user.
    
    Validates requirement 5.10: Amount with 2 decimal places.
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    amount: Decimal = Field(..., description="Amount to grant (can be negative, 2 decimals)")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for balance change")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount has max 2 decimal places."""
        # Round to 2 decimal places
        return round(v, 2)


class LotModerationRequest(BaseModel):
    """Request to moderate lot."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    status: str = Field(..., pattern="^(active|rejected|suspended)$", description="New lot status")
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Reason for rejection")


class DisputeResolutionRequest(BaseModel):
    """Request to resolve dispute.
    
    Validates requirement 5.10: Partial refund amount with 2 decimal places.
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    resolution: str = Field(..., pattern="^(release_to_seller|refund_to_buyer|partial_refund)$")
    partial_refund_amount: Optional[Decimal] = Field(None, gt=0, description="Partial refund amount (2 decimals)")
    admin_comment: str = Field(..., min_length=1, max_length=2000, description="Admin resolution comment")
    
    @field_validator('partial_refund_amount')
    @classmethod
    def validate_partial_refund(cls, v: Decimal | None) -> Decimal | None:
        """Validate partial refund amount has max 2 decimal places."""
        if v is not None:
            if v <= 0:
                raise ValueError('Partial refund amount must be positive')
            # Round to 2 decimal places
            return round(v, 2)
        return v


class BroadcastRequest(BaseModel):
    """Request to create broadcast message."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    message: str = Field(..., min_length=1, max_length=4096, description="Broadcast message text")
    media_id: Optional[int] = Field(None, description="Optional media attachment ID")
    scheduled_at: Optional[datetime] = Field(None, description="Optional scheduled send time")
    target_audience: str = Field("all", pattern="^(all|buyers|sellers|admins)$", description="Target audience")


class BroadcastResponse(BaseModel):
    """Broadcast message response."""
    id: int
    message: str
    media_id: int | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    target_audience: str
    total_recipients: int
    delivered_count: int
    failed_count: int
    status: str
    created_at: datetime


class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    id: int
    admin_id: int
    admin_username: str | None
    action: str
    entity_type: str
    entity_id: int
    description: str
    metadata: dict
    created_at: datetime


class AuditLogResponse(BaseModel):
    """Paginated audit log."""
    items: List[AuditLogEntry]
    total: int
    page: int
    limit: int


class BulkActionRequest(BaseModel):
    """Request for bulk actions."""
    entity_ids: List[int] = Field(..., min_items=1, max_items=100, description="Entity IDs (1-100)")
    action: str = Field(..., min_length=1, max_length=50, description="Action to perform")
    parameters: dict = Field(default_factory=dict, description="Action parameters")


class BulkActionResponse(BaseModel):
    """Bulk action result."""
    success_count: int
    failed_count: int
    errors: List[str]
