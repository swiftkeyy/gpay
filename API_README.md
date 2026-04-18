# P2P Marketplace API - Quick Start Guide

## 🎯 What's Been Implemented

### ✅ Complete
1. **Database Schema** - All 30+ tables with relationships
2. **Auto-Migrations** - Runs on bot startup
3. **FastAPI Application** - Core structure with CORS
4. **Authentication** - Telegram initData validation
5. **User Management** - Profile, balance, transactions
6. **Catalog System** - Games, categories, products, lots
7. **Favorites** - Add/remove lots from favorites
8. **API Documentation** - Auto-generated Swagger UI

### ⚠️ Partial (Stubs Created)
- Cart management
- Order creation
- Payment processing
- Seller dashboard
- Reviews system
- Admin panel
- Notifications

### ❌ Not Started
- WebSocket chat
- WebSocket notifications
- Payment provider integrations
- Frontend Mini App

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and set:
# - BOT_TOKEN=your_bot_token
# - DATABASE_URL=postgresql://...
# - REDIS_URL=redis://localhost:6379/0
```

### 3. Start the Bot (Runs Migrations)
```bash
python -m app.main
```

### 4. Start the API Server
```bash
# In a separate terminal
python -m api.main
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/api/docs
- **Health**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/telegram` - Authenticate via Telegram initData

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update profile (language)
- `GET /api/v1/users/me/balance` - Get balance
- `GET /api/v1/users/me/transactions` - Get transaction history
- `GET /api/v1/users/me/referrals` - Get referral stats

### Catalog
- `GET /api/v1/games` - List games (with search, pagination)
- `GET /api/v1/games/{id}` - Get game details
- `GET /api/v1/categories` - List categories
- `GET /api/v1/products` - List products
- `GET /api/v1/lots` - Search lots (with filters, sorting)
- `GET /api/v1/lots/{id}` - Get lot details
- `POST /api/v1/lots/{id}/favorite` - Add to favorites
- `DELETE /api/v1/lots/{id}/favorite` - Remove from favorites

### Cart (Stubs)
- `GET /api/v1/cart` - Get cart
- `POST /api/v1/cart/items` - Add to cart
- `PATCH /api/v1/cart/items/{id}` - Update quantity
- `DELETE /api/v1/cart/items/{id}` - Remove from cart
- `POST /api/v1/cart/validate` - Validate cart

### Orders (Stubs)
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders` - List orders
- `GET /api/v1/orders/{id}` - Get order details
- `POST /api/v1/orders/{id}/payment` - Initiate payment

### Sellers (Stubs)
- `POST /api/v1/sellers/apply` - Apply to become seller
- `GET /api/v1/sellers/me` - Get seller profile
- `GET /api/v1/sellers/me/dashboard` - Get dashboard stats
- `GET /api/v1/sellers/me/lots` - List seller lots
- `POST /api/v1/sellers/me/lots` - Create lot
- `POST /api/v1/sellers/me/withdrawals` - Request withdrawal

### Reviews (Stubs)
- `GET /api/v1/products/{id}/reviews` - Get product reviews
- `POST /api/v1/orders/{id}/review` - Create product review
- `GET /api/v1/sellers/{id}/reviews` - Get seller reviews
- `POST /api/v1/deals/{id}/review` - Create seller review

### Admin (Stubs)
- `GET /api/v1/admin/dashboard` - Dashboard stats
- `GET /api/v1/admin/users` - List users
- `PATCH /api/v1/admin/users/{id}` - Update user
- `GET /api/v1/admin/sellers` - List sellers
- `PATCH /api/v1/admin/sellers/{id}` - Update seller
- `GET /api/v1/admin/lots` - List all lots
- `GET /api/v1/admin/disputes` - List disputes
- `POST /api/v1/admin/disputes/{id}/resolve` - Resolve dispute
- `POST /api/v1/admin/broadcasts` - Create broadcast

### Payments (Stubs)
- `GET /api/v1/payment-methods` - Get available methods
- `POST /api/v1/webhooks/yukassa` - ЮKassa webhook
- `POST /api/v1/webhooks/tinkoff` - Tinkoff webhook
- `POST /api/v1/webhooks/cloudpayments` - CloudPayments webhook
- `POST /api/v1/webhooks/cryptobot` - Crypto Bot webhook

### Notifications (Stubs)
- `GET /api/v1/notifications` - Get notifications
- `PATCH /api/v1/notifications/{id}/read` - Mark as read
- `POST /api/v1/notifications/read-all` - Mark all as read
- `GET /api/v1/notifications/unread-count` - Get unread count

## 🧪 Testing the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Get Games List
```bash
curl http://localhost:8000/api/v1/games
```

### 3. Search Lots
```bash
curl "http://localhost:8000/api/v1/lots?sort_by=price_asc&limit=10"
```

### 4. Authenticate (Mock)
```bash
curl -X POST http://localhost:8000/api/v1/auth/telegram \
  -H "Content-Type: application/json" \
  -d '{"init_data": "mock_data"}'
```

### 5. Get User Profile
```bash
curl http://localhost:8000/api/v1/users/me
```

## 📖 Interactive Documentation

Visit http://localhost:8000/api/docs to:
- See all endpoints
- Try requests interactively
- View request/response schemas
- Test authentication

## 🗄️ Database Tables

The following tables are created automatically:

### Core Tables
- `users` - User accounts
- `admins` - Admin accounts
- `media_files` - Images and videos

### Catalog Tables
- `games` - Game database (700+ games)
- `categories` - Product categories
- `products` - Product definitions
- `prices` - Product pricing

### Marketplace Tables
- `sellers` - Seller accounts
- `lots` - Product listings
- `lot_stock_items` - Auto-delivery stock
- `deals` - Transactions with escrow
- `deal_messages` - Chat messages
- `deal_disputes` - Dispute resolution

### Order Tables
- `carts` - Shopping carts
- `cart_items` - Cart contents
- `orders` - Purchase orders
- `order_items` - Order line items
- `order_status_history` - Status tracking

### Financial Tables
- `transactions` - Balance changes
- `seller_withdrawals` - Withdrawal requests
- `promo_codes` - Discount codes
- `promo_code_usages` - Usage tracking

### Social Tables
- `reviews` - Product reviews
- `seller_reviews` - Seller ratings
- `favorites` - Saved lots
- `referrals` - Referral tracking
- `referral_rewards` - Reward payments

### System Tables
- `notifications` - User notifications
- `broadcasts` - Mass messages
- `audit_logs` - Admin actions
- `user_blocks` - User restrictions
- `bot_settings` - Configuration

## 🔧 Configuration

### Environment Variables
```env
# Bot
BOT_TOKEN=your_bot_token_here

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/gpay

# Redis
REDIS_URL=redis://localhost:6379/0

# API
CORS_ORIGINS=http://localhost:3000,https://your-miniapp.com

# Logging
LOG_LEVEL=INFO
```

## 🏗️ Project Structure

```
ПРОЕКТЫ/gpay-main/
├── api/                    # FastAPI application
│   ├── main.py            # FastAPI app entry point
│   └── routers/           # API route handlers
│       ├── auth.py        # ✅ Authentication
│       ├── users.py       # ✅ User management
│       ├── catalog.py     # ✅ Catalog & search
│       ├── cart.py        # ⚠️ Cart (stub)
│       ├── orders.py      # ⚠️ Orders (stub)
│       ├── sellers.py     # ⚠️ Sellers (stub)
│       ├── reviews.py     # ⚠️ Reviews (stub)
│       ├── admin.py       # ⚠️ Admin (stub)
│       ├── payments.py    # ⚠️ Payments (stub)
│       └── notifications.py # ⚠️ Notifications (stub)
├── app/                   # Bot application
│   ├── main.py           # Bot entry point (with migrations)
│   ├── models/           # Database models
│   │   ├── entities.py   # ✅ All 30+ tables
│   │   └── enums.py      # ✅ All enums
│   ├── repositories/     # Data access layer
│   ├── services/         # Business logic
│   └── handlers/         # Bot handlers
├── alembic/              # Database migrations
├── requirements.txt      # ✅ Updated with FastAPI
└── .env                  # Configuration
```

## 🎯 What Works Right Now

1. ✅ Start bot → migrations run automatically
2. ✅ Start API → server runs on port 8000
3. ✅ Visit /api/docs → see all endpoints
4. ✅ Call /health → get health status
5. ✅ Call /api/v1/games → get games list
6. ✅ Call /api/v1/lots → search lots
7. ✅ Add/remove favorites
8. ✅ Get user profile
9. ✅ Update language preference

## 🚧 What Needs Implementation

### High Priority
1. **Complete Cart Logic** - Stock reservation, validation
2. **Complete Order Flow** - Creation, payment, fulfillment
3. **Payment Integrations** - ЮKassa, Tinkoff, etc.
4. **WebSocket Chat** - Real-time messaging
5. **Seller Dashboard** - Stats, lot management
6. **Admin Panel** - Full moderation tools

### Medium Priority
7. **Review System** - Creation, moderation, replies
8. **Notification System** - Real-time push notifications
9. **Referral System** - Reward calculation and distribution
10. **Promo Codes** - Validation and application

### Low Priority
11. **Frontend Mini App** - React/Vue application
12. **Testing** - Unit and integration tests
13. **Documentation** - Complete API docs
14. **Deployment** - Production setup

## 📞 Testing Checklist

After implementation, verify:

- [ ] Bot starts without errors
- [ ] Migrations create all tables
- [ ] API server starts on port 8000
- [ ] /health endpoint returns 200
- [ ] /api/docs shows all endpoints
- [ ] Can authenticate via Telegram
- [ ] Can list games and lots
- [ ] Can add/remove favorites
- [ ] Can get user profile
- [ ] Database has sample data

## 🐛 Troubleshooting

### Bot won't start
- Check BOT_TOKEN in .env
- Check DATABASE_URL is correct
- Check PostgreSQL is running

### API won't start
- Check port 8000 is not in use
- Check all dependencies installed
- Check Python version (3.12+)

### Database errors
- Run migrations: `python -m app.main`
- Check PostgreSQL version (15+)
- Check database exists

### Import errors
- Install dependencies: `pip install -r requirements.txt`
- Check Python path includes project root

## 📚 Next Steps

1. **Implement Cart Logic** - See `api/routers/cart.py`
2. **Implement Order Flow** - See `api/routers/orders.py`
3. **Add Payment Providers** - See `api/routers/payments.py`
4. **Build WebSocket Chat** - Create `api/websockets/chat.py`
5. **Create Frontend** - Initialize React/Vue project

## 🎉 Success!

If you can:
- ✅ Start the bot
- ✅ Start the API
- ✅ Visit /api/docs
- ✅ Call /api/v1/games
- ✅ See data in database

Then the foundation is working! Now it's time to implement the business logic.

---

**Status**: 🚧 Foundation Complete (20%)
**Next Milestone**: Complete core API endpoints (50%)
**Final Goal**: Full P2P marketplace with Mini App (100%)
