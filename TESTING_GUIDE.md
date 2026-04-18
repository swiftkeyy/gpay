# Testing Guide - P2P Marketplace

## 🎯 Quick Test Checklist

Run these tests to verify everything works:

### ✅ 1. Bot Startup Test
```bash
python -m app.main
```

**Expected output:**
```
🔄 Checking database migrations...
✅ Migrations applied successfully!
INFO | Bot started successfully
```

**What to check:**
- [ ] No errors in console
- [ ] Bot responds to /start in Telegram
- [ ] Database tables created

### ✅ 2. API Startup Test
```bash
python -m api.main
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Starting FastAPI application...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**What to check:**
- [ ] Server starts without errors
- [ ] Port 8000 is listening
- [ ] No import errors

### ✅ 3. Health Check Test
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "p2p-marketplace-api"
}
```

### ✅ 4. API Documentation Test
Open in browser:
```
http://localhost:8000/api/docs
```

**What to check:**
- [ ] Swagger UI loads
- [ ] See all endpoints listed
- [ ] Can expand endpoint details
- [ ] See request/response schemas

### ✅ 5. Games List Test
```bash
curl http://localhost:8000/api/v1/games
```

**Expected response:**
```json
[
  {
    "id": 1,
    "title": "Brawl Stars",
    "description": "...",
    "image_url": null,
    "is_active": true
  },
  ...
]
```

### ✅ 6. Lots Search Test
```bash
curl "http://localhost:8000/api/v1/lots?sort_by=price_asc&limit=5"
```

**Expected response:**
```json
[
  {
    "id": 1,
    "title": "...",
    "price": 100.00,
    "currency_code": "RUB",
    "seller_id": 1,
    "delivery_type": "auto",
    "stock_count": 10,
    "status": "active"
  },
  ...
]
```

### ✅ 7. User Profile Test
```bash
curl http://localhost:8000/api/v1/users/me
```

**Expected response:**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "testuser",
  "first_name": "Test",
  "balance": 0.00,
  "referral_code": "ABC123XYZ",
  "language_code": "ru",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### ✅ 8. Database Tables Test
```sql
-- Connect to PostgreSQL
psql -U your_user -d gpay

-- List all tables
\dt

-- Should see 30+ tables including:
-- sellers, lots, deals, transactions, etc.
```

## 🔍 Detailed Testing

### Test 1: Bot Commands

**Start bot:**
```bash
python -m app.main
```

**In Telegram, send:**
```
/start
```

**Expected:**
- Welcome message with inline buttons
- Catalog navigation works
- Cart works
- Profile works

### Test 2: Database Schema

**Check tables exist:**
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Expected tables:**
```
admins
audit_logs
bot_settings
broadcasts
cart_items
carts
categories
deal_disputes
deal_messages
deals
favorites
games
lot_stock_items
lots
media_files
notifications
order_items
order_status_history
orders
prices
products
promo_code_usages
promo_codes
referral_rewards
referrals
reviews
seller_reviews
seller_withdrawals
sellers
transactions
user_blocks
users
```

### Test 3: API Endpoints

**Test each endpoint:**

```bash
# Health
curl http://localhost:8000/health

# Games
curl http://localhost:8000/api/v1/games
curl http://localhost:8000/api/v1/games/1

# Categories
curl http://localhost:8000/api/v1/categories
curl "http://localhost:8000/api/v1/categories?game_id=1"

# Products
curl http://localhost:8000/api/v1/products
curl "http://localhost:8000/api/v1/products?category_id=1"

# Lots
curl http://localhost:8000/api/v1/lots
curl http://localhost:8000/api/v1/lots/1
curl "http://localhost:8000/api/v1/lots?sort_by=price_asc"
curl "http://localhost:8000/api/v1/lots?min_price=100&max_price=500"

# User
curl http://localhost:8000/api/v1/users/me
curl http://localhost:8000/api/v1/users/me/balance
curl http://localhost:8000/api/v1/users/me/transactions
curl http://localhost:8000/api/v1/users/me/referrals

# Favorites
curl -X POST http://localhost:8000/api/v1/lots/1/favorite
curl -X DELETE http://localhost:8000/api/v1/lots/1/favorite

# Cart (stubs)
curl http://localhost:8000/api/v1/cart
curl -X POST http://localhost:8000/api/v1/cart/items \
  -H "Content-Type: application/json" \
  -d '{"lot_id": 1, "quantity": 1}'

# Orders (stubs)
curl http://localhost:8000/api/v1/orders
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"idempotency_key": "test123"}'

# Sellers (stubs)
curl http://localhost:8000/api/v1/sellers/me
curl -X POST http://localhost:8000/api/v1/sellers/apply \
  -H "Content-Type: application/json" \
  -d '{"shop_name": "My Shop", "description": "Test shop"}'

# Admin (stubs)
curl http://localhost:8000/api/v1/admin/dashboard
curl http://localhost:8000/api/v1/admin/users
curl http://localhost:8000/api/v1/admin/sellers

# Payments (stubs)
curl http://localhost:8000/api/v1/payment-methods

# Notifications (stubs)
curl http://localhost:8000/api/v1/notifications
curl http://localhost:8000/api/v1/notifications/unread-count
```

### Test 4: Interactive API Testing

1. Open http://localhost:8000/api/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. See response

**Try these:**
- GET /api/v1/games
- GET /api/v1/lots with filters
- GET /api/v1/users/me
- POST /api/v1/lots/{id}/favorite

### Test 5: Error Handling

**Test 404:**
```bash
curl http://localhost:8000/api/v1/games/99999
```

**Expected:**
```json
{
  "detail": "Game not found"
}
```

**Test invalid endpoint:**
```bash
curl http://localhost:8000/api/v1/invalid
```

**Expected:**
```json
{
  "detail": "Not Found"
}
```

## 🐛 Troubleshooting

### Problem: Bot won't start

**Error:** `asyncpg.exceptions.InvalidCatalogNameError`

**Solution:**
```bash
# Create database
createdb gpay

# Or in psql:
CREATE DATABASE gpay;
```

### Problem: API won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: Port already in use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8001
```

### Problem: Database connection failed

**Error:** `asyncpg.exceptions.InvalidPasswordError`

**Solution:**
```bash
# Check .env file
cat .env | grep DATABASE_URL

# Should be:
DATABASE_URL=postgresql://user:password@localhost:5432/gpay

# Test connection
psql -U user -d gpay
```

### Problem: No data in database

**Solution:**
```bash
# Run seed script
python seed.py

# Or manually add data via bot admin panel
# /admin -> Add game/category/product
```

## ✅ Success Criteria

Your implementation is working if:

- [ ] Bot starts without errors
- [ ] Bot responds to /start
- [ ] API starts on port 8000
- [ ] /health returns 200
- [ ] /api/docs shows all endpoints
- [ ] Can get games list
- [ ] Can search lots
- [ ] Can add/remove favorites
- [ ] Can get user profile
- [ ] Database has 30+ tables
- [ ] No errors in logs

## 📊 Test Results Template

```
# Test Results - P2P Marketplace

Date: ___________
Tester: ___________

## Bot Tests
- [ ] Bot starts: ___________
- [ ] /start works: ___________
- [ ] Migrations applied: ___________
- [ ] No errors: ___________

## API Tests
- [ ] API starts: ___________
- [ ] Health check: ___________
- [ ] Documentation: ___________
- [ ] Games endpoint: ___________
- [ ] Lots endpoint: ___________
- [ ] User endpoint: ___________
- [ ] Favorites work: ___________

## Database Tests
- [ ] Tables created: ___________
- [ ] Sample data exists: ___________
- [ ] Indexes created: ___________

## Issues Found
1. ___________
2. ___________
3. ___________

## Overall Status
- [ ] ✅ All tests passed
- [ ] ⚠️ Some tests failed
- [ ] ❌ Major issues found

Notes:
___________
___________
___________
```

## 🎯 Next Steps After Testing

If all tests pass:
1. ✅ Foundation is solid
2. ✅ Ready to implement business logic
3. ✅ Can start building features

If tests fail:
1. ❌ Check error messages
2. ❌ Review troubleshooting section
3. ❌ Fix issues before proceeding

## 📞 Getting Help

If stuck:
1. Check error logs
2. Review IMPLEMENTATION_SUMMARY.md
3. Check API_README.md
4. Review ЧТО_ИЗМЕНИЛОСЬ.md

---

**Happy Testing! 🚀**
