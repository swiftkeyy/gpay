# Task 11.1: Product Review Creation Implementation

## Overview

Implemented the `POST /api/v1/orders/{id}/review` endpoint for creating product reviews with validation and moderation support.

## Requirements Implemented

### ✅ Requirement 11.1: POST /api/v1/orders/{id}/review endpoint
- Endpoint created in `api/routers/reviews.py`
- Accepts order ID as path parameter
- Returns created review with ID and status

### ✅ Requirement 11.3: Validate rating (1-5) and text (max 2000 chars)
- Rating validation: Must be between 1 and 5 (inclusive)
- Text validation: Maximum 2000 characters
- Text is optional (can be None)
- Pydantic model handles validation automatically

### ✅ Requirement 11.10: Set status to pending for moderation
- Reviews created with `ReviewStatus.HIDDEN` (serves as "pending" status)
- Admin must approve before review becomes `ReviewStatus.PUBLISHED`
- Can be rejected with `ReviewStatus.REJECTED`

### ⚠️ Requirement 11.4: Support up to 5 photos
**Status**: Not implemented - requires database schema update

**Reason**: The current `reviews` table does not have a field for storing photos. Implementation requires one of:
1. Add `photos` JSONB field to `reviews` table (stores array of media_file IDs)
2. Create separate `review_photos` table with foreign key to reviews

**Recommendation**: Add JSONB field for simplicity:
```sql
ALTER TABLE reviews ADD COLUMN photos JSONB DEFAULT '[]'::jsonb;
```

## Implementation Details

### Endpoint: POST /api/v1/orders/{id}/review

**Request Body**:
```json
{
  "rating": 5,
  "text": "Great product! Very satisfied with the purchase."
}
```

**Response** (201 Created):
```json
{
  "review_id": 123,
  "order_id": 456,
  "product_id": 789,
  "rating": 5,
  "text": "Great product! Very satisfied with the purchase.",
  "status": "pending",
  "message": "Review submitted for moderation",
  "created_at": "2024-01-20T12:00:00Z"
}
```

### Validation Rules

1. **Order Validation**:
   - Order must exist
   - User must be the order owner
   - Order status must be `COMPLETED`
   - Order must have at least one item

2. **Review Validation**:
   - Rating: 1-5 (enforced by Pydantic)
   - Text: Max 2000 characters (enforced by Pydantic)
   - Text: Optional field
   - No duplicate reviews (one review per order per user)

3. **Status Management**:
   - New reviews: `ReviewStatus.HIDDEN` (pending)
   - After admin approval: `ReviewStatus.PUBLISHED`
   - After admin rejection: `ReviewStatus.REJECTED`

### Error Responses

**404 Not Found**:
```json
{
  "detail": "Order not found"
}
```

**403 Forbidden**:
```json
{
  "detail": "You can only review your own orders"
}
```

**400 Bad Request** (Order not completed):
```json
{
  "detail": "Cannot review order with status 'new'. Order must be completed."
}
```

**400 Bad Request** (Duplicate review):
```json
{
  "detail": "You have already reviewed this order"
}
```

**422 Unprocessable Entity** (Validation error):
```json
{
  "detail": [
    {
      "loc": ["body", "rating"],
      "msg": "ensure this value is less than or equal to 5",
      "type": "value_error.number.not_le"
    }
  ]
}
```

## Code Changes

### Modified Files

1. **api/routers/reviews.py**
   - Updated imports to include proper models and enums
   - Fixed `ProductReviewCreate` model (removed photos field temporarily)
   - Rewrote `create_product_review` endpoint with proper validation
   - Added comprehensive error handling
   - Added detailed logging
   - Added docstring with requirements mapping

### Key Improvements

1. **Proper Status Handling**: Uses `ReviewStatus.HIDDEN` instead of string "pending"
2. **Order Status Check**: Uses `OrderStatus.COMPLETED` enum instead of string
3. **Product ID Extraction**: Gets product_id from order items (not directly from order)
4. **Comprehensive Validation**: Checks order ownership, completion, and duplicates
5. **Better Error Messages**: Clear, actionable error messages for users
6. **Logging**: Added structured logging for debugging and monitoring

## Testing

### Validation Tests

Created `test_review_validation.py` with comprehensive validation tests:

```
✅ PASS: Rating Validation (1-5)
✅ PASS: Text Length Validation (max 2000)
✅ PASS: Optional Text Field
✅ PASS: Review Model Structure

Total: 4/4 tests passed
```

### Test Coverage

- ✅ Rating range validation (1-5)
- ✅ Text length validation (max 2000 chars)
- ✅ Optional text field
- ✅ Model structure and serialization
- ✅ Invalid rating rejection (0, 6, -1, 10)
- ✅ Text length edge cases (0, 100, 1000, 2000, 2001 chars)

## Database Schema

### Current Schema (reviews table)

```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    text TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'hidden',
    moderated_by_admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    moderated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_reviews_status_created ON reviews(status, created_at);
```

### Required Schema Update for Photos

To support requirement 11.4 (up to 5 photos), add:

```sql
ALTER TABLE reviews ADD COLUMN photos JSONB DEFAULT '[]'::jsonb;
```

Then update the Pydantic model:
```python
class ProductReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    text: Optional[str] = Field(None, max_length=2000)
    photos: Optional[List[int]] = Field(None, max_items=5)  # Media file IDs
```

And update the Review entity:
```python
class Review(Base, TimestampMixin):
    # ... existing fields ...
    photos: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
```

## API Documentation

The endpoint is automatically documented in Swagger UI at `/docs`:

- **Path**: `/api/v1/orders/{order_id}/review`
- **Method**: POST
- **Tags**: Reviews
- **Authentication**: Required (Bearer token)
- **Request Body**: ProductReviewCreate schema
- **Responses**:
  - 201: Review created successfully
  - 400: Bad request (validation error, duplicate, order not completed)
  - 403: Forbidden (not your order)
  - 404: Order not found
  - 422: Validation error

## Future Enhancements

1. **Photo Support**:
   - Add database migration for photos field
   - Create photo upload endpoint
   - Validate photo file types and sizes
   - Store photos in media_files table
   - Link photos to reviews via JSONB array of IDs

2. **Multiple Products per Order**:
   - Currently assumes one product per order
   - Could support multiple reviews per order (one per product)
   - Would require UI changes to select which product to review

3. **Review Editing**:
   - Allow users to edit reviews before moderation
   - Track edit history
   - Prevent editing after publication

4. **Review Notifications**:
   - Notify seller when review is published
   - Notify admin when review needs moderation
   - Notify user when review is approved/rejected

## Conclusion

Task 11.1 is **successfully implemented** with the following status:

- ✅ POST /api/v1/orders/{id}/review endpoint
- ✅ Rating validation (1-5)
- ✅ Text validation (max 2000 chars)
- ✅ Status set to pending (HIDDEN) for moderation
- ✅ Order ownership validation
- ✅ Order completion check
- ✅ Duplicate review prevention
- ⚠️ Photo support requires database migration

The endpoint is production-ready for text reviews. Photo support can be added in a future task with a database migration.
