# Task 6.3: Lot Boosting System Implementation

## Overview
Implemented a complete lot boosting system that allows sellers to promote their listings in search results by paying a fee. The system includes tiered pricing, balance management, transaction recording, and automatic boost expiration.

## Requirements Implemented

### ✅ Requirement 22.1: Boost Duration in Hours
- Endpoint accepts `duration_hours` parameter
- Validates duration is in allowed values: 24, 48, 72, or 168 hours
- Returns error for invalid durations

### ✅ Requirement 22.2: Deduct Boost Cost from Seller Balance
- Implements tiered pricing:
  - 24 hours: 100 RUB
  - 48 hours: 180 RUB (10% discount)
  - 72 hours: 250 RUB (15% discount)
  - 168 hours (1 week): 500 RUB (30% discount)
- Validates seller has sufficient balance before boosting
- Deducts cost from seller balance
- Creates transaction record with type `BOOST`
- Records balance before/after in transaction

### ✅ Requirement 22.3: Prioritize Boosted Lots in Search Results
- Updated catalog search endpoint to prioritize boosted lots
- Boosted lots (with `boosted_until > current_time`) appear first in all sort modes
- Uses SQLAlchemy `case` expression for efficient boost priority sorting
- Returns `is_boosted` and `boosted_until` fields in search results

### ✅ Requirement 22.4: Auto-Expire Boost After Duration
- Sets `boosted_until` timestamp to `current_time + duration_hours`
- Search query automatically filters expired boosts using `boosted_until > now`
- No manual expiration process needed - handled by query logic

## Changes Made

### 1. Database Schema Changes

#### Added to `app/models/entities.py`:
```python
class Lot(Base, TimestampMixin, SoftDeleteMixin):
    # ... existing fields ...
    boosted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

#### Added index for efficient querying:
```python
Index("ix_lots_boosted_until", "boosted_until")
```

### 2. Enum Updates

#### Added to `app/models/enums.py`:
```python
class TransactionType(StrEnum):
    # ... existing types ...
    BOOST = "boost"
```

### 3. API Endpoint Implementation

#### Updated `api/routers/sellers.py`:
```python
@router.post("/me/lots/{lot_id}/boost")
async def boost_lot(
    lot_id: int,
    request: LotBoostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
```

**Features:**
- Validates seller exists and owns the lot
- Validates duration is in allowed values (24, 48, 72, 168)
- Calculates boost cost based on tiered pricing
- Validates sufficient balance
- Prevents boosting already-boosted lots
- Deducts cost from seller balance
- Sets `boosted_until` timestamp
- Creates transaction record with metadata
- Returns boost details including cost, duration, expiration time, and remaining balance

**Request Body:**
```json
{
  "duration_hours": 24
}
```

**Response:**
```json
{
  "lot_id": 123,
  "boost_cost": 100.00,
  "duration_hours": 24,
  "boosted_until": "2024-01-02T12:00:00Z",
  "remaining_balance": 900.00,
  "transaction_id": 456
}
```

**Error Cases:**
- 404: Seller not found or lot not found
- 400: Invalid duration (not in allowed values)
- 400: Insufficient balance
- 400: Lot already boosted (must wait for expiration)

### 4. Search Integration

#### Updated `api/routers/catalog.py`:
```python
@router.get("/lots")
async def search_lots(...):
    # Create boost priority expression
    boost_priority = case(
        (Lot.boosted_until > now, 1),
        else_=0
    )
    
    # Apply to all sort modes
    if sort == "price_asc":
        query = query.order_by(boost_priority.desc(), Lot.price.asc())
    elif sort == "price_desc":
        query = query.order_by(boost_priority.desc(), Lot.price.desc())
    # ... etc for all sort modes
```

**Features:**
- Boosted lots always appear first regardless of sort mode
- Returns `is_boosted` and `boosted_until` in response
- Efficient query using SQLAlchemy case expression
- No additional database queries needed

### 5. Database Migration

#### Created migration: `4fa7210713d6_add_boosted_until_to_lots.py`
```python
def upgrade() -> None:
    # Add boosted_until column
    op.add_column('lots', sa.Column('boosted_until', sa.DateTime(timezone=True), nullable=True))
    
    # Create index
    op.create_index('ix_lots_boosted_until', 'lots', ['boosted_until'], unique=False)
    
    # Add BOOST transaction type
    op.execute("ALTER TYPE transaction_type_enum ADD VALUE IF NOT EXISTS 'boost'")
```

### 6. Test Suite

#### Created `test_lot_boosting.py`:
Tests:
- ✅ Boost lot with valid duration
- ✅ Validate boost cost calculation
- ✅ Verify balance deduction
- ✅ Check transaction record creation
- ✅ Verify boosted lots appear first in search
- ✅ Test pricing tiers (24h, 48h, 72h, 168h)
- ✅ Verify boost status and expiration

## Boost Pricing Tiers

| Duration | Price | Discount | Price per Hour |
|----------|-------|----------|----------------|
| 24 hours | 100 RUB | 0% | 4.17 RUB/h |
| 48 hours | 180 RUB | 10% | 3.75 RUB/h |
| 72 hours | 250 RUB | 15% | 3.47 RUB/h |
| 168 hours (1 week) | 500 RUB | 30% | 2.98 RUB/h |

## Transaction Record Example

```json
{
  "id": 456,
  "user_id": 123,
  "transaction_type": "boost",
  "amount": -100.00,
  "currency_code": "RUB",
  "status": "completed",
  "balance_before": 1000.00,
  "balance_after": 900.00,
  "description": "Boost lot #789 'Fortnite V-Bucks' for 24 hours",
  "reference_type": "lot",
  "reference_id": 789,
  "metadata_json": {
    "lot_id": 789,
    "lot_title": "Fortnite V-Bucks",
    "duration_hours": 24,
    "boost_cost": 100.00,
    "boosted_until": "2024-01-02T12:00:00Z"
  },
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Search Result Example

```json
{
  "items": [
    {
      "id": 789,
      "title": "Fortnite V-Bucks",
      "price": 500.00,
      "is_boosted": true,
      "boosted_until": "2024-01-02T12:00:00Z",
      "is_featured": false,
      "seller_rating": 4.5
    },
    {
      "id": 790,
      "title": "Roblox Robux",
      "price": 300.00,
      "is_boosted": false,
      "boosted_until": null,
      "is_featured": true,
      "seller_rating": 4.8
    }
  ]
}
```

## API Documentation

### POST /api/v1/sellers/me/lots/{lot_id}/boost

Boost a lot to prioritize it in search results.

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `lot_id` (integer): ID of the lot to boost

**Request Body:**
```json
{
  "duration_hours": 24  // Must be 24, 48, 72, or 168
}
```

**Response (200 OK):**
```json
{
  "lot_id": 123,
  "boost_cost": 100.00,
  "duration_hours": 24,
  "boosted_until": "2024-01-02T12:00:00Z",
  "remaining_balance": 900.00,
  "transaction_id": 456
}
```

**Error Responses:**
- `404 Not Found`: Seller not found or lot not found
- `400 Bad Request`: Invalid duration, insufficient balance, or lot already boosted
- `403 Forbidden`: Seller account not active

## Testing Instructions

### 1. Run the test suite:
```bash
cd ПРОЕКТЫ/gpay-main
python test_lot_boosting.py
```

### 2. Manual API testing:

#### Boost a lot:
```bash
curl -X POST http://localhost:8000/api/v1/sellers/me/lots/123/boost \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration_hours": 24}'
```

#### Search lots (boosted appear first):
```bash
curl http://localhost:8000/api/v1/lots?sort=popularity
```

### 3. Verify in database:
```sql
-- Check boosted lots
SELECT id, title, boosted_until, 
       CASE WHEN boosted_until > NOW() THEN 'active' ELSE 'expired' END as boost_status
FROM lots
WHERE boosted_until IS NOT NULL
ORDER BY boosted_until DESC;

-- Check boost transactions
SELECT id, user_id, amount, description, created_at
FROM transactions
WHERE transaction_type = 'boost'
ORDER BY created_at DESC;
```

## Migration Instructions

### Apply the migration:
```bash
cd ПРОЕКТЫ/gpay-main
python -m alembic upgrade head
```

### Rollback if needed:
```bash
python -m alembic downgrade -1
```

## Implementation Notes

1. **Boost Expiration**: Handled automatically by query logic - no background job needed
2. **Concurrent Boosts**: Prevented by checking if lot is already boosted
3. **Balance Validation**: Ensures seller has sufficient funds before deducting
4. **Transaction Integrity**: Uses database transaction to ensure atomicity
5. **Search Performance**: Index on `boosted_until` ensures efficient queries
6. **Pricing Strategy**: Tiered pricing encourages longer boost durations

## Future Enhancements

1. **Extend Boost**: Allow extending an active boost instead of blocking
2. **Boost Analytics**: Track boost effectiveness (views, clicks, conversions)
3. **Boost History**: Show seller's past boosts and their performance
4. **Auto-Renewal**: Option to automatically renew boost when it expires
5. **Boost Packages**: Bundle multiple boosts at discounted rates
6. **Featured Boost**: Premium boost tier that also sets `is_featured` flag

## Validation Checklist

- ✅ Requirement 22.1: Duration in hours accepted and validated
- ✅ Requirement 22.2: Boost cost deducted from seller balance
- ✅ Requirement 22.3: Boosted lots prioritized in search results
- ✅ Requirement 22.4: Boost auto-expires after duration
- ✅ Transaction record created with proper metadata
- ✅ Balance validation prevents insufficient funds
- ✅ Error handling for all edge cases
- ✅ API documentation complete
- ✅ Test suite created and passing
- ✅ Database migration created

## Status: ✅ COMPLETE

All requirements for Task 6.3 have been successfully implemented and tested.
