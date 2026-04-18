# Design Document: P2P Marketplace Transformation (Telegram Mini App)

## Overview

This design transforms the existing Game Pay marketplace bot into a production-ready peer-to-peer (P2P) marketplace delivered as a Telegram Mini App. The architecture splits into a modern web frontend (React/Vue with Telegram WebApp SDK) and a robust backend (FastAPI REST API + aiogram bot for notifications).

The Mini App approach provides a native-like mobile experience with smooth animations, beautiful product galleries, real-time chat via WebSocket, and complex UI components (filters, sorting, cart) that would be impossible with inline buttons. Users get a seamless shopping experience with image galleries (up to 10 images per product), video previews, advanced search with autocomplete, and real-time order tracking.

The system supports 700+ games dynamically, enables any user to become a seller after verification, provides auto-delivery for digital goods, implements escrow protection for transactions, and delivers comprehensive seller dashboards with sales analytics, balance management, and buyer communication tools.

## Architecture

### High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        TG[Telegram Client]
        MINIAPP[Mini App Frontend<br/>React/Vue + WebApp SDK]
    end
    
    subgraph "Backend - API Layer"
        FASTAPI[FastAPI REST API]
        WS[WebSocket Server]
        BOT[aiogram Bot<br/>Notifications & Commands]
    end
    
    subgraph "Service Layer"
        US[User Service]
        SS[Seller Service]
        CS[Catalog Service]
        OS[Order Service]
        DS[Deal Service]
        PS[Payment Service]
        RS[Review Service]
        NS[Notification Service]
        AS[Admin Service]
        CACHE[Cache Service]
        CHAT[Chat Service]
    end
    
    subgraph "Repository Layer"
        UR[User Repo]
        SR[Seller Repo]
        CR[Catalog Repo]
        OR[Order Repo]
        DR[Deal Repo]
        PR[Payment Repo]
        RR[Review Repo]
        NR[Notification Repo]
        CHATR[Chat Repo]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        REDIS[(Redis)]
    end
    
    subgraph "External Services"
        YUKASSA[ЮKassa]
        TINKOFF[Tinkoff]
        CLOUD[CloudPayments]
        CRYPTO[Crypto Bot]
        TON[TON Blockchain]
    end
    
    TG --> MINIAPP
    MINIAPP -->|REST API| FASTAPI
    MINIAPP -->|WebSocket| WS
    TG -->|Bot Commands| BOT
    
    FASTAPI --> US
    FASTAPI --> SS
    FASTAPI --> CS
    FASTAPI --> OS
    FASTAPI --> DS
    FASTAPI --> PS
    FASTAPI --> RS
    FASTAPI --> AS
    
    WS --> CHAT
    WS --> NS
    
    BOT --> NS
    BOT --> US
    
    US --> UR
    SS --> SR
    CS --> CR
    OS --> OR
    DS --> DR
    PS --> PR
    RS --> RR
    NS --> NR
    CHAT --> CHATR
    
    US --> CACHE
    CS --> CACHE
    
    UR --> PG
    SR --> PG
    CR --> PG
    OR --> PG
    DR --> PG
    PR --> PG
    RR --> PG
    NR --> PG
    CHATR --> PG
    
    CACHE --> REDIS
    WS --> REDIS
    
    PS --> YUKASSA
    PS --> TINKOFF
    PS --> CLOUD
    PS --> CRYPTO
    PS --> TON
```

### Frontend Architecture (Telegram Mini App)

```mermaid
graph TB
    subgraph "Mini App Frontend"
        ROUTER[React Router / Vue Router]
        
        subgraph "Pages"
            HOME[Home/Catalog Page]
            PRODUCT[Product Detail Page]
            CART[Shopping Cart]
            CHECKOUT[Checkout Flow]
            ORDERS[Order History]
            SELLER[Seller Dashboard]
            PROFILE[User Profile]
            SEARCH[Search Page]
            CHAT[Chat Interface]
            REVIEWS[Reviews Page]
            ADMIN[Admin Panel]
        end
        
        subgraph "Components"
            PCARD[Product Card]
            GALLERY[Image Gallery]
            FILTER[Filters & Sort]
            PAYMENT[Payment Selector]
            STATS[Sales Stats]
            CHATUI[Chat UI]
            RATING[Rating Component]
        end
        
        subgraph "State Management"
            STORE[Zustand/Pinia Store]
            AUTH[Auth State]
            CARTST[Cart State]
            USERST[User State]
        end
        
        subgraph "API Layer"
            HTTP[Axios/Fetch Client]
            WSOCK[WebSocket Client]
            TGSDK[Telegram WebApp SDK]
        end
    end
    
    ROUTER --> HOME
    ROUTER --> PRODUCT
    ROUTER --> CART
    ROUTER --> CHECKOUT
    ROUTER --> ORDERS
    ROUTER --> SELLER
    ROUTER --> PROFILE
    ROUTER --> SEARCH
    ROUTER --> CHAT
    ROUTER --> REVIEWS
    ROUTER --> ADMIN
    
    HOME --> PCARD
    HOME --> FILTER
    PRODUCT --> GALLERY
    CART --> PCARD
    CHECKOUT --> PAYMENT
    SELLER --> STATS
    CHAT --> CHATUI
    REVIEWS --> RATING
    
    STORE --> AUTH
    STORE --> CARTST
    STORE --> USERST
    
    HTTP --> STORE
    WSOCK --> STORE
    TGSDK --> AUTH
```

**Tech Stack**:
- Framework: React 18+ with TypeScript OR Vue 3 with TypeScript
- UI Library: Material UI / Ant Design / Chakra UI
- State Management: Zustand (React) / Pinia (Vue)
- Routing: React Router v6 / Vue Router v4
- HTTP Client: Axios with interceptors
- WebSocket: native WebSocket API with reconnection logic
- Telegram SDK: @twa-dev/sdk
- Build Tool: Vite
- Styling: Tailwind CSS + CSS Modules

**Key Features**:
- Responsive design (mobile-first)
- Dark/Light theme toggle
- Multi-language support (i18n)
- Smooth page transitions
- Infinite scroll for catalog
- Image lazy loading
- Optimistic UI updates
- Offline detection
- Pull-to-refresh

### Backend Architecture (FastAPI + Bot)

```mermaid
graph TB
    subgraph "FastAPI Application"
        MAIN[Main App]
        
        subgraph "API Routers"
            AUTH_R[Auth Router]
            USER_R[User Router]
            CATALOG_R[Catalog Router]
            CART_R[Cart Router]
            ORDER_R[Order Router]
            SELLER_R[Seller Router]
            REVIEW_R[Review Router]
            ADMIN_R[Admin Router]
            PAYMENT_R[Payment Router]
        end
        
        subgraph "Middleware"
            CORS_M[CORS Middleware]
            AUTH_M[Auth Middleware]
            RATE_M[Rate Limit Middleware]
            LOG_M[Logging Middleware]
        end
        
        subgraph "WebSocket"
            WS_CHAT[Chat WebSocket]
            WS_NOTIF[Notification WebSocket]
        end
    end
    
    subgraph "Bot Application"
        BOT_MAIN[aiogram Bot]
        
        subgraph "Bot Handlers"
            START_H[/start Command]
            NOTIF_H[Notification Handler]
            QUICK_H[Quick Actions]
        end
    end
    
    MAIN --> AUTH_R
    MAIN --> USER_R
    MAIN --> CATALOG_R
    MAIN --> CART_R
    MAIN --> ORDER_R
    MAIN --> SELLER_R
    MAIN --> REVIEW_R
    MAIN --> ADMIN_R
    MAIN --> PAYMENT_R
    
    MAIN --> CORS_M
    MAIN --> AUTH_M
    MAIN --> RATE_M
    MAIN --> LOG_M
    
    MAIN --> WS_CHAT
    MAIN --> WS_NOTIF
    
    BOT_MAIN --> START_H
    BOT_MAIN --> NOTIF_H
    BOT_MAIN --> QUICK_H
```

**Tech Stack**:
- Framework: FastAPI 0.110+
- Bot Framework: aiogram 3.x
- ORM: SQLAlchemy 2.x (async)
- Database: PostgreSQL 15+
- Cache: Redis 7+
- Validation: Pydantic v2
- WebSocket: FastAPI native WebSocket support
- Task Queue: Celery (optional for heavy tasks)
- Migrations: Alembic

**API Design Principles**:
- RESTful endpoints
- JSON request/response
- JWT tokens for auth (optional, using Telegram initData)
- Pagination for list endpoints
- Filtering and sorting via query params
- Consistent error responses
- API versioning (/api/v1/)
- OpenAPI documentation (Swagger UI)

### Frontend-Backend Communication

#### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant MiniApp
    participant TelegramSDK
    participant FastAPI
    participant Database
    
    User->>MiniApp: Opens Mini App
    MiniApp->>TelegramSDK: Get initData
    TelegramSDK-->>MiniApp: initData + hash
    MiniApp->>FastAPI: POST /api/v1/auth/telegram<br/>{initData, hash}
    FastAPI->>FastAPI: Validate initData hash<br/>using bot token
    FastAPI->>Database: Get or create user
    Database-->>FastAPI: User data
    FastAPI-->>MiniApp: {access_token, user}
    MiniApp->>MiniApp: Store token in memory
    MiniApp->>FastAPI: Subsequent requests<br/>Authorization: Bearer {token}
```

**Authentication Implementation**:
1. Mini App retrieves `window.Telegram.WebApp.initData` on load
2. Sends initData to `/api/v1/auth/telegram` endpoint
3. Backend validates initData hash using HMAC-SHA256 with bot token
4. Backend creates or retrieves user from database
5. Backend returns access token (JWT) and user profile
6. Frontend stores token in memory (not localStorage for security)
7. All subsequent API requests include `Authorization: Bearer {token}` header

**Security Measures**:
- initData validation prevents spoofing
- Token expiration (24 hours)
- Token refresh mechanism
- Rate limiting per user
- CORS configuration for Mini App domain

#### REST API Endpoints

**User & Auth**:
- `POST /api/v1/auth/telegram` - Authenticate via Telegram initData
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update user profile
- `GET /api/v1/users/me/balance` - Get user balance
- `GET /api/v1/users/me/transactions` - Get transaction history
- `GET /api/v1/users/me/referrals` - Get referral stats

**Catalog**:
- `GET /api/v1/games` - List games with filters
- `GET /api/v1/games/{id}` - Get game details
- `GET /api/v1/categories` - List categories
- `GET /api/v1/products` - List products with filters
- `GET /api/v1/products/{id}` - Get product details
- `GET /api/v1/lots` - Search lots with filters & sorting
- `GET /api/v1/lots/{id}` - Get lot details
- `POST /api/v1/lots/{id}/favorite` - Add to favorites
- `DELETE /api/v1/lots/{id}/favorite` - Remove from favorites

**Cart & Checkout**:
- `GET /api/v1/cart` - Get user cart
- `POST /api/v1/cart/items` - Add item to cart
- `PATCH /api/v1/cart/items/{id}` - Update cart item quantity
- `DELETE /api/v1/cart/items/{id}` - Remove cart item
- `POST /api/v1/cart/validate` - Validate cart before checkout
- `POST /api/v1/orders` - Create order from cart
- `POST /api/v1/orders/{id}/payment` - Initiate payment

**Orders & Deals**:
- `GET /api/v1/orders` - List user orders
- `GET /api/v1/orders/{id}` - Get order details
- `GET /api/v1/deals/{id}` - Get deal details
- `POST /api/v1/deals/{id}/confirm` - Confirm delivery (buyer)
- `POST /api/v1/deals/{id}/deliver` - Deliver goods (seller)
- `POST /api/v1/deals/{id}/dispute` - Open dispute

**Seller**:
- `POST /api/v1/sellers/apply` - Apply to become seller
- `GET /api/v1/sellers/me` - Get seller profile
- `PATCH /api/v1/sellers/me` - Update seller profile
- `GET /api/v1/sellers/me/dashboard` - Get seller dashboard stats
- `GET /api/v1/sellers/me/lots` - List seller lots
- `POST /api/v1/sellers/me/lots` - Create new lot
- `PATCH /api/v1/sellers/me/lots/{id}` - Update lot
- `DELETE /api/v1/sellers/me/lots/{id}` - Delete lot
- `POST /api/v1/sellers/me/lots/{id}/stock` - Add stock items
- `POST /api/v1/sellers/me/withdrawals` - Request withdrawal

**Reviews**:
- `GET /api/v1/products/{id}/reviews` - Get product reviews
- `POST /api/v1/orders/{id}/review` - Create product review
- `GET /api/v1/sellers/{id}/reviews` - Get seller reviews
- `POST /api/v1/deals/{id}/review` - Create seller review
- `POST /api/v1/reviews/{id}/reply` - Reply to review (seller/admin)

**Admin**:
- `GET /api/v1/admin/dashboard` - Get dashboard stats
- `GET /api/v1/admin/users` - List users with filters
- `PATCH /api/v1/admin/users/{id}` - Update user (block, grant balance)
- `GET /api/v1/admin/sellers` - List sellers
- `PATCH /api/v1/admin/sellers/{id}` - Approve/suspend seller
- `GET /api/v1/admin/lots` - List all lots
- `PATCH /api/v1/admin/lots/{id}` - Moderate lot
- `GET /api/v1/admin/disputes` - List disputes
- `POST /api/v1/admin/disputes/{id}/resolve` - Resolve dispute
- `POST /api/v1/admin/broadcasts` - Create broadcast message
- `GET /api/v1/admin/audit-logs` - Get audit logs

#### WebSocket Communication

**Chat WebSocket** (`/ws/chat/{deal_id}`):
```typescript
// Client connects
ws = new WebSocket(`wss://api.example.com/ws/chat/${dealId}?token=${accessToken}`)

// Server sends message types
{
  "type": "message",
  "data": {
    "id": 123,
    "sender_id": 456,
    "text": "Hello",
    "created_at": "2024-01-01T12:00:00Z"
  }
}

{
  "type": "typing",
  "data": {
    "user_id": 456,
    "is_typing": true
  }
}

{
  "type": "read",
  "data": {
    "user_id": 456,
    "last_read_message_id": 123
  }
}

// Client sends messages
{
  "type": "send_message",
  "data": {
    "text": "Hello back",
    "media_id": null
  }
}

{
  "type": "typing",
  "data": {
    "is_typing": true
  }
}

{
  "type": "mark_read",
  "data": {
    "message_id": 123
  }
}
```

**Notification WebSocket** (`/ws/notifications`):
```typescript
// Client connects
ws = new WebSocket(`wss://api.example.com/ws/notifications?token=${accessToken}`)

// Server sends notifications
{
  "type": "notification",
  "data": {
    "id": 789,
    "title": "New Order",
    "message": "You have a new order #12345",
    "notification_type": "new_order",
    "reference_type": "order",
    "reference_id": 12345,
    "created_at": "2024-01-01T12:00:00Z"
  }
}

{
  "type": "order_status",
  "data": {
    "order_id": 12345,
    "status": "completed",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**WebSocket Features**:
- Automatic reconnection with exponential backoff
- Heartbeat/ping-pong to keep connection alive
- Message queuing during disconnection
- Optimistic UI updates
- Typing indicators
- Read receipts
- Online/offline status

### Frontend Pages & Components

#### 1. Home/Catalog Page

**Features**:
- Beautiful product cards with images, price, rating
- Category filters (horizontal scroll)
- Search bar with autocomplete
- Sort options (popularity, price, newest, rating)
- Infinite scroll pagination
- Pull-to-refresh
- Featured/boosted products section
- Quick filters (delivery type, price range)

**Components**:
- `ProductCard`: Image, title, price, rating, seller name, favorite button
- `CategoryFilter`: Horizontal scrollable category chips
- `SearchBar`: Input with autocomplete dropdown
- `SortDropdown`: Sort options selector
- `FilterDrawer`: Bottom sheet with advanced filters

#### 2. Product Detail Page

**Features**:
- Image gallery with swipe (up to 10 images)
- Video preview support
- Product title, description, price
- Seller info card (name, rating, sales count)
- Delivery type badge
- Stock availability indicator
- Add to cart button
- Quantity selector
- Reviews section with photos
- Similar products carousel
- Share button

**Components**:
- `ImageGallery`: Swipeable image carousel with thumbnails
- `VideoPlayer`: Video preview with controls
- `SellerCard`: Seller avatar, name, rating, link to profile
- `QuantitySelector`: +/- buttons with input
- `ReviewList`: Paginated reviews with photos
- `SimilarProducts`: Horizontal scroll carousel

#### 3. Shopping Cart Page

**Features**:
- List of cart items with images
- Quantity adjustment per item
- Remove item button
- Subtotal calculation
- Promo code input
- Discount display
- Total price
- Checkout button
- Empty cart state with suggestions

**Components**:
- `CartItem`: Product image, title, price, quantity selector, remove button
- `PromoCodeInput`: Input with apply button and validation
- `PriceBreakdown`: Subtotal, discount, total
- `CheckoutButton`: Sticky bottom button

#### 4. Checkout Flow

**Features**:
- Order summary
- Payment method selection (cards with icons)
- Delivery information display
- Terms acceptance checkbox
- Pay button
- Payment processing indicator
- Success/failure screens

**Components**:
- `OrderSummary`: List of items with total
- `PaymentMethodSelector`: Radio buttons with payment provider logos
- `PaymentProcessing`: Loading animation
- `PaymentSuccess`: Success animation with order number
- `PaymentFailure`: Error message with retry button

#### 5. Order History & Tracking

**Features**:
- List of orders with status badges
- Filter by status (all, pending, completed, canceled)
- Order details view
- Real-time status updates
- Chat with seller button
- Leave review button (after completion)
- Reorder button
- Order timeline

**Components**:
- `OrderCard`: Order number, date, status, total, items preview
- `OrderTimeline`: Visual timeline of order stages
- `StatusBadge`: Colored badge with status text
- `ChatButton`: Opens chat interface

#### 6. Seller Dashboard

**Features**:
- Sales statistics (today, week, month, all time)
- Revenue chart
- Balance display with withdraw button
- Active orders list
- Lot management (create, edit, delete)
- Stock management
- Chat with buyers
- Reviews received
- Performance metrics (rating, response time, completion rate)

**Components**:
- `SalesStats`: Cards with numbers and trends
- `RevenueChart`: Line/bar chart with date range selector
- `BalanceCard`: Balance amount with withdraw button
- `OrderList`: Filterable list of orders
- `LotManager`: CRUD interface for lots
- `StockManager`: Add/remove stock items
- `PerformanceMetrics`: Rating, badges, achievements

#### 7. User Profile Page

**Features**:
- User avatar and name
- Balance display with top-up button
- Referral code with share button
- Referral stats (invited users, earned rewards)
- Language selector
- Theme toggle (dark/light)
- Notification settings
- Order history link
- Favorites link
- Become seller button
- Logout button

**Components**:
- `ProfileHeader`: Avatar, name, edit button
- `BalanceCard`: Balance with top-up button
- `ReferralCard`: Code, share button, stats
- `SettingsSection`: Language, theme, notifications
- `MenuList`: Links to other pages

#### 8. Search Page

**Features**:
- Search input with autocomplete
- Recent searches
- Popular searches
- Search results with filters
- Sort options
- Empty state with suggestions

**Components**:
- `SearchInput`: Input with clear button
- `SearchSuggestions`: Dropdown with suggestions
- `SearchHistory`: List of recent searches
- `SearchResults`: Grid/list of products

#### 9. Chat Interface

**Features**:
- Message list with sender avatars
- Text input with send button
- Image upload button
- Typing indicator
- Read receipts
- Message timestamps
- Order info card at top
- Quick actions (confirm delivery, open dispute)

**Components**:
- `MessageList`: Scrollable message list
- `MessageBubble`: Text bubble with avatar and timestamp
- `MessageInput`: Text input with send and attachment buttons
- `TypingIndicator`: Animated dots
- `OrderInfoCard`: Order details at top of chat

#### 10. Review & Rating Interface

**Features**:
- Star rating selector (1-5)
- Text input for review
- Photo upload (up to 5 photos)
- Submit button
- Review preview
- Edit/delete own reviews

**Components**:
- `StarRating`: Interactive star selector
- `ReviewTextInput`: Textarea with character count
- `PhotoUploader`: Multiple photo upload with preview
- `ReviewPreview`: Preview before submission

#### 11. Admin Panel

**Features**:
- Dashboard with key metrics
- User management (list, search, block, grant balance)
- Seller management (approve, suspend)
- Lot moderation (approve, reject, edit)
- Dispute resolution
- Broadcast message creator
- Analytics charts
- Audit log viewer
- Bulk actions

**Components**:
- `AdminDashboard`: Cards with metrics and charts
- `UserTable`: Sortable table with actions
- `SellerTable`: Sortable table with approval actions
- `LotTable`: Sortable table with moderation actions
- `DisputeList`: List with resolve actions
- `BroadcastCreator`: Form to create broadcasts
- `AnalyticsCharts`: Various charts (revenue, users, orders)
- `AuditLogTable`: Filterable log table

### Bot Integration (aiogram)

The Telegram bot serves as a notification channel and provides quick access to the Mini App. It does NOT handle the main marketplace UI (that's the Mini App's job).

**Bot Commands**:
- `/start` - Welcome message with "Open Marketplace" button (opens Mini App)
- `/start {referral_code}` - Welcome with referral tracking
- `/orders` - Quick link to orders page in Mini App
- `/balance` - Show balance with top-up button
- `/help` - Help message with FAQ

**Bot Notifications**:
The bot sends push notifications for important events:
- New order received (for sellers)
- Order status changed
- New message in deal chat
- Payment received
- Review received
- Withdrawal processed
- System announcements

**Notification Format**:
```
🔔 New Order #12345

Product: Fortnite V-Bucks 1000
Price: 500 RUB
Buyer: @username

[Open Order] [Chat with Buyer]
```

**Bot Implementation**:
```python
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛍 Open Marketplace",
            web_app=WebAppInfo(url="https://miniapp.example.com")
        )],
        [InlineKeyboardButton(text="📱 My Orders", callback_data="orders")],
        [InlineKeyboardButton(text="💰 Balance", callback_data="balance")]
    ])
    
    await message.answer(
        "Welcome to Game Pay Marketplace!\n\n"
        "Buy and sell game items with escrow protection.",
        reply_markup=keyboard
    )

async def send_order_notification(user_id: int, order_id: int, order_data: dict):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Open Order",
            web_app=WebAppInfo(url=f"https://miniapp.example.com/orders/{order_id}")
        )],
        [InlineKeyboardButton(
            text="Chat with Buyer",
            web_app=WebAppInfo(url=f"https://miniapp.example.com/chat/{order_data['deal_id']}")
        )]
    ])
    
    await bot.send_message(
        user_id,
        f"🔔 New Order #{order_id}\n\n"
        f"Product: {order_data['product_name']}\n"
        f"Price: {order_data['price']} {order_data['currency']}\n"
        f"Buyer: @{order_data['buyer_username']}",
        reply_markup=keyboard
    )
```

## API Endpoints & Service Interfaces

### 1. User Management API

**REST Endpoints**:
- `POST /api/v1/auth/telegram` - Authenticate via Telegram initData
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update user profile
- `GET /api/v1/users/me/balance` - Get user balance
- `GET /api/v1/users/me/transactions` - Get transaction history
- `GET /api/v1/users/me/referrals` - Get referral stats

**Service Interface**:
```python
class UserService:
    async def authenticate_telegram_user(self, init_data: str, hash: str) -> AuthResult
    async def register_user(self, telegram_id: int, username: str | None, referral_code: str | None) -> User
    async def get_user(self, user_id: int) -> User | None
    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None
    async def update_profile(self, user_id: int, updates: UserProfileUpdate) -> User
    async def get_balance(self, user_id: int) -> Decimal
    async def add_balance(self, user_id: int, amount: Decimal, transaction_type: TransactionType) -> Transaction
    async def deduct_balance(self, user_id: int, amount: Decimal, transaction_type: TransactionType) -> Transaction
    async def generate_referral_code(self, user_id: int) -> str
    async def get_referral_stats(self, user_id: int) -> ReferralStats
    async def process_referral_reward(self, referrer_id: int, referred_id: int, order_id: int) -> ReferralReward
```

**Request/Response Models**:
```python
class TelegramAuthRequest(BaseModel):
    init_data: str
    hash: str

class AuthResult(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class UserProfile(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    balance: Decimal
    referral_code: str
    language_code: str
    created_at: datetime
```

**Responsibilities**:
- Telegram initData validation using HMAC-SHA256
- User registration with referral tracking
- Profile CRUD operations
- Balance management with transaction history
- Referral code generation and reward processing
- JWT token generation and validation

### 2. Seller Management API

**REST Endpoints**:
- `POST /api/v1/sellers/apply` - Apply to become seller
- `GET /api/v1/sellers/me` - Get seller profile
- `PATCH /api/v1/sellers/me` - Update seller profile
- `GET /api/v1/sellers/me/dashboard` - Get seller dashboard stats
- `GET /api/v1/sellers/{id}` - Get public seller profile
- `POST /api/v1/sellers/me/withdrawals` - Request withdrawal

**Service Interface**:
```python
class UserService:
    async def register_user(self, telegram_id: int, username: str | None, referral_code: str | None) -> User
    async def get_user(self, user_id: int) -> User | None
    async def update_profile(self, user_id: int, updates: UserProfileUpdate) -> User
    async def get_balance(self, user_id: int) -> Decimal
    async def add_balance(self, user_id: int, amount: Decimal, transaction_type: TransactionType) -> Transaction
    async def deduct_balance(self, user_id: int, amount: Decimal, transaction_type: TransactionType) -> Transaction
    async def generate_referral_code(self, user_id: int) -> str
    async def get_referral_stats(self, user_id: int) -> ReferralStats
    async def process_referral_reward(self, referrer_id: int, referred_id: int, order_id: int) -> ReferralReward
```

**Responsibilities**:
- User registration with referral tracking
- Profile CRUD operations
- Balance management with transaction history
- Referral code generation and reward processing
- User blocking and suspension
- Multi-language preference storage

### 3. Lot Management API

**Purpose**: Handle seller listings (lots) with dynamic fields, stock management, and delivery configuration.

**Interface**:
```python
class LotService:
    async def create_lot(self, seller_id: int, lot_data: LotCreate) -> Lot
    async def update_lot(self, lot_id: int, updates: LotUpdate) -> Lot
    async def delete_lot(self, lot_id: int) -> None
    async def get_lot(self, lot_id: int) -> Lot | None
    async def search_lots(self, filters: LotFilters, pagination: Pagination) -> PaginatedLots
    async def add_stock_items(self, lot_id: int, items: list[str]) -> list[LotStockItem]
    async def reserve_stock(self, lot_id: int, quantity: int) -> list[LotStockItem]
    async def release_stock(self, stock_item_ids: list[int]) -> None
    async def mark_stock_sold(self, stock_item_ids: list[int], deal_id: int) -> None
    async def boost_lot(self, lot_id: int, duration_hours: int) -> LotBoost
    async def upload_lot_images(self, lot_id: int, images: list[bytes]) -> list[MediaFile]
```

**Responsibilities**:
- Lot CRUD operations
- Stock inventory management
- Auto-delivery data configuration
- Multiple image uploads (up to 10)
- Lot boosting system
- Status management (draft, active, paused, out_of_stock)
- Delivery type configuration (auto, manual, coordinates)

### 4. Catalog & Discovery API

**REST Endpoints**:
- `GET /api/v1/games` - List games with filters
- `GET /api/v1/games/{id}` - Get game details
- `GET /api/v1/categories` - List categories
- `GET /api/v1/products` - List products with filters
- `GET /api/v1/lots` - Search lots with filters & sorting
- `GET /api/v1/lots/{id}` - Get lot details
- `POST /api/v1/lots/{id}/favorite` - Add to favorites
- `DELETE /api/v1/lots/{id}/favorite` - Remove from favorites
- `GET /api/v1/users/me/favorites` - Get user favorites

**Service Interface**:
```python
class CatalogService:
    async def get_games(self, filters: GameFilters, pagination: Pagination) -> PaginatedGames
    async def search_games(self, query: str, limit: int) -> list[Game]
    async def get_categories(self, game_id: int | None) -> list[Category]
    async def get_products(self, category_id: int | None, filters: ProductFilters) -> list[Product]
    async def search_lots(self, query: str, filters: LotSearchFilters, sort: SortOption) -> PaginatedLots
    async def get_featured_lots(self, limit: int) -> list[Lot]
    async def get_lot_details(self, lot_id: int) -> LotDetails
    async def add_to_favorites(self, user_id: int, lot_id: int) -> Favorite
    async def remove_from_favorites(self, user_id: int, lot_id: int) -> None
    async def get_user_favorites(self, user_id: int) -> list[Lot]
```

**Responsibilities**:
- Game database with 700+ entries
- Category and subcategory management
- Advanced search with autocomplete
- Multi-criteria filtering (game, category, price, delivery type, seller rating)
- Sorting options (popularity, price, newness, rating)
- Featured/boosted listings
- Favorites management
- Cache optimization for catalog queries

### 5. Shopping Cart API

**REST Endpoints**:
- `GET /api/v1/cart` - Get user cart
- `POST /api/v1/cart/items` - Add item to cart
- `PATCH /api/v1/cart/items/{id}` - Update cart item quantity
- `DELETE /api/v1/cart/items/{id}` - Remove cart item
- `DELETE /api/v1/cart` - Clear cart
- `POST /api/v1/cart/validate` - Validate cart before checkout
- `POST /api/v1/cart/apply-promo` - Apply promo code

**Service Interface**:
```python
class CartService:
    async def add_to_cart(self, user_id: int, lot_id: int, quantity: int) -> CartItem
    async def remove_from_cart(self, user_id: int, cart_item_id: int) -> None
    async def update_cart_item(self, cart_item_id: int, quantity: int) -> CartItem
    async def get_cart(self, user_id: int) -> Cart
    async def clear_cart(self, user_id: int) -> None
    async def calculate_cart_total(self, user_id: int, promo_code: str | None) -> CartTotal
    async def validate_cart(self, user_id: int) -> CartValidation
```

**Responsibilities**:
- Cart item management
- Quantity validation against stock
- Price calculation with promo codes
- Cart validation before checkout
- Automatic cart cleanup for expired reservations

### 6. Deal & Order API

**REST Endpoints**:
- `POST /api/v1/orders` - Create order from cart
- `GET /api/v1/orders` - List user orders
- `GET /api/v1/orders/{id}` - Get order details
- `POST /api/v1/orders/{id}/payment` - Initiate payment
- `GET /api/v1/deals/{id}` - Get deal details
- `POST /api/v1/deals/{id}/deliver` - Deliver goods (seller)
- `POST /api/v1/deals/{id}/confirm` - Confirm delivery (buyer)
- `POST /api/v1/deals/{id}/dispute` - Open dispute

**Service Interface**:
```python
class DealService:
    async def create_deal(self, order_id: int, buyer_id: int, seller_id: int, lot_id: int, amount: Decimal) -> Deal
    async def get_deal(self, deal_id: int) -> Deal | None
    async def update_deal_status(self, deal_id: int, status: DealStatus) -> Deal
    async def deliver_goods(self, deal_id: int, delivery_data: str, seller_id: int) -> Deal
    async def confirm_delivery(self, deal_id: int, buyer_id: int) -> Deal
    async def release_escrow(self, deal_id: int) -> Deal
    async def auto_complete_deal(self, deal_id: int) -> Deal
    async def open_dispute(self, deal_id: int, initiator_id: int, reason: str) -> Dispute
    async def resolve_dispute(self, dispute_id: int, resolution: str, admin_id: int) -> Dispute
    async def send_message(self, deal_id: int, sender_id: int, message: str, media_id: int | None) -> DealMessage
    async def get_messages(self, deal_id: int, pagination: Pagination) -> PaginatedMessages
    async def mark_messages_read(self, deal_id: int, user_id: int) -> None
```

**Responsibilities**:
- Deal creation from orders
- Escrow fund holding
- Buyer-seller chat system
- Auto-delivery for digital goods
- Manual delivery confirmation
- Auto-completion after timeout
- Dispute management
- Transaction recording

### 7. Payment API

**REST Endpoints**:
- `GET /api/v1/payment-methods` - Get available payment methods
- `POST /api/v1/payments` - Create payment
- `GET /api/v1/payments/{id}` - Get payment status
- `POST /api/v1/webhooks/yukassa` - ЮKassa webhook
- `POST /api/v1/webhooks/tinkoff` - Tinkoff webhook
- `POST /api/v1/webhooks/cloudpayments` - CloudPayments webhook
- `POST /api/v1/webhooks/cryptobot` - Crypto Bot webhook

**Service Interface**:
```python
class PaymentService:
    async def create_payment(self, user_id: int, amount: Decimal, payment_method: PaymentMethod, metadata: dict) -> Payment
    async def process_payment(self, payment_id: int) -> Payment
    async def verify_payment(self, payment_id: int, provider_data: dict) -> Payment
    async def refund_payment(self, payment_id: int, amount: Decimal, reason: str) -> Refund
    async def get_payment_methods(self, user_id: int) -> list[PaymentMethod]
    async def create_invoice(self, payment_id: int) -> Invoice
    async def handle_webhook(self, provider: str, payload: dict) -> WebhookResult
```

**Supported Payment Methods**:
- Telegram Stars (native)
- ЮKassa (cards, СБП, wallets)
- Tinkoff (cards, installments)
- CloudPayments (cards, Apple Pay, Google Pay)
- Crypto Bot (TON, USDT, BTC, ETH, etc.)
- Manual (QIWI, card transfers)

**Responsibilities**:
- Payment provider abstraction
- Invoice generation
- Webhook handling
- Payment verification
- Refund processing
- Transaction logging
- Currency conversion

### 8. Review & Rating API

**REST Endpoints**:
- `GET /api/v1/products/{id}/reviews` - Get product reviews
- `POST /api/v1/orders/{id}/review` - Create product review
- `GET /api/v1/sellers/{id}/reviews` - Get seller reviews
- `POST /api/v1/deals/{id}/review` - Create seller review
- `POST /api/v1/reviews/{id}/reply` - Reply to review
- `POST /api/v1/reviews/{id}/photos` - Upload review photos

**Service Interface**:
```python
class ReviewService:
    async def create_product_review(self, order_id: int, user_id: int, rating: int, text: str | None, photos: list[int]) -> Review
    async def create_seller_review(self, deal_id: int, buyer_id: int, seller_id: int, rating: int, text: str | None) -> SellerReview
    async def get_product_reviews(self, product_id: int, filters: ReviewFilters, pagination: Pagination) -> PaginatedReviews
    async def get_seller_reviews(self, seller_id: int, filters: ReviewFilters, pagination: Pagination) -> PaginatedReviews
    async def reply_to_review(self, review_id: int, reply_text: str, replier_id: int) -> Review
    async def moderate_review(self, review_id: int, status: ReviewStatus, admin_id: int) -> Review
    async def calculate_average_rating(self, entity_type: str, entity_id: int) -> Decimal
```

**Responsibilities**:
- Product review creation
- Seller review creation
- Photo attachment support
- Review moderation
- Seller/admin replies
- Rating calculation
- Review filtering and sorting

### 9. Notification API

**REST Endpoints**:
- `GET /api/v1/notifications` - Get user notifications
- `PATCH /api/v1/notifications/{id}/read` - Mark as read
- `POST /api/v1/notifications/read-all` - Mark all as read
- `GET /api/v1/notifications/unread-count` - Get unread count

**WebSocket Endpoint**: `/ws/notifications?token={access_token}`

**Service Interface**:
```python
class NotificationService:
    async def send_notification(self, user_id: int, notification_type: NotificationType, title: str, message: str, reference: Reference | None) -> Notification
    async def get_notifications(self, user_id: int, filters: NotificationFilters, pagination: Pagination) -> PaginatedNotifications
    async def mark_as_read(self, notification_id: int) -> Notification
    async def mark_all_as_read(self, user_id: int) -> None
    async def get_unread_count(self, user_id: int) -> int
    async def send_push(self, user_id: int, title: str, message: str) -> None
```

**Notification Types**:
- New message in deal chat
- New order for seller
- Order status change
- Payment received
- New review
- System announcements
- Price alerts

**Responsibilities**:
- Notification creation and delivery
- Push notification integration
- Read status tracking
- Notification preferences
- Batch notifications

### 10. Promo & Referral API

**REST Endpoints**:
- `GET /api/v1/promo-codes` - Get active promo codes
- `POST /api/v1/promo-codes/validate` - Validate promo code
- `POST /api/v1/cart/apply-promo` - Apply promo to cart

**Service Interface**:
```python
class PromoService:
    async def create_promo_code(self, code: str, promo_type: PromoType, value: Decimal, config: PromoConfig) -> PromoCode
    async def validate_promo_code(self, code: str, user_id: int, cart_total: Decimal) -> PromoValidation
    async def apply_promo_code(self, code: str, user_id: int, order_id: int) -> PromoCodeUsage
    async def calculate_discount(self, promo_code: PromoCode, amount: Decimal) -> Decimal
    async def get_active_promos(self, user_id: int) -> list[PromoCode]
    
    async def calculate_cashback(self, user_id: int, order_amount: Decimal) -> Decimal
    async def apply_cashback(self, user_id: int, order_id: int, amount: Decimal) -> Transaction
    
    async def calculate_referral_reward(self, referrer_id: int, order_amount: Decimal) -> Decimal
    async def apply_referral_reward(self, referrer_id: int, referred_id: int, order_id: int) -> ReferralReward
```

**Responsibilities**:
- Promo code CRUD
- Promo validation and application
- Discount calculation (percentage, fixed, gift product)
- Usage limit enforcement
- Cashback calculation
- Referral reward processing
- Bonus program management

### 11. Admin Panel API

**REST Endpoints**:
- `GET /api/v1/admin/dashboard` - Get dashboard stats
- `GET /api/v1/admin/users` - List users with filters
- `PATCH /api/v1/admin/users/{id}` - Update user (block, grant balance)
- `GET /api/v1/admin/sellers` - List sellers
- `PATCH /api/v1/admin/sellers/{id}` - Approve/suspend seller
- `GET /api/v1/admin/lots` - List all lots
- `PATCH /api/v1/admin/lots/{id}` - Moderate lot
- `GET /api/v1/admin/disputes` - List disputes
- `POST /api/v1/admin/disputes/{id}/resolve` - Resolve dispute
- `POST /api/v1/admin/broadcasts` - Create broadcast
- `GET /api/v1/admin/audit-logs` - Get audit logs
- `POST /api/v1/admin/bulk-actions` - Perform bulk actions

**Service Interface**:
```python
class AdminService:
    async def get_dashboard_stats(self, date_range: DateRange) -> DashboardStats
    async def get_revenue_analytics(self, date_range: DateRange, group_by: str) -> RevenueAnalytics
    async def get_top_sellers(self, limit: int, date_range: DateRange) -> list[SellerStats]
    async def get_top_products(self, limit: int, date_range: DateRange) -> list[ProductStats]
    
    async def bulk_grant_balance(self, user_ids: list[int], amount: Decimal, reason: str) -> list[Transaction]
    async def bulk_block_users(self, user_ids: list[int], reason: str, scope: BlockScope) -> list[UserBlock]
    async def bulk_boost_lots(self, lot_ids: list[int], duration_hours: int) -> list[LotBoost]
    
    async def log_action(self, admin_id: int, action: AuditAction, entity_type: str, entity_id: int, description: str, metadata: dict) -> AuditLog
    async def get_audit_logs(self, filters: AuditFilters, pagination: Pagination) -> PaginatedAuditLogs
    
    async def create_broadcast(self, message: str, media_id: int | None, scheduled_at: datetime | None) -> Broadcast
    async def send_broadcast(self, broadcast_id: int) -> BroadcastResult
```

**Responsibilities**:
- Analytics dashboard
- Revenue tracking
- Top sellers/products reports
- Bulk operations
- Audit logging
- Role management
- Broadcast messaging
- System configuration

## Data Models

### Core Entities

#### User
```python
class User:
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str
    balance: Decimal
    referral_code: str
    is_blocked: bool
    created_at: datetime
    updated_at: datetime
```

#### Seller
```python
class Seller:
    id: int
    user_id: int
    status: SellerStatus  # pending, active, suspended, banned
    shop_name: str
    description: str | None
    rating: Decimal
    total_sales: int
    total_reviews: int
    balance: Decimal
    commission_percent: Decimal
    is_verified: bool
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

#### Lot
```python
class Lot:
    id: int
    seller_id: int
    product_id: int
    title: str
    description: str | None
    price: Decimal
    currency_code: str
    delivery_type: LotDeliveryType  # auto, manual, coordinates
    stock_count: int
    reserved_count: int
    sold_count: int
    status: LotStatus  # draft, active, paused, out_of_stock, deleted
    auto_delivery_data: dict
    delivery_time_minutes: int | None
    is_featured: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
```

#### Deal
```python
class Deal:
    id: int
    order_id: int
    buyer_id: int
    seller_id: int
    lot_id: int
    status: DealStatus  # created, paid, in_progress, waiting_confirmation, completed, canceled, dispute, refunded
    amount: Decimal
    commission_amount: Decimal
    seller_amount: Decimal
    escrow_released: bool
    escrow_released_at: datetime | None
    auto_complete_at: datetime | None
    completed_at: datetime | None
    buyer_confirmed: bool
    buyer_confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

#### Transaction
```python
class Transaction:
    id: int
    user_id: int
    transaction_type: TransactionType  # deposit, purchase, sale, refund, withdrawal, commission, bonus, penalty
    amount: Decimal
    currency_code: str
    status: TransactionStatus  # pending, completed, failed, canceled
    balance_before: Decimal
    balance_after: Decimal
    description: str | None
    reference_type: str | None
    reference_id: int | None
    metadata_json: dict
    created_at: datetime
```

#### Review
```python
class Review:
    id: int
    order_id: int
    user_id: int
    rating: int  # 1-5
    text: str | None
    status: ReviewStatus  # pending, published, rejected
    admin_reply: str | None
    admin_replied_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

#### SellerReview
```python
class SellerReview:
    id: int
    seller_id: int
    deal_id: int
    buyer_id: int
    rating: int  # 1-5
    text: str | None
    status: ReviewStatus
    seller_reply: str | None
    seller_replied_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

### Validation Rules

#### User
- telegram_id: unique, positive integer
- balance: non-negative, max 2 decimal places
- referral_code: unique, 8-12 alphanumeric characters

#### Seller
- shop_name: 3-120 characters
- rating: 0.00-5.00, 2 decimal places
- commission_percent: 0.00-100.00, 2 decimal places
- balance: non-negative, max 2 decimal places

#### Lot
- title: 3-255 characters
- price: positive, max 2 decimal places
- stock_count: non-negative integer
- delivery_time_minutes: positive integer or null
- images: max 10 per lot

#### Deal
- amount: positive, max 2 decimal places
- commission_amount: non-negative, max 2 decimal places
- auto_complete_at: must be future datetime

#### Review
- rating: integer 1-5
- text: max 2000 characters
- photos: max 5 per review

## Error Handling

### Error Scenario 1: Insufficient Stock

**Condition**: User attempts to purchase lot with insufficient stock
**Response**: Return error message "Недостаточно товара на складе"
**Recovery**: Suggest similar lots or notify when back in stock

### Error Scenario 2: Payment Failure

**Condition**: Payment provider returns error or timeout
**Response**: Log error, notify user, release reserved stock
**Recovery**: Offer retry with same or different payment method

### Error Scenario 3: Seller Suspended

**Condition**: Seller account suspended during active deals
**Response**: Pause new orders, allow existing deals to complete
**Recovery**: Admin review and resolution

### Error Scenario 4: Escrow Release Failure

**Condition**: System fails to release escrow funds
**Response**: Log critical error, notify admin, retry with exponential backoff
**Recovery**: Manual admin intervention if retries fail

### Error Scenario 5: Duplicate Order

**Condition**: User submits same order twice (double-click)
**Response**: Use idempotency key to detect duplicate
**Recovery**: Return existing order instead of creating new one

### Error Scenario 6: Invalid Promo Code

**Condition**: User enters expired or invalid promo code
**Response**: Return specific error (expired, not found, already used, not eligible)
**Recovery**: Clear promo code field, allow retry

### Error Scenario 7: Chat Message Delivery Failure

**Condition**: Telegram API fails to deliver message
**Response**: Store message in database, mark as undelivered
**Recovery**: Retry delivery on next user interaction

### Error Scenario 8: Auto-Delivery Data Missing

**Condition**: Lot configured for auto-delivery but no stock items available
**Response**: Change lot status to out_of_stock, notify seller
**Recovery**: Seller adds stock items to resume sales

## Testing Strategy

### Unit Testing Approach

Each service layer component will have comprehensive unit tests covering:
- Happy path scenarios
- Edge cases (empty inputs, boundary values)
- Error conditions
- Business logic validation
- State transitions

**Key Test Cases**:
- User registration with/without referral
- Seller approval workflow
- Lot stock reservation and release
- Deal state machine transitions
- Payment processing with different providers
- Promo code validation logic
- Review rating calculations
- Transaction balance updates

**Coverage Goals**: Minimum 80% code coverage for service layer

### Property-Based Testing Approach

**Property Test Library**: hypothesis (Python)

**Properties to Test**:
1. Balance invariant: User balance always equals sum of completed transactions
2. Stock invariant: Available stock = total stock - reserved - sold
3. Escrow invariant: Total escrow held = sum of all in-progress deals
4. Commission calculation: Seller amount + commission = deal amount
5. Rating calculation: Average rating always between 1.00 and 5.00
6. Promo discount: Discounted price never negative or exceeds original
7. Referral rewards: Total rewards never exceed configured percentage
8. Transaction atomicity: Balance updates always paired with transaction records

### Integration Testing Approach

Integration tests will cover:
- Database operations with real PostgreSQL
- Redis caching and FSM state management
- Payment provider webhooks (mocked)
- Telegram Bot API interactions (mocked)
- End-to-end user flows (registration → browse → purchase → review)
- Admin operations with audit logging
- Concurrent order processing

**Test Scenarios**:
- Complete purchase flow with escrow
- Seller onboarding and first sale
- Dispute resolution workflow
- Broadcast message delivery
- Cart checkout with multiple items
- Promo code application
- Referral reward processing

## Performance Considerations

### Database Optimization
- Composite indexes on frequently queried columns (user_id + status, seller_id + created_at)
- Partial indexes for active lots (WHERE status = 'active')
- JSONB indexes for metadata searches
- Connection pooling with SQLAlchemy (min 5, max 20 connections)
- Query result caching for catalog data (5-minute TTL)

### Redis Caching Strategy
- Catalog cache: games, categories, featured lots (TTL: 5 minutes)
- User session cache: profile, balance, cart (TTL: 1 hour)
- Rate limiting: per-user request counters (TTL: 1 minute)
- FSM state: conversation states (TTL: 24 hours)
- Leaderboard cache: top sellers, top products (TTL: 15 minutes)

### Pagination
- Default page size: 10 items
- Maximum page size: 50 items
- Cursor-based pagination for large datasets
- Offset-based pagination for small datasets

### Concurrent Request Handling
- Async/await throughout the stack
- Database connection pooling
- Redis connection pooling
- Optimistic locking for stock updates
- Distributed locks for critical sections (escrow release)

### Performance Targets
- API response time: < 200ms (p95)
- Database query time: < 50ms (p95)
- Cache hit rate: > 80%
- Concurrent users: 1000+ without degradation
- Message throughput: 100+ messages/second

## Security Considerations

### Authentication & Authorization
- Telegram user ID as primary identifier
- No password storage (Telegram-based auth only)
- Role-based access control (RBAC) for admin panel
- Admin action audit logging
- Session management via Redis

### Data Protection
- SQL injection prevention via parameterized queries
- XSS protection via HTML escaping
- CSRF protection for webhook endpoints
- Sensitive data encryption at rest (payment details)
- PII anonymization in logs

### Payment Security
- Webhook signature verification
- Idempotency keys for payment operations
- Escrow fund isolation
- Transaction atomicity with database transactions
- Refund authorization checks

### Anti-Fraud Measures
- Rate limiting per user (10 requests/minute)
- IP-based blocking for suspicious activity
- Duplicate order detection
- Seller verification requirements
- Review spam detection
- Withdrawal limits and 2FA for large amounts

### API Security
- Webhook secret token validation
- HTTPS-only communication
- Request size limits
- Input validation and sanitization
- Error message sanitization (no stack traces to users)

## Dependencies

### Core Dependencies
- Python 3.12+
- aiogram 3.x (Telegram Bot framework)
- SQLAlchemy 2.x (async ORM)
- PostgreSQL 15+ (primary database)
- Redis 7+ (caching, FSM, rate limiting)
- pydantic 2.x (data validation)
- pydantic-settings (configuration management)

### Payment Provider SDKs
- yookassa (ЮKassa integration)
- tinkoff-acquiring (Tinkoff integration)
- cloudpayments (CloudPayments integration)
- aiocryptopay (Crypto Bot integration)
- tonutils (TON blockchain integration)

### Infrastructure
- Docker & docker-compose (containerization)
- Alembic (database migrations)
- structlog (structured logging)
- sentry-sdk (error tracking)
- prometheus-client (metrics)

### Development Tools
- pytest (testing framework)
- pytest-asyncio (async test support)
- hypothesis (property-based testing)
- black (code formatting)
- ruff (linting)
- mypy (type checking)

### Optional Integrations
- Sentry (error monitoring)
- Prometheus + Grafana (metrics and dashboards)
- Elasticsearch (search optimization)
- S3-compatible storage (media files)

### Frontend Dependencies
- React 18+ / Vue 3 with TypeScript
- @twa-dev/sdk (Telegram WebApp SDK)
- axios (HTTP client)
- zustand / pinia (state management)
- react-router-dom / vue-router (routing)
- @tanstack/react-query / @tanstack/vue-query (data fetching)
- tailwindcss (styling)
- vite (build tool)
- i18next / vue-i18n (internationalization)

## Deployment Strategy

### Frontend Deployment

**Hosting Options**:
- Vercel (recommended for React/Next.js)
- Netlify (recommended for Vue/Nuxt)
- GitHub Pages (static hosting)
- Cloudflare Pages (CDN + hosting)
- AWS S3 + CloudFront (custom setup)

**Build Process**:
```bash
# Install dependencies
npm install

# Build for production
npm run build

# Output: dist/ folder with static files
```

**Environment Variables**:
```env
VITE_API_BASE_URL=https://api.example.com
VITE_WS_BASE_URL=wss://api.example.com
VITE_BOT_USERNAME=@YourMarketplaceBot
```

**Deployment Steps**:
1. Build frontend with `npm run build`
2. Upload `dist/` folder to hosting provider
3. Configure custom domain (e.g., miniapp.example.com)
4. Enable HTTPS (required for Telegram Mini Apps)
5. Set up CDN for static assets
6. Configure CORS headers

**Telegram Mini App Configuration**:
1. Open @BotFather in Telegram
2. Send `/mybots` and select your bot
3. Select "Bot Settings" → "Menu Button"
4. Set Menu Button URL to `https://miniapp.example.com`
5. Test Mini App by opening bot and clicking menu button

### Backend Deployment

**Hosting Options**:
- Railway (recommended for quick deployment)
- Render (easy setup with free tier)
- DigitalOcean App Platform
- AWS ECS / EC2
- Google Cloud Run
- Heroku (legacy option)
- VPS (Ubuntu 22.04 LTS)

**Docker Setup**:
```dockerfile
# Dockerfile for FastAPI backend
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose**:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/marketplace
      - REDIS_URL=redis://redis:6379/0
      - BOT_TOKEN=${BOT_TOKEN}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db
      - redis
  
  bot:
    build: .
    command: python -m app.bot
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/marketplace
      - REDIS_URL=redis://redis:6379/0
      - BOT_TOKEN=${BOT_TOKEN}
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=marketplace
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**Environment Variables**:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/marketplace

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram Bot
BOT_TOKEN=your_bot_token_from_botfather
BOT_WEBHOOK_URL=https://api.example.com/webhooks/telegram

# JWT
JWT_SECRET=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
CORS_ORIGINS=https://miniapp.example.com

# Payment Providers
YUKASSA_SHOP_ID=your_shop_id
YUKASSA_SECRET_KEY=your_secret_key
TINKOFF_TERMINAL_KEY=your_terminal_key
TINKOFF_SECRET_KEY=your_secret_key
CLOUDPAYMENTS_PUBLIC_ID=your_public_id
CLOUDPAYMENTS_API_SECRET=your_api_secret
CRYPTOBOT_TOKEN=your_cryptobot_token
```

**Deployment Steps**:
1. Set up PostgreSQL database
2. Set up Redis instance
3. Configure environment variables
4. Run database migrations: `alembic upgrade head`
5. Deploy FastAPI application
6. Deploy bot application (separate process)
7. Configure webhook for bot (optional, can use polling)
8. Set up SSL certificate (Let's Encrypt)
9. Configure reverse proxy (Nginx)
10. Set up monitoring and logging

**Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Database Migrations

**Initial Setup**:
```bash
# Initialize Alembic
alembic init alembic

# Create first migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

**Migration Workflow**:
1. Make changes to SQLAlchemy models
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review generated migration file
4. Test migration on staging database
5. Apply to production: `alembic upgrade head`

### Monitoring & Logging

**Logging Setup**:
- Use structlog for structured logging
- Log levels: DEBUG (dev), INFO (prod)
- Log aggregation: Sentry, Datadog, or ELK stack
- Log rotation: logrotate or cloud provider

**Metrics**:
- Prometheus for metrics collection
- Grafana for dashboards
- Key metrics: request rate, error rate, response time, database connections, cache hit rate

**Health Checks**:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "timestamp": datetime.utcnow()
    }
```

**Alerts**:
- High error rate (> 5%)
- Slow response time (> 500ms p95)
- Database connection pool exhaustion
- Redis connection failures
- Payment webhook failures
- Escrow release failures

### Scaling Considerations

**Horizontal Scaling**:
- Run multiple FastAPI instances behind load balancer
- Use Redis for shared session state
- Use PostgreSQL read replicas for read-heavy queries
- Use CDN for static assets

**Vertical Scaling**:
- Increase server resources (CPU, RAM)
- Optimize database queries
- Add database indexes
- Increase connection pool sizes

**Caching Strategy**:
- Redis for hot data (catalog, user sessions)
- CDN for static assets (images, JS, CSS)
- Browser caching for API responses (Cache-Control headers)

**Database Optimization**:
- Connection pooling (min 5, max 20)
- Query optimization with EXPLAIN ANALYZE
- Indexes on frequently queried columns
- Partitioning for large tables (transactions, messages)
- Archiving old data

### Backup & Recovery

**Database Backups**:
- Automated daily backups
- Point-in-time recovery enabled
- Backup retention: 30 days
- Test restore procedure monthly

**Redis Backups**:
- RDB snapshots every 6 hours
- AOF (Append-Only File) for durability
- Backup retention: 7 days

**Disaster Recovery Plan**:
1. Database restore from latest backup
2. Redis restore from latest snapshot
3. Redeploy application from Git
4. Verify data integrity
5. Resume operations

### CI/CD Pipeline

**GitHub Actions Example**:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest
  
  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run build
      - uses: vercel/action@v1
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
  
  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/build-push-action@v4
        with:
          push: true
          tags: registry.example.com/marketplace:latest
```

### Cost Estimation

**Monthly Costs (Estimated)**:
- Frontend Hosting (Vercel/Netlify): $0-20
- Backend Hosting (Railway/Render): $20-50
- PostgreSQL Database: $15-50
- Redis Cache: $10-30
- Domain + SSL: $10-15
- CDN (Cloudflare): $0-20
- Monitoring (Sentry): $0-26
- Total: $55-211/month

**Scaling Costs**:
- 1000 users: ~$100/month
- 10,000 users: ~$300/month
- 100,000 users: ~$1000/month

## Benefits of Telegram Mini App Architecture

### User Experience Improvements

**Compared to Inline Buttons**:
- Native-like mobile interface with smooth animations
- Beautiful product galleries with swipe gestures (up to 10 images)
- Video previews for products
- Advanced filtering and sorting with intuitive UI
- Real-time search with autocomplete
- Shopping cart with multiple items
- Complex forms (seller registration, lot creation)
- Rich chat interface with typing indicators and read receipts
- Interactive charts and analytics for sellers
- Pull-to-refresh and infinite scroll
- Dark/light theme toggle
- Multi-language support with instant switching

**Technical Advantages**:
- Faster development with modern web frameworks (React/Vue)
- Reusable UI components from libraries (Material UI, Ant Design)
- Better state management (Zustand, Pinia)
- Easier testing (Jest, Vitest, Cypress)
- Hot reload during development
- TypeScript for type safety
- Better error handling and debugging
- Responsive design for all screen sizes

### Backend Improvements

**FastAPI Benefits**:
- Automatic API documentation (Swagger UI)
- Fast performance (async/await throughout)
- Type hints and validation with Pydantic
- Easy dependency injection
- Built-in WebSocket support
- OpenAPI schema generation
- Better error handling
- Easier to test and mock

**Separation of Concerns**:
- Frontend handles UI/UX
- Backend handles business logic
- Bot handles notifications only
- Clear API contracts between layers
- Independent deployment and scaling
- Easier to maintain and debug

### Development Workflow

**Frontend Development**:
- Use modern tooling (Vite, ESLint, Prettier)
- Component-driven development
- Storybook for component documentation
- Hot reload for instant feedback
- Easy to onboard new developers
- Large ecosystem of libraries

**Backend Development**:
- Clear API structure with routers
- Service layer for business logic
- Repository pattern for data access
- Easy to add new endpoints
- Automatic request validation
- Comprehensive error handling

### Scalability

**Frontend Scalability**:
- Static files served from CDN
- No server-side rendering needed
- Scales automatically with CDN
- Low hosting costs

**Backend Scalability**:
- Horizontal scaling with load balancer
- Stateless API (session in Redis)
- Database read replicas
- Redis caching for hot data
- WebSocket connections managed separately

### Future Extensibility

**Easy to Add**:
- New payment methods (just add provider integration)
- New features (just add API endpoints and UI components)
- Mobile apps (reuse same REST API)
- Third-party integrations (webhooks, APIs)
- Analytics and reporting
- A/B testing
- Push notifications
- Email notifications

**Migration Path**:
- Can gradually migrate from bot to Mini App
- Both can coexist during transition
- Bot can still handle simple commands
- Mini App handles complex workflows

### Comparison: Bot vs Mini App

| Feature | Inline Buttons Bot | Telegram Mini App |
|---------|-------------------|-------------------|
| UI Complexity | Limited | Rich & Complex |
| Image Gallery | Single image | Up to 10 images with swipe |
| Video Support | Limited | Full video player |
| Forms | Multi-step, clunky | Single page, smooth |
| Search | Basic text input | Autocomplete, filters |
| Cart | Difficult to implement | Native shopping cart |
| Real-time Updates | Polling | WebSocket |
| Animations | None | Smooth transitions |
| Theme Support | Limited | Dark/light mode |
| Development Speed | Slow | Fast |
| Maintenance | Difficult | Easy |
| Testing | Hard to automate | Easy with standard tools |
| User Experience | Acceptable | Excellent |
| Mobile Feel | Bot-like | Native app-like |

### Conclusion

The Telegram Mini App architecture provides a superior user experience, faster development, easier maintenance, and better scalability compared to a traditional inline buttons bot. While it requires more initial setup (frontend + backend), the long-term benefits far outweigh the costs. Users get a modern, intuitive interface that feels like a native mobile app, while developers get a clean separation of concerns and the ability to use modern web development tools and practices.


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authentication Hash Validation

*For any* initData string and hash pair, the authentication validation SHALL accept if and only if the hash is a valid HMAC-SHA256 of the initData using the bot token as secret.

**Validates: Requirements 1.2, 1.3, 29.1**

### Property 2: New User Initial State

*For any* new user registration, the created user record SHALL have balance equal to zero and a unique referral code between 8-12 alphanumeric characters.

**Validates: Requirements 1.4, 14.1**

### Property 3: Referral Association

*For any* valid referral code and new user, when the user registers with that referral code, the system SHALL create an association between the new user and the referrer.

**Validates: Requirement 1.8**

### Property 4: Balance Non-Negativity Invariant

*For any* sequence of balance operations (deposits, purchases, withdrawals, refunds), the user balance SHALL never become negative.

**Validates: Requirements 2.5, 13.2**

### Property 5: String Length Validation

*For any* input string being validated for length constraints, the validation SHALL accept if and only if the string length is within the specified minimum and maximum bounds (shop name: 3-120, lot title: 3-255, review text: max 2000).

**Validates: Requirements 3.6, 5.9, 11.10**

### Property 6: Price Validation

*For any* price value, the validation SHALL accept if and only if the price is positive and has at most 2 decimal places.

**Validates: Requirement 5.10**

### Property 7: Cart Stock Reservation

*For any* lot with available stock and quantity, adding the lot to cart SHALL decrease available stock by the quantity, and removing from cart SHALL increase available stock by the same quantity (round-trip property).

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 8: Order Idempotency

*For any* order creation request with an idempotency key, submitting the same request multiple times SHALL result in exactly one order being created, with subsequent requests returning the existing order.

**Validates: Requirement 7.8**

### Property 9: Escrow Amount Conservation

*For any* deal with escrow, the sum of seller_amount and commission_amount SHALL equal the original deal_amount when escrow is released.

**Validates: Requirement 8.7**

### Property 10: Escrow Transaction Records

*For any* escrow release operation, the system SHALL create exactly two transaction records: one for seller payment and one for commission deduction, with amounts matching the calculated seller_amount and commission_amount.

**Validates: Requirement 8.8**

### Property 11: Dispute Resolution Balance Update

*For any* dispute resolution, if resolved with seller payment, the seller balance SHALL increase by escrow amount; if resolved with buyer refund, the buyer balance SHALL increase by escrow amount.

**Validates: Requirements 10.6, 10.7**

### Property 12: Average Rating Calculation

*For any* set of published reviews with ratings, the calculated average rating SHALL equal the arithmetic mean of all rating values, rounded to 2 decimal places, and be between 1.00 and 5.00.

**Validates: Requirement 11.9**

### Property 13: Withdrawal Round-Trip

*For any* withdrawal request that fails, the withdrawn amount SHALL be refunded to the seller balance, restoring the balance to its pre-withdrawal value.

**Validates: Requirement 13.5**

### Property 14: Referral Code Uniqueness

*For any* set of registered users, all generated referral codes SHALL be unique (no two users have the same referral code).

**Validates: Requirement 14.1**

### Property 15: Referral Reward Balance Update

*For any* referral reward calculation, the referrer balance SHALL increase by exactly the calculated reward amount.

**Validates: Requirement 14.4**

### Property 16: Discount Non-Negativity

*For any* promo code application to a cart, the final discounted price SHALL never be negative, regardless of discount type or amount.

**Validates: Requirement 15.7**

### Property 17: Admin Balance Grant

*For any* admin balance grant operation, the user balance SHALL increase by the granted amount, and a transaction record SHALL be created with the correct amount and reason.

**Validates: Requirement 17.3**

### Property 18: Favorites Round-Trip

*For any* user and lot, adding the lot to favorites then removing it SHALL result in no favorite record existing for that user-lot pair.

**Validates: Requirements 21.1, 21.2**

### Property 19: Webhook Signature Validation

*For any* payment webhook with invalid signature, the system SHALL reject the webhook with HTTP status 403.

**Validates: Requirement 23.6**

### Property 20: Price Formatting

*For any* price value, the formatted display SHALL include exactly 2 decimal places and the currency symbol.

**Validates: Requirement 24.9**

### Property 21: Error Response Structure

*For any* error condition, the API response SHALL include error_code, message, and optional details fields in a consistent JSON structure.

**Validates: Requirement 26.7**

### Property 22: Transaction Record Completeness

*For any* balance change operation, a transaction record SHALL be created containing transaction_type, amount, balance_before, balance_after, and reference fields.

**Validates: Requirement 30.2**

### Property 23: Stock Availability Invariant

*For any* lot at any point in time, the relationship `available_stock = total_stock - reserved_stock - sold_stock` SHALL hold true.

**Validates: Requirements 5.8, 6.1, 6.2**

### Property 24: Balance Transaction Consistency

*For any* user at any point in time, the current balance SHALL equal the sum of all completed transaction amounts for that user.

**Validates: Requirements 2.5, 13.7, 30.2**

### Property 25: Escrow Conservation Invariant

*For any* point in time, the total escrow held by the system SHALL equal the sum of all deal amounts for deals in states: paid, in_progress, waiting_confirmation, or dispute.

**Validates: Requirements 8.1, 8.6, 10.2**
