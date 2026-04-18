# Requirements Document: P2P Marketplace Transformation (Telegram Mini App)

## Introduction

This document specifies the business and functional requirements for transforming the Game Pay marketplace bot into a production-ready peer-to-peer (P2P) marketplace delivered as a Telegram Mini App. The system enables users to buy and sell game items through a modern web interface with escrow protection, supporting 700+ games, multiple payment methods, seller verification, auto-delivery, reviews, and comprehensive seller dashboards.

The architecture consists of three main components:
- **Frontend**: React/Vue Telegram Mini App providing native-like mobile experience
- **Backend**: FastAPI REST API with WebSocket support for real-time features
- **Bot**: aiogram bot for notifications and quick access

## Glossary

- **Mini_App**: Telegram Mini App web application providing the marketplace user interface
- **Backend_API**: FastAPI REST API server handling business logic and data operations
- **Bot**: aiogram-based Telegram bot for notifications and commands
- **User**: Any person using the marketplace (buyer or seller)
- **Seller**: Verified user authorized to create and manage product listings
- **Buyer**: User purchasing products from sellers
- **Lot**: Product listing created by a seller with price, stock, and delivery configuration
- **Deal**: Transaction between buyer and seller with escrow protection
- **Escrow**: System-held funds during transaction until delivery confirmation
- **Stock_Item**: Individual digital good data for auto-delivery
- **Order**: Purchase request created by buyer from cart
- **Cart**: Temporary collection of items user intends to purchase
- **Review**: Rating and feedback left by buyer for product or seller
- **Promo_Code**: Discount code applicable to purchases
- **Referral**: User invitation system with rewards
- **Dispute**: Conflict resolution process when deal issues arise
- **Admin**: System administrator with moderation and management privileges
- **Payment_Provider**: External service processing payments (ЮKassa, Tinkoff, etc.)
- **WebSocket**: Real-time bidirectional communication channel
- **initData**: Telegram authentication data passed from Mini App to backend
- **Transaction**: Record of balance change (deposit, purchase, withdrawal, etc.)
- **Withdrawal**: Seller request to transfer earned funds to external account
- **Boost**: Paid feature to promote lot in search results
- **Catalog**: Browsable collection of games, categories, and products
- **Auto_Delivery**: Automated delivery of digital goods without seller intervention
- **Manual_Delivery**: Delivery requiring seller to provide goods after purchase

## Requirements

### Requirement 1: User Authentication and Registration

**User Story:** As a user, I want to authenticate via Telegram and have my profile automatically created, so that I can access the marketplace securely without additional registration steps.

#### Acceptance Criteria

1. WHEN a user opens the Mini App, THE Mini_App SHALL retrieve Telegram initData including user ID, username, and hash
2. WHEN the Mini App sends initData to the authentication endpoint, THE Backend_API SHALL validate the hash using HMAC-SHA256 with the bot token
3. IF the initData hash is invalid, THEN THE Backend_API SHALL reject the authentication request with error code 401
4. WHEN authentication succeeds for a new user, THE Backend_API SHALL create a user record with Telegram ID, username, zero balance, and unique referral code
5. WHEN authentication succeeds for an existing user, THE Backend_API SHALL retrieve the user profile from the database
6. WHEN authentication completes, THE Backend_API SHALL return an access token and user profile to the Mini App
7. WHEN the Mini App receives the access token, THE Mini_App SHALL store it in memory for subsequent API requests
8. WHEN a user opens the Mini App with a referral code in the start parameter, THE Backend_API SHALL associate the new user with the referrer

### Requirement 2: User Profile Management

**User Story:** As a user, I want to view and update my profile information, so that I can manage my account settings and preferences.

#### Acceptance Criteria

1. WHEN a user requests their profile, THE Backend_API SHALL return user ID, Telegram ID, username, balance, referral code, language preference, and creation date
2. WHEN a user updates their language preference, THE Backend_API SHALL save the new language code and return the updated profile
3. WHEN a user requests their balance, THE Backend_API SHALL return the current balance with two decimal precision
4. WHEN a user requests transaction history, THE Backend_API SHALL return paginated list of transactions with type, amount, status, and timestamp
5. THE Backend_API SHALL ensure balance is never negative

### Requirement 3: Seller Registration and Verification

**User Story:** As a user, I want to apply to become a seller, so that I can list and sell products on the marketplace.

#### Acceptance Criteria

1. WHEN a user submits a seller application with shop name and description, THE Backend_API SHALL create a seller record with pending status
2. WHEN an admin reviews a seller application, THE Backend_API SHALL allow approval or rejection with reason
3. WHEN a seller application is approved, THE Backend_API SHALL update seller status to active and set verified flag to true
4. WHEN a seller application is rejected, THE Backend_API SHALL update seller status to rejected and notify the user
5. WHEN a seller is suspended by admin, THE Backend_API SHALL prevent new lot creation while allowing existing deals to complete
6. THE Backend_API SHALL validate shop name is between 3 and 120 characters

### Requirement 4: Catalog Browsing and Search

**User Story:** As a user, I want to browse games, categories, and products with filtering and sorting options, so that I can find items I want to purchase.

#### Acceptance Criteria

1. WHEN a user requests the games list, THE Backend_API SHALL return games with pagination supporting up to 50 items per page
2. WHEN a user searches for games by query text, THE Backend_API SHALL return matching games using case-insensitive search
3. WHEN a user requests categories, THE Backend_API SHALL return hierarchical category structure for the specified game
4. WHEN a user requests products for a category, THE Backend_API SHALL return products with name, description, and image
5. WHEN a user searches lots with filters, THE Backend_API SHALL support filtering by game, category, price range, delivery type, and seller rating
6. WHEN a user searches lots with sorting, THE Backend_API SHALL support sorting by popularity, price ascending, price descending, newest, and rating
7. WHEN a user requests featured lots, THE Backend_API SHALL return boosted lots ordered by boost priority
8. THE Backend_API SHALL cache catalog data in Redis with 5-minute TTL for performance

### Requirement 5: Lot Creation and Management

**User Story:** As a seller, I want to create and manage product listings with images, pricing, and stock, so that I can sell items to buyers.

#### Acceptance Criteria

1. WHEN a seller creates a lot, THE Backend_API SHALL require product ID, title, description, price, currency, delivery type, and at least one image
2. WHEN a seller uploads lot images, THE Backend_API SHALL accept up to 10 images per lot
3. WHEN a seller sets delivery type to auto, THE Backend_API SHALL require stock items to be added before activation
4. WHEN a seller adds stock items for auto-delivery, THE Backend_API SHALL store each item as a separate record with available status
5. WHEN a seller updates lot price or description, THE Backend_API SHALL save changes and update the modification timestamp
6. WHEN a seller pauses a lot, THE Backend_API SHALL update status to paused and hide it from search results
7. WHEN a seller deletes a lot, THE Backend_API SHALL set is_deleted flag to true and prevent new purchases while preserving existing deals
8. WHEN stock count reaches zero, THE Backend_API SHALL automatically update lot status to out_of_stock
9. THE Backend_API SHALL validate lot title is between 3 and 255 characters
10. THE Backend_API SHALL validate lot price is positive with maximum 2 decimal places

### Requirement 6: Shopping Cart Management

**User Story:** As a buyer, I want to add items to a shopping cart and checkout multiple items together, so that I can purchase several products in one transaction.

#### Acceptance Criteria

1. WHEN a buyer adds a lot to cart with quantity, THE Backend_API SHALL create a cart item and reserve the specified stock quantity
2. WHEN a buyer updates cart item quantity, THE Backend_API SHALL adjust stock reservation accordingly
3. WHEN a buyer removes a cart item, THE Backend_API SHALL release the reserved stock
4. WHEN a buyer requests cart contents, THE Backend_API SHALL return all cart items with lot details, quantities, and subtotal
5. WHEN a buyer validates cart before checkout, THE Backend_API SHALL verify all lots are still available and prices unchanged
6. IF any cart item is no longer available during validation, THEN THE Backend_API SHALL return validation error with unavailable items
7. WHEN a buyer applies a promo code to cart, THE Backend_API SHALL validate the code and calculate discount
8. WHEN a buyer clears cart, THE Backend_API SHALL remove all cart items and release all reserved stock

### Requirement 7: Order Creation and Payment

**User Story:** As a buyer, I want to create an order from my cart and pay using my preferred payment method, so that I can complete my purchase.

#### Acceptance Criteria

1. WHEN a buyer creates an order from cart, THE Backend_API SHALL create order record with all cart items and calculate total amount
2. WHEN an order is created, THE Backend_API SHALL create separate deals for each seller involved
3. WHEN a buyer initiates payment for an order, THE Backend_API SHALL support payment methods including Telegram Stars, ЮKassa, Tinkoff, CloudPayments, and Crypto Bot
4. WHEN a buyer selects a payment method, THE Backend_API SHALL create payment record and return payment URL or invoice
5. WHEN a payment provider sends webhook notification, THE Backend_API SHALL verify webhook signature and update payment status
6. WHEN payment is confirmed, THE Backend_API SHALL update order status to paid and transfer funds to escrow
7. IF payment fails, THEN THE Backend_API SHALL update payment status to failed and release reserved stock
8. THE Backend_API SHALL use idempotency keys to prevent duplicate order creation

### Requirement 8: Deal Management and Escrow

**User Story:** As a buyer and seller, I want deals to be protected by escrow, so that funds are held safely until delivery is confirmed.

#### Acceptance Criteria

1. WHEN a deal is created from a paid order, THE Backend_API SHALL hold the deal amount in escrow
2. WHEN a deal is created for auto-delivery lot, THE Backend_API SHALL immediately mark stock items as sold and provide delivery data to buyer
3. WHEN a deal is created for manual delivery lot, THE Backend_API SHALL update deal status to in_progress and notify seller
4. WHEN a seller delivers goods for manual delivery, THE Backend_API SHALL update deal status to waiting_confirmation
5. WHEN a buyer confirms delivery, THE Backend_API SHALL release escrow funds to seller balance minus commission
6. WHEN a deal reaches auto-completion timeout without buyer confirmation, THE Backend_API SHALL automatically release escrow and complete the deal
7. WHEN escrow is released, THE Backend_API SHALL calculate commission amount and seller amount according to seller commission percentage
8. WHEN escrow is released, THE Backend_API SHALL create transaction records for seller payment and commission deduction
9. THE Backend_API SHALL set auto-completion timeout to 72 hours after delivery

### Requirement 9: Real-Time Chat Communication

**User Story:** As a buyer and seller, I want to communicate in real-time about deal details, so that I can coordinate delivery and resolve questions.

#### Acceptance Criteria

1. WHEN a buyer or seller connects to chat WebSocket for a deal, THE Backend_API SHALL authenticate using access token
2. WHEN a user sends a chat message, THE Backend_API SHALL store the message in database and broadcast to other party via WebSocket
3. WHEN a user is typing, THE Mini_App SHALL send typing indicator via WebSocket
4. WHEN a typing indicator is received, THE Mini_App SHALL display typing animation for the other user
5. WHEN a user reads messages, THE Mini_App SHALL send read receipt via WebSocket
6. WHEN a read receipt is received, THE Mini_App SHALL update message read status
7. WHEN WebSocket connection is lost, THE Mini_App SHALL attempt reconnection with exponential backoff
8. WHEN a user sends a message while disconnected, THE Mini_App SHALL queue the message and send when reconnected

### Requirement 10: Dispute Resolution

**User Story:** As a buyer or seller, I want to open a dispute if there are issues with a deal, so that an admin can help resolve the problem.

#### Acceptance Criteria

1. WHEN a buyer or seller opens a dispute for a deal, THE Backend_API SHALL create dispute record with initiator, reason, and timestamp
2. WHEN a dispute is opened, THE Backend_API SHALL update deal status to dispute and prevent automatic completion
3. WHEN a dispute is opened, THE Backend_API SHALL notify admin via notification system
4. WHEN an admin reviews a dispute, THE Backend_API SHALL provide access to deal details, chat history, and user information
5. WHEN an admin resolves a dispute, THE Backend_API SHALL allow choosing resolution: release to seller, refund to buyer, or partial refund
6. WHEN a dispute is resolved with seller payment, THE Backend_API SHALL release escrow to seller balance
7. WHEN a dispute is resolved with buyer refund, THE Backend_API SHALL refund escrow to buyer balance
8. WHEN a dispute is resolved, THE Backend_API SHALL update dispute status to resolved and record admin decision

### Requirement 11: Product and Seller Reviews

**User Story:** As a buyer, I want to leave reviews and ratings for products and sellers, so that I can share my experience with other users.

#### Acceptance Criteria

1. WHEN a buyer completes an order, THE Backend_API SHALL allow creating a product review with rating 1-5 and optional text
2. WHEN a buyer completes a deal, THE Backend_API SHALL allow creating a seller review with rating 1-5 and optional text
3. WHEN a buyer creates a review, THE Backend_API SHALL allow uploading up to 5 photos
4. WHEN a review is created, THE Backend_API SHALL set status to pending for admin moderation
5. WHEN an admin approves a review, THE Backend_API SHALL update status to published and make it visible
6. WHEN a seller or admin replies to a review, THE Backend_API SHALL store the reply and display it with the review
7. WHEN reviews are requested for a product, THE Backend_API SHALL return paginated reviews with ratings, text, photos, and replies
8. WHEN reviews are requested for a seller, THE Backend_API SHALL return paginated seller reviews with ratings and text
9. THE Backend_API SHALL calculate average rating as mean of all published reviews rounded to 2 decimal places
10. THE Backend_API SHALL validate review text is maximum 2000 characters

### Requirement 12: Seller Dashboard and Analytics

**User Story:** As a seller, I want to view sales statistics and manage my business, so that I can track performance and optimize my listings.

#### Acceptance Criteria

1. WHEN a seller requests dashboard stats, THE Backend_API SHALL return total sales count, revenue, and active deals for today, week, month, and all time
2. WHEN a seller requests revenue chart data, THE Backend_API SHALL return daily revenue grouped by date for the specified period
3. WHEN a seller requests their lots list, THE Backend_API SHALL return all lots with status, stock count, and sales count
4. WHEN a seller requests active orders, THE Backend_API SHALL return deals in progress with buyer information and status
5. WHEN a seller views performance metrics, THE Backend_API SHALL return average rating, total reviews, response time, and completion rate
6. THE Backend_API SHALL calculate response time as average time between buyer message and seller first reply
7. THE Backend_API SHALL calculate completion rate as percentage of deals completed without disputes

### Requirement 13: Balance and Withdrawal Management

**User Story:** As a seller, I want to withdraw my earned funds to an external account, so that I can receive payment for my sales.

#### Acceptance Criteria

1. WHEN a seller requests withdrawal, THE Backend_API SHALL require withdrawal amount and payment details
2. WHEN a withdrawal is requested, THE Backend_API SHALL validate seller balance is sufficient
3. WHEN a withdrawal is created, THE Backend_API SHALL deduct amount from seller balance and create pending withdrawal record
4. WHEN an admin processes a withdrawal, THE Backend_API SHALL update withdrawal status to completed or failed
5. IF a withdrawal fails, THEN THE Backend_API SHALL refund the amount to seller balance
6. WHEN a seller views balance, THE Backend_API SHALL display available balance, pending withdrawals, and escrow held
7. THE Backend_API SHALL create transaction record for each withdrawal with type, amount, and status

### Requirement 14: Referral System

**User Story:** As a user, I want to invite friends using my referral code and earn rewards, so that I can benefit from growing the marketplace community.

#### Acceptance Criteria

1. WHEN a user registers, THE Backend_API SHALL generate a unique 8-12 character alphanumeric referral code
2. WHEN a new user registers with a referral code, THE Backend_API SHALL associate them with the referrer
3. WHEN a referred user completes their first purchase, THE Backend_API SHALL calculate referral reward as configured percentage of order amount
4. WHEN referral reward is calculated, THE Backend_API SHALL add the reward amount to referrer balance
5. WHEN a user requests referral stats, THE Backend_API SHALL return count of invited users and total rewards earned
6. THE Backend_API SHALL ensure referral code is unique across all users

### Requirement 15: Promo Code System

**User Story:** As a buyer, I want to apply promo codes to get discounts on purchases, so that I can save money.

#### Acceptance Criteria

1. WHEN a buyer applies a promo code to cart, THE Backend_API SHALL validate the code exists and is active
2. WHEN a promo code is validated, THE Backend_API SHALL check expiration date, usage limit, and user eligibility
3. IF a promo code is expired, THEN THE Backend_API SHALL return error indicating code is no longer valid
4. IF a promo code usage limit is reached, THEN THE Backend_API SHALL return error indicating code is fully used
5. WHEN a valid promo code is applied, THE Backend_API SHALL calculate discount based on promo type (percentage, fixed amount, or gift product)
6. WHEN an order is created with promo code, THE Backend_API SHALL record promo code usage and increment usage count
7. THE Backend_API SHALL ensure discounted price never becomes negative

### Requirement 16: Notification System

**User Story:** As a user, I want to receive notifications about important events, so that I stay informed about my orders and deals.

#### Acceptance Criteria

1. WHEN a seller receives a new order, THE Bot SHALL send push notification with order details and action buttons
2. WHEN an order status changes, THE Bot SHALL send notification to buyer with updated status
3. WHEN a buyer sends a message in deal chat, THE Bot SHALL send notification to seller if they are offline
4. WHEN a payment is confirmed, THE Bot SHALL send notification to buyer confirming successful payment
5. WHEN a seller receives a review, THE Bot SHALL send notification with review rating and text
6. WHEN a withdrawal is processed, THE Bot SHALL send notification to seller with withdrawal status
7. WHEN a user connects to notifications WebSocket, THE Backend_API SHALL send real-time notifications via WebSocket
8. WHEN a user requests notification history, THE Backend_API SHALL return paginated list of notifications with read status
9. WHEN a user marks notification as read, THE Backend_API SHALL update read status and timestamp

### Requirement 17: Admin User Management

**User Story:** As an admin, I want to manage users and sellers, so that I can maintain marketplace quality and handle policy violations.

#### Acceptance Criteria

1. WHEN an admin requests users list, THE Backend_API SHALL return paginated users with filters for status, registration date, and balance
2. WHEN an admin blocks a user, THE Backend_API SHALL prevent the user from creating orders and accessing marketplace features
3. WHEN an admin grants balance to a user, THE Backend_API SHALL add the specified amount and create transaction record with reason
4. WHEN an admin requests sellers list, THE Backend_API SHALL return sellers with status, rating, sales count, and verification status
5. WHEN an admin suspends a seller, THE Backend_API SHALL prevent new lot creation and hide existing lots from search
6. WHEN an admin performs bulk actions, THE Backend_API SHALL apply the action to all specified user IDs and log each action
7. THE Backend_API SHALL log all admin actions in audit log with admin ID, action type, entity type, entity ID, and timestamp

### Requirement 18: Admin Lot Moderation

**User Story:** As an admin, I want to moderate lot listings, so that I can ensure content quality and policy compliance.

#### Acceptance Criteria

1. WHEN an admin requests lots list, THE Backend_API SHALL return all lots with filters for status, seller, and creation date
2. WHEN an admin views lot details, THE Backend_API SHALL display all lot information including images, description, and seller details
3. WHEN an admin approves a lot, THE Backend_API SHALL update lot status to active and make it visible in search
4. WHEN an admin rejects a lot, THE Backend_API SHALL update lot status to rejected and notify seller with reason
5. WHEN an admin edits lot details, THE Backend_API SHALL save changes and log the modification in audit log
6. WHEN an admin deletes a lot, THE Backend_API SHALL set is_deleted flag and hide from search while preserving deal history

### Requirement 19: Admin Analytics Dashboard

**User Story:** As an admin, I want to view marketplace analytics and metrics, so that I can monitor business performance and make informed decisions.

#### Acceptance Criteria

1. WHEN an admin requests dashboard stats, THE Backend_API SHALL return total users, active sellers, total orders, and revenue for specified date range
2. WHEN an admin requests revenue analytics, THE Backend_API SHALL return revenue grouped by day, week, or month
3. WHEN an admin requests top sellers, THE Backend_API SHALL return sellers ranked by sales count or revenue for specified period
4. WHEN an admin requests top products, THE Backend_API SHALL return products ranked by sales count for specified period
5. WHEN an admin requests user growth chart, THE Backend_API SHALL return new user registrations grouped by date
6. THE Backend_API SHALL cache dashboard statistics in Redis with 15-minute TTL

### Requirement 20: Admin Broadcast System

**User Story:** As an admin, I want to send broadcast messages to all users, so that I can communicate important announcements.

#### Acceptance Criteria

1. WHEN an admin creates a broadcast message, THE Backend_API SHALL require message text and optional media attachment
2. WHEN an admin schedules a broadcast, THE Backend_API SHALL allow setting future send time
3. WHEN a broadcast is sent, THE Bot SHALL deliver the message to all active users
4. WHEN a broadcast is sent, THE Backend_API SHALL track delivery status for each user
5. WHEN an admin views broadcast history, THE Backend_API SHALL return list of broadcasts with send time, recipient count, and delivery statistics

### Requirement 21: Favorites Management

**User Story:** As a buyer, I want to save lots to favorites, so that I can easily find and purchase them later.

#### Acceptance Criteria

1. WHEN a buyer adds a lot to favorites, THE Backend_API SHALL create favorite record with user ID and lot ID
2. WHEN a buyer removes a lot from favorites, THE Backend_API SHALL delete the favorite record
3. WHEN a buyer requests favorites list, THE Backend_API SHALL return all favorited lots with current price and availability
4. WHEN a favorited lot price changes, THE Mini_App SHALL display price change indicator
5. WHEN a favorited lot becomes unavailable, THE Mini_App SHALL display unavailable status

### Requirement 22: Lot Boosting System

**User Story:** As a seller, I want to boost my lots to appear higher in search results, so that I can increase visibility and sales.

#### Acceptance Criteria

1. WHEN a seller requests to boost a lot, THE Backend_API SHALL require boost duration in hours
2. WHEN a boost is purchased, THE Backend_API SHALL deduct boost cost from seller balance
3. WHEN a boost is active, THE Backend_API SHALL prioritize the lot in search results and featured sections
4. WHEN a boost expires, THE Backend_API SHALL automatically remove boost priority
5. WHEN a seller views lot details, THE Mini_App SHALL display boost status and expiration time

### Requirement 23: Payment Provider Integration

**User Story:** As a buyer, I want to pay using various payment methods, so that I can choose the most convenient option.

#### Acceptance Criteria

1. WHEN a buyer requests available payment methods, THE Backend_API SHALL return list of enabled providers with names and icons
2. WHEN a payment is created via ЮKassa, THE Backend_API SHALL generate payment URL and return it to Mini App
3. WHEN ЮKassa sends webhook notification, THE Backend_API SHALL verify signature using secret key
4. WHEN a payment is created via Crypto Bot, THE Backend_API SHALL create invoice and return payment URL
5. WHEN a payment provider webhook is received, THE Backend_API SHALL update payment status and trigger order processing
6. IF webhook signature verification fails, THEN THE Backend_API SHALL reject the webhook with 403 status
7. THE Backend_API SHALL log all payment events including creation, confirmation, and failures

### Requirement 24: Frontend Mini App Interface

**User Story:** As a user, I want a beautiful and intuitive mobile interface, so that I can easily browse and purchase products.

#### Acceptance Criteria

1. WHEN the Mini App loads, THE Mini_App SHALL display loading indicator while fetching initial data
2. WHEN the home page loads, THE Mini_App SHALL display featured products, categories, and search bar
3. WHEN a user scrolls to bottom of product list, THE Mini_App SHALL load next page automatically (infinite scroll)
4. WHEN a user pulls down on a page, THE Mini_App SHALL refresh the content
5. WHEN a user clicks a product card, THE Mini_App SHALL navigate to product detail page with smooth transition
6. WHEN a user views product details, THE Mini_App SHALL display image gallery with swipe gestures supporting up to 10 images
7. WHEN a user applies filters, THE Mini_App SHALL update search results without full page reload
8. WHEN a user toggles theme, THE Mini_App SHALL switch between dark and light mode with smooth transition
9. THE Mini_App SHALL display all prices with 2 decimal places and currency symbol

### Requirement 25: WebSocket Connection Management

**User Story:** As a user, I want real-time updates for chat and notifications, so that I receive information instantly without refreshing.

#### Acceptance Criteria

1. WHEN the Mini App establishes WebSocket connection, THE Mini_App SHALL include access token in connection URL
2. WHEN WebSocket connection is established, THE Backend_API SHALL authenticate the token and accept or reject connection
3. WHEN WebSocket connection is lost, THE Mini_App SHALL attempt reconnection with exponential backoff starting at 1 second
4. WHEN WebSocket reconnects, THE Mini_App SHALL request missed messages since last connection
5. WHEN WebSocket receives a message, THE Mini_App SHALL update UI immediately with optimistic rendering
6. THE Backend_API SHALL send heartbeat ping every 30 seconds to keep connection alive
7. WHEN the Mini App receives ping, THE Mini_App SHALL respond with pong message

### Requirement 26: Error Handling and User Feedback

**User Story:** As a user, I want clear error messages and feedback, so that I understand what went wrong and how to fix it.

#### Acceptance Criteria

1. WHEN an API request fails with 4xx error, THE Mini_App SHALL display user-friendly error message
2. WHEN an API request fails with 5xx error, THE Mini_App SHALL display generic error message and log details for debugging
3. WHEN network connection is lost, THE Mini_App SHALL display offline indicator
4. WHEN a form submission fails validation, THE Mini_App SHALL highlight invalid fields with error messages
5. WHEN a user action succeeds, THE Mini_App SHALL display success notification with confirmation message
6. WHEN a payment fails, THE Mini_App SHALL display specific error reason and offer retry option
7. THE Backend_API SHALL return consistent error response format with error code, message, and optional details

### Requirement 27: Multi-Language Support

**User Story:** As a user, I want to use the marketplace in my preferred language, so that I can understand all content and instructions.

#### Acceptance Criteria

1. WHEN the Mini App loads, THE Mini_App SHALL detect user language from Telegram settings
2. WHEN a user changes language preference, THE Mini_App SHALL update all UI text immediately
3. WHEN the Mini App displays content, THE Mini_App SHALL use translations for all static text
4. WHEN the Backend API returns error messages, THE Backend_API SHALL provide error codes that Mini App can translate
5. THE Mini_App SHALL support at minimum Russian and English languages

### Requirement 28: Performance and Caching

**User Story:** As a user, I want fast page loads and smooth interactions, so that I have a pleasant shopping experience.

#### Acceptance Criteria

1. WHEN the Mini App requests catalog data, THE Backend_API SHALL return cached results from Redis if available
2. WHEN catalog cache expires, THE Backend_API SHALL refresh cache from database with 5-minute TTL
3. WHEN the Mini App loads images, THE Mini_App SHALL use lazy loading to defer off-screen images
4. WHEN the Backend API processes requests, THE Backend_API SHALL respond within 200ms for 95th percentile
5. WHEN the Backend API queries database, THE Backend_API SHALL use connection pooling with minimum 5 and maximum 20 connections
6. THE Backend_API SHALL use database indexes on frequently queried columns including user_id, seller_id, status, and created_at

### Requirement 29: Security and Data Protection

**User Story:** As a user, I want my data and transactions to be secure, so that I can trust the marketplace with my information and money.

#### Acceptance Criteria

1. WHEN the Mini App sends initData, THE Backend_API SHALL validate hash using HMAC-SHA256 with bot token as secret
2. WHEN the Backend API receives payment webhook, THE Backend_API SHALL verify signature using provider secret key
3. WHEN the Backend API stores sensitive data, THE Backend_API SHALL encrypt payment details at rest
4. WHEN the Backend API logs events, THE Backend_API SHALL anonymize personally identifiable information
5. WHEN the Backend API detects suspicious activity, THE Backend_API SHALL apply rate limiting of 10 requests per minute per user
6. THE Backend_API SHALL use parameterized queries to prevent SQL injection
7. THE Mini_App SHALL communicate with Backend API only via HTTPS

### Requirement 30: Audit Logging

**User Story:** As an admin, I want all important actions to be logged, so that I can track changes and investigate issues.

#### Acceptance Criteria

1. WHEN an admin performs any action, THE Backend_API SHALL create audit log entry with admin ID, action type, entity type, entity ID, description, and metadata
2. WHEN a user balance changes, THE Backend_API SHALL create transaction record with type, amount, balance before, balance after, and reference
3. WHEN a deal status changes, THE Backend_API SHALL log the status transition with timestamp and triggering user
4. WHEN an admin requests audit logs, THE Backend_API SHALL return paginated logs with filters for date range, admin, action type, and entity type
5. THE Backend_API SHALL retain audit logs for minimum 1 year

