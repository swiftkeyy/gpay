# Task 8.1: Order Creation from Cart - Implementation Summary

## Overview
Implemented POST /api/v1/orders endpoint to create orders from cart with Product-based system (not Lot-based), promo code support, and idempotency.

## Requirements Validated
- **7.1**: Create order record with all cart items and calculate total amount
- **7.2**: Apply promo code discount if provided
- **7.8**: Use idempotency keys to prevent duplicate order creation

## Key Changes

### 1. Updated Imports (orders.py)
Added necessary imports for Product-based system:
- `Price` - for product pricing
- `PromoCode`, `PromoCodeUsage` - for promo code functionality
- `FulfillmentType`, `PromoType` - for enums
- `get_current_user` - for authentication

### 2. Refactored create_order Endpoint

#### Authentication
- Changed from hardcoded `user_id: int = 1` to `current_user: User = Depends(get_current_user)`
- Now properly authenticates users via JWT token

#### Idempotency (Requirement 7.8)
- Checks for existing order with same `idempotency_key`
- Returns existing order if found (prevents duplicate orders from double-clicks)

#### Cart Validation
- Validates cart exists and is not empty
- Loads cart items with products (not lots)
- Validates each product is active and not deleted
- Gets current active price for each product

#### Subtotal Calculation
- Calculates subtotal from product prices
- Uses `Price.base_price * quantity` for each item

#### Promo Code Application (Requirement 7.2)
If promo code provided:
1. Validates promo code exists and is active
2. Checks expiration dates (starts_at, ends_at)
3. Checks usage limit (max_usages)
4. Checks if user already used this promo code
5. Checks if only for new users (only_new_users flag)
6. Calculates discount based on promo type:
   - `PERCENT`: (subtotal * value) / 100
   - `FIXED`: value amount
7. Ensures discount doesn't exceed subtotal

#### Order Creation (Requirement 7.1)
- Generates unique order number: `GP-YYYYMMDD-XXXXXXXX`
- Creates Order with:
  - `order_number`: unique identifier
  - `user_id`: authenticated user
  - `status`: NEW (or WAITING_PAYMENT)
  - `subtotal_amount`: sum of all items
  - `discount_amount`: promo code discount
  - `total_amount`: subtotal - discount
  - `promo_code_id`: linked promo code (if applied)
  - `idempotency_key`: for duplicate prevention

#### Order Items Creation
- Creates OrderItem for each cart item with:
  - `product_id`: reference to product
  - `title_snapshot`: product title at time of order
  - `quantity`: number of items
  - `unit_price`: price per item
  - `total_price`: unit_price * quantity
  - `fulfillment_type`: from product (auto/manual)

#### Audit Trail
- Creates OrderStatusHistory record:
  - `old_status`: None (new order)
  - `new_status`: NEW
  - `comment`: "Order created from cart"

#### Promo Code Usage Recording
If promo code applied:
- Creates PromoCodeUsage record
- Increments promo_code.used_count

#### Cart Cleanup
- Deletes all cart items after successful order creation
- Cart is cleared for next purchase

### 3. Updated _get_order_response Helper

Changed from Lot-based to Product-based:
- Loads OrderItem with Product (not Lot)
- Gets game info from Product.game_id
- Uses product title from title_snapshot
- Uses product_id as lot_id for API compatibility
- Default seller is "Game Pay" (seller_id=1)

## Data Flow

```
1. User submits order with idempotency_key and optional promo_code
2. Authenticate user via JWT token
3. Check for existing order with same idempotency_key
   - If exists: return existing order (idempotency)
4. Load user's cart and cart items
5. Validate all products are active and have prices
6. Calculate subtotal from product prices
7. If promo_code provided:
   - Validate promo code
   - Calculate discount
8. Calculate total_amount = subtotal - discount
9. Generate unique order_number
10. Create Order record
11. Create OrderItem records with product snapshots
12. Create OrderStatusHistory for audit
13. Record promo code usage (if applied)
14. Clear cart
15. Return order details
```

## Database Schema Used

### Order
- `order_number`: String(32), unique
- `user_id`: FK to users
- `status`: OrderStatus enum (NEW, WAITING_PAYMENT, etc.)
- `subtotal_amount`: Decimal(12,2)
- `discount_amount`: Decimal(12,2)
- `total_amount`: Decimal(12,2)
- `promo_code_id`: FK to promo_codes (nullable)
- `idempotency_key`: String(255), unique index

### OrderItem
- `order_id`: FK to orders
- `product_id`: FK to products (nullable)
- `title_snapshot`: String(255) - product title at order time
- `quantity`: Integer
- `unit_price`: Decimal(12,2)
- `total_price`: Decimal(12,2)
- `fulfillment_type`: FulfillmentType enum

### OrderStatusHistory
- `order_id`: FK to orders
- `old_status`: OrderStatus (nullable)
- `new_status`: OrderStatus
- `comment`: Text (nullable)

### PromoCodeUsage
- `promo_code_id`: FK to promo_codes
- `user_id`: FK to users
- `order_id`: FK to orders (nullable)

## API Endpoint

### POST /api/v1/orders

**Request:**
```json
{
  "idempotency_key": "unique-key-123",
  "promo_code": "SAVE10"  // optional
}
```

**Response:**
```json
{
  "id": 1,
  "status": "new",
  "total_amount": "450.00",
  "items": [
    {
      "id": 1,
      "lot_id": 5,  // product_id
      "lot_title": "Fortnite V-Bucks 1000",
      "lot_image_url": "https://i.imgur.com/...",
      "quantity": 2,
      "price_per_item": "250.00",
      "subtotal": "500.00",
      "seller_id": 1,
      "seller_name": "Game Pay"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Authentication:**
- Requires Bearer token in Authorization header
- Token obtained from /api/v1/auth/telegram endpoint

**Error Responses:**
- 400: Cart is empty
- 400: Product not available
- 400: Price not found
- 400: Promo code invalid/expired/used
- 401: Unauthorized (invalid/missing token)
- 404: Order not found (for GET requests)

## Testing

Created `test_order_creation.py` to verify:
1. Order creation without promo code
2. Idempotency check (duplicate prevention)
3. Order creation with promo code
4. Promo code usage recording

## Future Enhancements (P2P Marketplace)

When implementing P2P marketplace features:
1. Create separate Deal records for each seller
2. Implement escrow system
3. Add seller commission calculation
4. Support multiple sellers per order

## Notes

- Current implementation uses single seller (Game Pay)
- Order status starts as NEW (can be changed to WAITING_PAYMENT)
- Cart is cleared after order creation
- Promo codes are validated and recorded
- All amounts use Decimal for precision
- Order numbers are unique and timestamped
- Idempotency prevents duplicate orders from network retries
