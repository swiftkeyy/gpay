# Implementation Plan: P2P Marketplace Transformation (Telegram Mini App)

## Overview

This implementation plan transforms the existing Game Pay bot into a production-ready P2P marketplace with Telegram Mini App frontend, FastAPI REST API backend, and aiogram bot for notifications. The system supports 700+ games, seller verification, auto-delivery, escrow protection, real-time chat, reviews, and comprehensive dashboards.

## Tasks

- [x] 1. Database schema and models for P2P marketplace
  - Create Alembic migration for new tables: sellers, lots, lot_stock_items, lot_images, deals, deal_messages, seller_reviews, favorites, promo_codes, promo_code_usages, referral_rewards, withdrawals, notifications, audit_logs
  - Add new columns to users table: referral_code, is_blocked
  - Add new columns to orders table: promo_code_id, idempotency_key
  - Create indexes on frequently queried columns (user_id, seller_id, status, created_at)
  - _Requirements: 1.4, 3.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1, 13.1, 14.1, 15.1, 16.1, 17.1, 30.1_

- [ ] 2. FastAPI application setup and structure
  - [x] 2.1 Create FastAPI app with CORS middleware
    - Set up main FastAPI application in `api/main.py`
    - Configure CORS for Mini App domain
    - Add logging middleware
    - Add rate limiting middleware
    - _Requirements: 29.5, 29.7_
  
  - [x] 2.2 Create API router structure
    - Create routers: auth, users, catalog, cart, orders, sellers, reviews, admin, payments, notifications
    - Mount routers with `/api/v1` prefix
    - _Requirements: All API requirements_
  
  - [x] 2.3 Set up Pydantic models for requests/responses
    - Create schemas for all API endpoints
    - Add validation rules (string lengths, price formats, ratings)
    - _Requirements: 3.6, 5.9, 5.10, 11.10_

- [ ] 3. Authentication and user management
  - [x] 3.1 Implement Telegram initData validation
    - Create auth service with HMAC-SHA256 validation
    - Validate initData hash using bot token
    - Return 401 for invalid hash
    - _Requirements: 1.1, 1.2, 1.3, 29.1_
  
  - [x] 3.2 Implement user registration with referral tracking
    - Create user record with zero balance
    - Generate unique 8-12 character referral code
    - Associate new user with referrer if referral code provided
    - _Requirements: 1.4, 1.8, 14.1, 14.2_
  
  - [x] 3.3 Implement user profile management
    - GET /api/v1/users/me endpoint
    - PATCH /api/v1/users/me endpoint for language preference
    - GET /api/v1/users/me/balance endpoint
    - GET /api/v1/users/me/transactions endpoint with pagination
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 4. Seller management system
  - [x] 4.1 Implement seller application and verification
    - POST /api/v1/sellers/apply endpoint
    - Validate shop name length (3-120 characters)
    - Create seller record with pending status
    - _Requirements: 3.1, 3.6_
  
  - [x] 4.2 Implement seller approval workflow
    - Admin endpoints for seller approval/rejection
    - Update seller status and verified flag
    - Send notification to user
    - _Requirements: 3.2, 3.3, 3.4_
  
  - [x] 4.3 Implement seller profile and dashboard
    - GET /api/v1/sellers/me endpoint
    - PATCH /api/v1/sellers/me endpoint
    - GET /api/v1/sellers/me/dashboard with stats (today, week, month, all time)
    - Calculate performance metrics (rating, response time, completion rate)
    - _Requirements: 12.1, 12.2, 12.5, 12.6, 12.7_

- [ ] 5. Catalog and search system
  - [x] 5.1 Implement games and categories API
    - GET /api/v1/games with pagination and search
    - GET /api/v1/categories with hierarchical structure
    - GET /api/v1/products with filters
    - Cache catalog data in Redis with 5-minute TTL
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.8, 28.1, 28.2_
  
  - [x] 5.2 Implement lot search with filters and sorting
    - GET /api/v1/lots with filters (game, category, price range, delivery type, seller rating)
    - Support sorting (popularity, price asc/desc, newest, rating)
    - GET /api/v1/lots/{id} for lot details
    - _Requirements: 4.5, 4.6_
  
  - [x] 5.3 Implement favorites system
    - POST /api/v1/lots/{id}/favorite endpoint
    - DELETE /api/v1/lots/{id}/favorite endpoint
    - GET /api/v1/users/me/favorites endpoint
    - _Requirements: 21.1, 21.2, 21.3_

- [ ] 6. Lot creation and management
  - [x] 6.1 Implement lot CRUD operations
    - POST /api/v1/sellers/me/lots endpoint
    - Validate title (3-255 chars), price (positive, 2 decimals)
    - Support up to 10 images per lot
    - PATCH /api/v1/sellers/me/lots/{id} endpoint
    - DELETE /api/v1/sellers/me/lots/{id} (soft delete)
    - _Requirements: 5.1, 5.2, 5.5, 5.7, 5.9, 5.10_
  
  - [x] 6.2 Implement stock management for auto-delivery
    - POST /api/v1/sellers/me/lots/{id}/stock endpoint
    - Store stock items as separate records
    - Update lot status to out_of_stock when stock reaches zero
    - _Requirements: 5.3, 5.4, 5.8_
  
  - [x] 6.3 Implement lot boosting system
    - POST /api/v1/sellers/me/lots/{id}/boost endpoint
    - Deduct boost cost from seller balance
    - Prioritize boosted lots in search results
    - Auto-expire boost after duration
    - _Requirements: 22.1, 22.2, 22.3, 22.4_

- [ ] 7. Shopping cart system
  - [x] 7.1 Implement cart management
    - POST /api/v1/cart/items endpoint with stock reservation
    - PATCH /api/v1/cart/items/{id} for quantity updates
    - DELETE /api/v1/cart/items/{id} with stock release
    - GET /api/v1/cart endpoint
    - DELETE /api/v1/cart for clearing cart
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.8_
  
  - [x] 7.2 Implement cart validation and promo codes
    - POST /api/v1/cart/validate endpoint
    - Check lot availability and price changes
    - POST /api/v1/cart/apply-promo endpoint
    - Validate promo code and calculate discount
    - Ensure discounted price never negative
    - _Requirements: 6.5, 6.6, 6.7, 15.1, 15.2, 15.5, 15.7_

- [ ] 8. Order creation and payment processing
  - [x] 8.1 Implement order creation from cart
    - POST /api/v1/orders endpoint
    - Use idempotency key to prevent duplicates
    - Create order with all cart items
    - Create separate deals for each seller
    - _Requirements: 7.1, 7.2, 7.8_
  
  - [x] 8.2 Implement payment provider integrations
    - POST /api/v1/orders/{id}/payment endpoint
    - Support Telegram Stars, ЮKassa, Tinkoff, CloudPayments, Crypto Bot
    - Create payment record and return payment URL
    - _Requirements: 7.3, 7.4, 23.1, 23.2_
  
  - [~] 8.3 Implement payment webhook handlers
    - POST /api/v1/webhooks/yukassa endpoint
    - POST /api/v1/webhooks/tinkoff endpoint
    - POST /api/v1/webhooks/cloudpayments endpoint
    - POST /api/v1/webhooks/cryptobot endpoint
    - Verify webhook signatures
    - Update payment status and process order
    - Release stock if payment fails
    - _Requirements: 7.5, 7.6, 7.7, 23.3, 23.5, 23.6, 23.7_

- [ ] 9. Deal management and escrow system
  - [~] 9.1 Implement deal creation and escrow holding
    - Create deal from paid order
    - Hold deal amount in escrow
    - For auto-delivery: mark stock as sold and provide delivery data
    - For manual delivery: update status to in_progress and notify seller
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [~] 9.2 Implement delivery confirmation and escrow release
    - POST /api/v1/deals/{id}/deliver endpoint (seller)
    - POST /api/v1/deals/{id}/confirm endpoint (buyer)
    - Auto-complete after 72 hours timeout
    - Calculate commission and seller amount
    - Create transaction records for seller payment and commission
    - _Requirements: 8.4, 8.5, 8.6, 8.7, 8.8, 8.9_
  
  - [~] 9.3 Implement dispute system
    - POST /api/v1/deals/{id}/dispute endpoint
    - Update deal status to dispute
    - Prevent auto-completion
    - Notify admin
    - Admin resolution endpoints (release to seller, refund to buyer, partial)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [ ] 10. Real-time chat system via WebSocket
  - [~] 10.1 Implement chat WebSocket endpoint
    - Create /ws/chat/{deal_id} WebSocket endpoint
    - Authenticate using access token
    - Store messages in database
    - Broadcast messages to other party
    - _Requirements: 9.1, 9.2_
  
  - [~] 10.2 Implement typing indicators and read receipts
    - Handle typing indicator messages
    - Handle read receipt messages
    - Update message read status
    - _Requirements: 9.3, 9.4, 9.5, 9.6_
  
  - [~] 10.3 Implement WebSocket reconnection and message queuing
    - Handle connection loss with exponential backoff
    - Queue messages during disconnection
    - Send queued messages on reconnection
    - _Requirements: 9.7, 9.8_

- [ ] 11. Review and rating system
  - [~] 11.1 Implement product review creation
    - POST /api/v1/orders/{id}/review endpoint
    - Validate rating (1-5) and text (max 2000 chars)
    - Support up to 5 photos
    - Set status to pending for moderation
    - _Requirements: 11.1, 11.3, 11.4, 11.10_
  
  - [~] 11.2 Implement seller review creation
    - POST /api/v1/deals/{id}/review endpoint
    - Validate rating (1-5) and text
    - Set status to pending
    - _Requirements: 11.2, 11.4_
  
  - [~] 11.3 Implement review moderation and replies
    - Admin approval/rejection endpoints
    - POST /api/v1/reviews/{id}/reply endpoint
    - Calculate average rating as mean of published reviews
    - GET /api/v1/products/{id}/reviews with pagination
    - GET /api/v1/sellers/{id}/reviews with pagination
    - _Requirements: 11.5, 11.6, 11.7, 11.8, 11.9_

- [ ] 12. Balance and withdrawal management
  - [~] 12.1 Implement withdrawal system
    - POST /api/v1/sellers/me/withdrawals endpoint
    - Validate sufficient balance
    - Deduct amount and create pending withdrawal
    - Admin processing endpoints
    - Refund if withdrawal fails
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [~] 12.2 Implement balance display with breakdown
    - Show available balance, pending withdrawals, escrow held
    - Create transaction records for all balance changes
    - _Requirements: 13.6, 13.7_

- [ ] 13. Referral and promo code systems
  - [~] 13.1 Implement referral reward processing
    - Calculate reward on first purchase
    - Add reward to referrer balance
    - GET /api/v1/users/me/referrals endpoint for stats
    - _Requirements: 14.3, 14.4, 14.5_
  
  - [~] 13.2 Implement promo code management
    - Admin endpoints for promo code CRUD
    - Validate expiration, usage limit, eligibility
    - Calculate discount (percentage, fixed, gift product)
    - Record promo code usage
    - _Requirements: 15.2, 15.3, 15.4, 15.5, 15.6_

- [ ] 14. Notification system
  - [~] 14.1 Implement notification WebSocket
    - Create /ws/notifications WebSocket endpoint
    - Send real-time notifications via WebSocket
    - GET /api/v1/notifications endpoint with pagination
    - PATCH /api/v1/notifications/{id}/read endpoint
    - POST /api/v1/notifications/read-all endpoint
    - GET /api/v1/notifications/unread-count endpoint
    - _Requirements: 16.7, 16.8, 16.9_
  
  - [~] 14.2 Integrate bot notifications
    - Send push notifications via bot for: new order, order status change, new message, payment confirmed, new review, withdrawal processed
    - Format notifications with action buttons
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

- [ ] 15. Admin panel backend
  - [~] 15.1 Implement admin dashboard and analytics
    - GET /api/v1/admin/dashboard endpoint with stats
    - GET /api/v1/admin/revenue-analytics with date grouping
    - GET /api/v1/admin/top-sellers endpoint
    - GET /api/v1/admin/top-products endpoint
    - Cache dashboard stats in Redis with 15-minute TTL
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6_
  
  - [~] 15.2 Implement admin user management
    - GET /api/v1/admin/users with filters
    - PATCH /api/v1/admin/users/{id} for blocking and balance grants
    - GET /api/v1/admin/sellers with filters
    - PATCH /api/v1/admin/sellers/{id} for approval/suspension
    - Bulk action endpoints
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6_
  
  - [~] 15.3 Implement admin lot moderation
    - GET /api/v1/admin/lots with filters
    - PATCH /api/v1/admin/lots/{id} for approval/rejection/editing
    - DELETE /api/v1/admin/lots/{id} (soft delete)
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_
  
  - [~] 15.4 Implement admin broadcast system
    - POST /api/v1/admin/broadcasts endpoint
    - Support scheduled broadcasts
    - Track delivery status
    - GET /api/v1/admin/broadcasts for history
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_
  
  - [~] 15.5 Implement audit logging
    - Log all admin actions with admin ID, action type, entity type, entity ID, description, metadata
    - Log balance changes with transaction records
    - Log deal status transitions
    - GET /api/v1/admin/audit-logs with filters
    - _Requirements: 17.7, 30.1, 30.2, 30.3, 30.4, 30.5_

- [ ] 16. Frontend Mini App - Core setup
  - [~] 16.1 Initialize React/Vue project with TypeScript
    - Set up Vite project
    - Install dependencies: @twa-dev/sdk, axios, zustand/pinia, react-router-dom/vue-router
    - Configure Tailwind CSS
    - Set up i18n for Russian and English
    - _Requirements: 27.1, 27.2, 27.3_
  
  - [~] 16.2 Implement authentication flow
    - Get initData from Telegram WebApp SDK
    - Send to /api/v1/auth/telegram endpoint
    - Store access token in memory
    - Add Authorization header to all requests
    - _Requirements: 1.1, 1.2, 1.6, 1.7_
  
  - [~] 16.3 Create global state management
    - Set up auth state (user, token)
    - Set up cart state
    - Set up notification state
    - _Requirements: 2.1, 6.4_

- [ ] 17. Frontend Mini App - Catalog and product pages
  - [~] 17.1 Implement home/catalog page
    - Display product cards with image, price, rating
    - Category filters (horizontal scroll)
    - Search bar with autocomplete
    - Sort dropdown
    - Infinite scroll pagination
    - Pull-to-refresh
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 24.1, 24.2, 24.3, 24.4_
  
  - [~] 17.2 Implement product detail page
    - Image gallery with swipe (up to 10 images)
    - Product info (title, description, price)
    - Seller card (name, rating, sales count)
    - Delivery type badge
    - Stock availability
    - Add to cart button with quantity selector
    - Reviews section
    - Similar products carousel
    - _Requirements: 24.5, 24.6_
  
  - [~] 17.3 Implement search page
    - Search input with autocomplete
    - Recent searches
    - Popular searches
    - Search results with filters
    - _Requirements: 4.2, 4.5_

- [ ] 18. Frontend Mini App - Cart and checkout
  - [~] 18.1 Implement shopping cart page
    - List cart items with images
    - Quantity adjustment
    - Remove item button
    - Promo code input
    - Price breakdown (subtotal, discount, total)
    - Checkout button
    - _Requirements: 6.4, 6.7, 24.9_
  
  - [~] 18.2 Implement checkout flow
    - Order summary
    - Payment method selection
    - Terms acceptance checkbox
    - Pay button
    - Payment processing indicator
    - Success/failure screens
    - _Requirements: 7.3, 7.4, 7.6, 7.7_

- [ ] 19. Frontend Mini App - Orders and deals
  - [~] 19.1 Implement order history page
    - List orders with status badges
    - Filter by status
    - Order details view
    - Real-time status updates via WebSocket
    - Chat with seller button
    - Leave review button
    - _Requirements: 7.1, 7.2, 16.7_
  
  - [~] 19.2 Implement chat interface
    - Message list with sender avatars
    - Text input with send button
    - Image upload button
    - Typing indicator
    - Read receipts
    - Order info card at top
    - Quick actions (confirm delivery, open dispute)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 20. Frontend Mini App - Seller dashboard
  - [~] 20.1 Implement seller dashboard page
    - Sales stats cards (today, week, month, all time)
    - Revenue chart
    - Balance card with withdraw button
    - Active orders list
    - Performance metrics
    - _Requirements: 12.1, 12.2, 12.5_
  
  - [~] 20.2 Implement lot management interface
    - List seller lots with status
    - Create lot form (title, description, price, images, delivery type)
    - Edit lot form
    - Delete lot button
    - Stock management for auto-delivery
    - Boost lot button
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 22.1, 22.5_

- [ ] 21. Frontend Mini App - User profile and reviews
  - [~] 21.1 Implement user profile page
    - User avatar and name
    - Balance display with top-up button
    - Referral code with share button
    - Referral stats
    - Language selector
    - Theme toggle
    - Notification settings
    - Become seller button
    - _Requirements: 2.1, 2.2, 2.3, 14.5, 27.2_
  
  - [~] 21.2 Implement review creation interface
    - Star rating selector (1-5)
    - Text input (max 2000 chars)
    - Photo uploader (up to 5 photos)
    - Submit button
    - _Requirements: 11.1, 11.2, 11.3_
  
  - [~] 21.3 Implement reviews display
    - Paginated review list
    - Rating display
    - Review text and photos
    - Seller/admin replies
    - _Requirements: 11.7, 11.8_

- [ ] 22. Frontend Mini App - Admin panel
  - [~] 22.1 Implement admin dashboard
    - Key metrics cards
    - Revenue chart
    - User growth chart
    - Top sellers table
    - Top products table
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_
  
  - [~] 22.2 Implement admin user management
    - User table with filters
    - Block user action
    - Grant balance action
    - Seller approval/suspension
    - Bulk actions
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6_
  
  - [~] 22.3 Implement admin lot moderation
    - Lot table with filters
    - Approve/reject actions
    - Edit lot details
    - Delete lot action
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_
  
  - [~] 22.4 Implement admin dispute resolution
    - Dispute list
    - Dispute details with chat history
    - Resolution actions (release to seller, refund to buyer, partial)
    - _Requirements: 10.4, 10.5, 10.6, 10.7, 10.8_
  
  - [~] 22.5 Implement admin broadcast creator
    - Broadcast form (message, media, schedule)
    - Send broadcast action
    - Broadcast history with delivery stats
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

- [ ] 23. WebSocket connection management
  - [~] 23.1 Implement WebSocket client with reconnection
    - Automatic reconnection with exponential backoff
    - Heartbeat ping/pong
    - Message queuing during disconnection
    - Request missed messages on reconnect
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.6, 25.7_
  
  - [~] 23.2 Implement optimistic UI updates
    - Update UI immediately on user action
    - Rollback on error
    - _Requirements: 25.5_

- [ ] 24. Error handling and user feedback
  - [~] 24.1 Implement error handling
    - Display user-friendly error messages for 4xx errors
    - Display generic error for 5xx errors
    - Show offline indicator when network lost
    - Highlight invalid form fields
    - _Requirements: 26.1, 26.2, 26.3, 26.4_
  
  - [~] 24.2 Implement success notifications
    - Show success toast on successful actions
    - Show specific error reasons for payment failures
    - Offer retry option
    - _Requirements: 26.5, 26.6_
  
  - [~] 24.3 Implement consistent error response format
    - Return error_code, message, details in all error responses
    - _Requirements: 26.7_

- [ ] 25. Performance optimization
  - [~] 25.1 Implement caching strategy
    - Cache catalog data in Redis (5-minute TTL)
    - Cache user session data (1-hour TTL)
    - Cache dashboard stats (15-minute TTL)
    - _Requirements: 28.1, 28.2, 19.6_
  
  - [~] 25.2 Implement database optimization
    - Add indexes on frequently queried columns
    - Configure connection pooling (min 5, max 20)
    - _Requirements: 28.5, 28.6_
  
  - [~] 25.3 Implement frontend performance optimizations
    - Image lazy loading
    - Infinite scroll pagination
    - Optimistic UI updates
    - _Requirements: 28.3_

- [ ] 26. Security implementation
  - [~] 26.1 Implement security measures
    - Use parameterized queries for SQL injection prevention
    - Encrypt sensitive data at rest
    - Anonymize PII in logs
    - Apply rate limiting (10 requests/minute per user)
    - _Requirements: 29.2, 29.3, 29.4, 29.5, 29.6_
  
  - [~] 26.2 Implement webhook security
    - Verify webhook signatures for all payment providers
    - Reject webhooks with invalid signatures (403)
    - _Requirements: 23.6, 29.2_

- [ ] 27. Testing and deployment
  - [~] 27.1 Set up testing infrastructure
    - Configure pytest for backend
    - Configure Jest/Vitest for frontend
    - Set up test database
    - _Requirements: All requirements_
  
  - [~] 27.2 Deploy backend to production
    - Set up PostgreSQL database
    - Set up Redis instance
    - Configure environment variables
    - Run database migrations
    - Deploy FastAPI application
    - Deploy bot application
    - Configure SSL certificate
    - _Requirements: All requirements_
  
  - [~] 27.3 Deploy frontend to production
    - Build frontend with Vite
    - Deploy to Vercel/Netlify
    - Configure custom domain
    - Enable HTTPS
    - Set up CDN
    - Configure Telegram Mini App in BotFather
    - _Requirements: All requirements_

- [~] 28. Final checkpoint - Verify all functionality
  - Test complete user flow: registration → browse → add to cart → checkout → payment → delivery → review
  - Test seller flow: apply → create lot → receive order → deliver → receive payment → withdraw
  - Test admin flow: approve seller → moderate lot → resolve dispute → send broadcast
  - Verify WebSocket connections (chat, notifications)
  - Verify payment webhooks
  - Verify escrow system
  - Verify referral rewards
  - Verify promo codes
  - Check all error scenarios
  - Verify performance targets (< 200ms p95)
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- This is a comprehensive transformation requiring both backend API and frontend Mini App development
- The existing bot will be simplified to handle only notifications and quick access
- All main marketplace functionality moves to the Mini App interface
- Database migrations must be run before deploying new code
- Payment provider credentials must be configured in environment variables
- Telegram Mini App URL must be configured in BotFather
- Redis is required for caching, WebSocket state, and rate limiting
- All prices displayed with 2 decimal places and currency symbol
- Multi-language support (Russian and English minimum)
- Dark/light theme support in Mini App
- Real-time features via WebSocket (chat, notifications, order status)
- Escrow protection for all transactions
- Auto-delivery for digital goods
- Manual delivery with buyer confirmation
- Dispute resolution system
- Comprehensive admin panel
- Audit logging for all admin actions
- Performance targets: < 200ms API response time (p95)
- Security: HTTPS only, webhook signature verification, rate limiting
