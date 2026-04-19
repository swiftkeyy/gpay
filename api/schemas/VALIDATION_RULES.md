# Pydantic Schema Validation Rules

This document summarizes all validation rules implemented in the API schemas for the P2P Marketplace Transformation project.

## Requirements Coverage

### Requirement 3.6: Shop Name Validation
**Rule**: Shop name must be between 3 and 120 characters

**Implementation**:
- `SellerApplicationRequest.shop_name`: `Field(..., min_length=3, max_length=120)`
- `SellerProfileUpdate.shop_name`: `Field(None, min_length=3, max_length=120)`

**Files**: `api/schemas/sellers.py`

---

### Requirement 5.9: Lot Title Validation
**Rule**: Lot title must be between 3 and 255 characters

**Implementation**:
- `LotCreateRequest.title`: `Field(..., min_length=3, max_length=255)`
- `LotUpdateRequest.title`: `Field(None, min_length=3, max_length=255)`

**Files**: `api/schemas/sellers.py`

---

### Requirement 5.10: Price Format Validation
**Rule**: Price must be positive with maximum 2 decimal places

**Implementation**:
- `LotCreateRequest.price`: 
  - Field constraint: `Field(..., gt=0)`
  - Validator: Rounds to 2 decimal places and ensures positive value
- `LotUpdateRequest.price`:
  - Field constraint: `Field(None, gt=0)`
  - Validator: Rounds to 2 decimal places and ensures positive value
- `WithdrawalRequest.amount`:
  - Field constraint: `Field(..., gt=0)`
  - Validator: Rounds to 2 decimal places and ensures positive value
- `RefundRequest.amount`:
  - Field constraint: `Field(..., gt=0)`
  - Validator: Rounds to 2 decimal places and ensures positive value
- `GrantBalanceRequest.amount`:
  - Validator: Rounds to 2 decimal places (can be negative for deductions)
- `DisputeResolutionRequest.partial_refund_amount`:
  - Field constraint: `Field(None, gt=0)`
  - Validator: Rounds to 2 decimal places and ensures positive value

**Files**: 
- `api/schemas/sellers.py`
- `api/schemas/payments.py`
- `api/schemas/admin.py`

---

### Requirement 11.10: Rating and Review Validation
**Rule**: 
- Rating must be an integer between 1 and 5
- Review text must not exceed 2000 characters

**Implementation**:
- `CreateReviewRequest.rating`:
  - Field constraint: `Field(..., ge=1, le=5)`
  - Validator: Ensures value is between 1 and 5
- `CreateReviewRequest.text`:
  - Field constraint: `Field(None, max_length=2000)`
  - Validator: Ensures text does not exceed 2000 characters
- `ReviewReplyRequest.reply_text`:
  - Field constraint: `Field(..., min_length=1, max_length=2000)`

**Files**: `api/schemas/reviews.py`

---

## Additional Validation Rules

### String Length Validations

#### Shop Descriptions
- `SellerApplicationRequest.description`: max 2000 characters
- `SellerProfileUpdate.description`: max 2000 characters

#### Lot Descriptions
- `LotCreateRequest.description`: max 5000 characters
- `LotUpdateRequest.description`: max 5000 characters

#### Stock Items
- `StockItemAdd.data`: max 10000 characters

#### Payment Details
- `WithdrawalRequest.payment_details`: max 500 characters

#### Messages
- `DealMessageRequest.text`: 1-5000 characters
- `ChatMessageRequest.text`: 1-5000 characters

#### Disputes
- `DisputeRequest.reason`: 10-2000 characters
- `DisputeResolutionRequest.admin_comment`: 1-2000 characters

#### Delivery
- `DealDeliveryRequest.delivery_data`: 1-10000 characters

#### Admin Actions
- `SellerApprovalRequest.rejection_reason`: max 500 characters
- `UserBlockRequest.reason`: max 500 characters
- `GrantBalanceRequest.reason`: 1-500 characters
- `LotModerationRequest.rejection_reason`: max 500 characters
- `BroadcastRequest.message`: 1-4096 characters

#### Promo Codes
- `PromoCodeRequest.promo_code`: 1-50 characters
- `CreateOrderRequest.promo_code`: max 50 characters

#### Idempotency
- `CreateOrderRequest.idempotency_key`: 1-255 characters

### Numeric Validations

#### Positive Integers
- `AddToCartRequest.product_id`: > 0
- `AddToCartRequest.quantity`: >= 1
- `UpdateCartItemRequest.quantity`: >= 1
- `LotCreateRequest.game_id`: > 0
- `LotCreateRequest.category_id`: > 0
- `LotCreateRequest.product_id`: > 0
- `LotCreateRequest.stock_quantity`: >= 0 (optional)
- `LotBoostRequest.duration_hours`: 1-168 hours

#### Photo Limits
- `CreateReviewRequest.photo_ids`: max 5 items

### Pattern Validations

#### Delivery Types
- Pattern: `^(auto|instant|manual)$`
- Used in: `LotCreateRequest`, `LotUpdateRequest`

#### Lot Status
- Pattern: `^(draft|active|out_of_stock|suspended)$`
- Used in: `LotUpdateRequest`

#### Payment Methods
- Withdrawal: `^(card|qiwi|yoomoney|crypto)$`
- Payment: `^(yookassa|tinkoff|cloudpayments|cryptobot|telegram_stars)$`

#### Seller Status
- Pattern: `^(active|rejected|suspended)$`
- Used in: `SellerApprovalRequest`, `LotModerationRequest`

#### Dispute Resolution
- Pattern: `^(release_to_seller|refund_to_buyer|partial_refund)$`
- Used in: `DisputeResolutionRequest`

#### Broadcast Audience
- Pattern: `^(all|buyers|sellers|admins)$`
- Used in: `BroadcastRequest`

### Configuration

All request schemas use `ConfigDict(str_strip_whitespace=True)` to automatically strip leading and trailing whitespace from string fields, improving data quality and user experience.

## Schema Files

1. **sellers.py** - Seller management, lot creation, withdrawals
2. **reviews.py** - Product and seller reviews
3. **payments.py** - Payment processing and refunds
4. **admin.py** - Admin panel operations
5. **cart.py** - Shopping cart operations
6. **orders.py** - Order creation and payment
7. **deals.py** - Deal management and disputes
8. **chat.py** - Chat messaging
9. **auth.py** - Authentication
10. **users.py** - User profile management
11. **catalog.py** - Catalog browsing
12. **notifications.py** - Notification management

## Testing Validation Rules

To test these validation rules:

```python
from api.schemas.sellers import LotCreateRequest
from decimal import Decimal

# Valid request
valid_lot = LotCreateRequest(
    title="Valid Title",
    description="Valid description",
    price=Decimal("99.99"),
    game_id=1,
    category_id=1,
    product_id=1,
    delivery_type="auto"
)

# Invalid - title too short
try:
    invalid_lot = LotCreateRequest(
        title="AB",  # Only 2 characters
        description="Valid description",
        price=Decimal("99.99"),
        game_id=1,
        category_id=1,
        product_id=1,
        delivery_type="auto"
    )
except ValueError as e:
    print(f"Validation error: {e}")

# Invalid - price with too many decimals
try:
    invalid_lot = LotCreateRequest(
        title="Valid Title",
        description="Valid description",
        price=Decimal("99.999"),  # 3 decimal places
        game_id=1,
        category_id=1,
        product_id=1,
        delivery_type="auto"
    )
    # Price will be automatically rounded to 99.99
except ValueError as e:
    print(f"Validation error: {e}")
```

## Summary

All required validation rules from the specification have been implemented:
- ✅ Requirement 3.6: Shop name (3-120 characters)
- ✅ Requirement 5.9: Lot title (3-255 characters)
- ✅ Requirement 5.10: Price format (positive, 2 decimals)
- ✅ Requirement 11.10: Rating (1-5) and review text (max 2000 chars)

Additional validations have been added for data integrity, security, and user experience across all API endpoints.
