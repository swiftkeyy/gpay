"""Pydantic schemas for API request/response validation."""
from __future__ import annotations

from .auth import *
from .users import *
from .sellers import *
from .catalog import *
from .cart import *
from .orders import *
from .deals import *
from .reviews import *
from .payments import *
from .admin import *

__all__ = [
    # Auth
    "TelegramAuthRequest",
    "AuthResponse",
    "UserProfile",
    
    # Users
    "UserProfileResponse",
    "UpdateProfileRequest",
    "BalanceResponse",
    "TransactionResponse",
    "TransactionListResponse",
    "ReferralStatsResponse",
    
    # Sellers
    "SellerApplicationRequest",
    "SellerProfileResponse",
    "SellerProfileUpdate",
    "SellerDashboardResponse",
    "LotCreateRequest",
    "LotUpdateRequest",
    "LotResponse",
    "LotListResponse",
    "StockItemAdd",
    "WithdrawalRequest",
    "WithdrawalResponse",
    "LotBoostRequest",
    
    # Catalog
    "GameResponse",
    "GameListResponse",
    "CategoryResponse",
    "ProductResponse",
    "LotSearchResponse",
    "LotDetailResponse",
    
    # Cart
    "AddToCartRequest",
    "UpdateCartItemRequest",
    "CartItemResponse",
    "CartResponse",
    "CartValidationResponse",
    
    # Orders
    "CreateOrderRequest",
    "OrderResponse",
    "OrderListResponse",
    "PaymentInitiationRequest",
    
    # Deals
    "DealResponse",
    "DealMessageRequest",
    "DealMessageResponse",
    "DisputeRequest",
    "DisputeResponse",
    
    # Reviews
    "CreateReviewRequest",
    "ReviewResponse",
    "ReviewListResponse",
    "ReviewReplyRequest",
    
    # Payments
    "PaymentMethodResponse",
    "PaymentResponse",
    "WebhookPayload",
    
    # Admin
    "DashboardStatsResponse",
    "RevenueAnalyticsResponse",
    "UserListResponse",
    "SellerApprovalRequest",
    "UserBlockRequest",
    "GrantBalanceRequest",
    "LotModerationRequest",
    "DisputeResolutionRequest",
    "BroadcastRequest",
    "BroadcastResponse",
    "AuditLogResponse",
    "BulkActionRequest",
    "BulkActionResponse",
]
