# Bot Notification Integration Guide

This document explains how to integrate Telegram bot push notifications throughout the marketplace application.

## Overview

The bot notification system sends push notifications to users via the Telegram bot for important events:
- New order (for sellers)
- Order status changes
- New messages in deal chat
- Payment confirmations
- New reviews
- Withdrawal processing

## Architecture

1. **Bot Notification Service** (`app/services/bot_notifications.py`): Core service that sends notifications via Telegram bot
2. **Notification Repository** (`app/repositories/transactions.py`): Database repository that can trigger bot notifications
3. **Helper Function** (`api/routers/notifications.py`): `send_notification_to_user()` helper for API routes

## Integration Methods

### Method 1: Using NotificationRepository (Recommended for Services)

```python
from app.repositories.transactions import NotificationRepository
from app.models.enums import NotificationType

# In your service or router
notification_repo = NotificationRepository(session)

await notification_repo.create_notification(
    user_id=seller_user_id,
    notification_type=NotificationType.NEW_ORDER,
    title="New Order Received",
    message=f"You have a new order for {product_name}",
    reference_type="order",
    reference_id=order_id,
    bot_notification_data={
        "order_id": order_id,
        "product_name": product_name,
        "price": price,
        "currency": currency,
        "buyer_username": buyer_username,
        "deal_id": deal_id  # Optional
    }
)
```

### Method 2: Using send_notification_to_user Helper (For API Routes)

```python
from api.routers.notifications import send_notification_to_user

await send_notification_to_user(
    user_id=buyer_user_id,
    notification_type="order_status",
    title="Order Status Updated",
    message=f"Your order #{order_id} status: {status}",
    reference_type="order",
    reference_id=order_id,
    db=session,
    bot_notification_data={
        "order_id": order_id,
        "status": status,
        "product_name": product_name
    }
)
```

### Method 3: Direct Bot Notification (Without Database)

```python
from app.services.bot_notifications import send_bot_notification

await send_bot_notification(
    notification_type="payment_confirmed",
    user_telegram_id=user.telegram_id,
    order_id=order_id,
    amount=amount,
    currency=currency
)
```

## Notification Types and Required Data

### 1. New Order (for sellers)

**Notification Type:** `new_order`

**Required Data:**
```python
{
    "order_id": int,
    "product_name": str,
    "price": float,
    "currency": str,
    "buyer_username": str | None,
    "deal_id": int | None  # Optional, for chat button
}
```

**Example:**
```python
await notification_repo.create_notification(
    user_id=seller.user_id,
    notification_type=NotificationType.NEW_ORDER,
    title="New Order Received",
    message=f"You have a new order for {lot.title}",
    reference_type="order",
    reference_id=order.id,
    bot_notification_data={
        "order_id": order.id,
        "product_name": lot.title,
        "price": float(order.total_amount),
        "currency": order.currency_code,
        "buyer_username": buyer.username,
        "deal_id": deal.id
    }
)
```

### 2. Order Status Change (for buyers)

**Notification Type:** `order_status`

**Required Data:**
```python
{
    "order_id": int,
    "status": str,  # paid, in_progress, waiting_confirmation, completed, canceled, dispute, refunded
    "product_name": str
}
```

**Example:**
```python
await send_notification_to_user(
    user_id=order.user_id,
    notification_type="order_status",
    title="Order Status Updated",
    message=f"Your order #{order.id} is now {status}",
    reference_type="order",
    reference_id=order.id,
    db=session,
    bot_notification_data={
        "order_id": order.id,
        "status": "completed",
        "product_name": "Fortnite V-Bucks 1000"
    }
)
```

### 3. New Message (for deal participants)

**Notification Type:** `new_message`

**Required Data:**
```python
{
    "sender_username": str | None,
    "deal_id": int,
    "message_preview": str  # First 100 chars of message
}
```

**Example:**
```python
# When a message is sent in deal chat
await send_bot_notification(
    notification_type="new_message",
    user_telegram_id=recipient.telegram_id,
    sender_username=sender.username,
    deal_id=deal.id,
    message_preview=message_text[:100]
)
```

### 4. Payment Confirmed (for buyers)

**Notification Type:** `payment_confirmed`

**Required Data:**
```python
{
    "order_id": int,
    "amount": float,
    "currency": str
}
```

**Example:**
```python
# After payment webhook confirms payment
await send_notification_to_user(
    user_id=order.user_id,
    notification_type="payment_confirmed",
    title="Payment Confirmed",
    message=f"Your payment for order #{order.id} was successful",
    reference_type="order",
    reference_id=order.id,
    db=session,
    bot_notification_data={
        "order_id": order.id,
        "amount": float(payment.amount),
        "currency": payment.currency_code
    }
)
```

### 5. New Review (for sellers)

**Notification Type:** `new_review`

**Required Data:**
```python
{
    "rating": int,  # 1-5
    "review_text": str | None,
    "reviewer_username": str | None,
    "product_name": str
}
```

**Example:**
```python
# After buyer leaves a review
await notification_repo.create_notification(
    user_id=seller.user_id,
    notification_type=NotificationType.REVIEW,
    title="New Review Received",
    message=f"You received a {rating}-star review",
    reference_type="review",
    reference_id=review.id,
    bot_notification_data={
        "rating": review.rating,
        "review_text": review.text,
        "reviewer_username": buyer.username,
        "product_name": lot.title
    }
)
```

### 6. Withdrawal Processed (for sellers)

**Notification Type:** `withdrawal_processed`

**Required Data:**
```python
{
    "withdrawal_id": int,
    "amount": float,
    "currency": str,
    "status": str  # completed, rejected, processing
}
```

**Example:**
```python
# After admin processes withdrawal
await notification_repo.create_notification(
    user_id=seller.user_id,
    notification_type=NotificationType.SYSTEM,
    title="Withdrawal Processed",
    message=f"Your withdrawal request has been {status}",
    reference_type="withdrawal",
    reference_id=withdrawal.id,
    bot_notification_data={
        "withdrawal_id": withdrawal.id,
        "amount": float(withdrawal.amount),
        "currency": withdrawal.currency_code,
        "status": "completed"
    }
)
```

## Integration Points

### 1. Order Creation (payments.py)

**Location:** `api/routers/payments.py` - After payment confirmation

```python
# After creating deal for manual delivery
await notification_repo.create_notification(
    user_id=lot.seller.user_id,
    notification_type=NotificationType.NEW_ORDER,
    title="New Order Received",
    message=f"You have a new order for {lot.title}",
    reference_type="deal",
    reference_id=deal.id,
    bot_notification_data={
        "order_id": order.id,
        "product_name": lot.title,
        "price": float(deal.amount),
        "currency": order.currency_code,
        "buyer_username": buyer.username,
        "deal_id": deal.id
    }
)
```

### 2. Order Status Changes (deals.py)

**Location:** `api/routers/deals.py` - When deal status changes

```python
# After buyer confirms delivery
await send_notification_to_user(
    user_id=order.user_id,
    notification_type="order_status",
    title="Order Completed",
    message=f"Your order #{order.id} has been completed",
    reference_type="order",
    reference_id=order.id,
    db=session,
    bot_notification_data={
        "order_id": order.id,
        "status": "completed",
        "product_name": lot.title
    }
)
```

### 3. Chat Messages (chat WebSocket)

**Location:** `api/routers/chat.py` - When message is sent

```python
# In WebSocket message handler
if message_type == "send_message":
    # ... save message to database ...
    
    # Send notification to other party if offline
    other_user_id = deal.seller_id if sender_id == deal.buyer_id else deal.buyer_id
    
    await send_bot_notification(
        notification_type="new_message",
        user_telegram_id=other_user.telegram_id,
        sender_username=sender.username,
        deal_id=deal.id,
        message_preview=message_text[:100]
    )
```

### 4. Payment Confirmation (webhooks)

**Location:** `api/routers/payments.py` - Webhook handlers

```python
# After payment is confirmed
await send_notification_to_user(
    user_id=order.user_id,
    notification_type="payment_confirmed",
    title="Payment Confirmed",
    message=f"Your payment of {amount} {currency} was successful",
    reference_type="payment",
    reference_id=payment.id,
    db=session,
    bot_notification_data={
        "order_id": order.id,
        "amount": float(amount),
        "currency": currency
    }
)
```

### 5. Review Creation (reviews.py)

**Location:** `api/routers/reviews.py` - After review is created

```python
# After buyer creates review
await notification_repo.create_notification(
    user_id=seller.user_id,
    notification_type=NotificationType.REVIEW,
    title="New Review Received",
    message=f"You received a {review.rating}-star review",
    reference_type="review",
    reference_id=review.id,
    bot_notification_data={
        "rating": review.rating,
        "review_text": review.text,
        "reviewer_username": buyer.username,
        "product_name": lot.title
    }
)
```

### 6. Withdrawal Processing (admin withdrawals)

**Location:** `api/routers/admin.py` - When admin processes withdrawal

```python
# After admin approves/rejects withdrawal
await notification_repo.create_notification(
    user_id=seller.user_id,
    notification_type=NotificationType.SYSTEM,
    title=f"Withdrawal {status.title()}",
    message=f"Your withdrawal request has been {status}",
    reference_type="withdrawal",
    reference_id=withdrawal.id,
    bot_notification_data={
        "withdrawal_id": withdrawal.id,
        "amount": float(withdrawal.amount),
        "currency": withdrawal.currency_code,
        "status": status
    }
)
```

## Configuration

### Mini App URL

Update the Mini App URL in `app/services/bot_notifications.py`:

```python
# Replace "https://your-miniapp-url.com" with your actual Mini App URL
web_app=WebAppInfo(url=f"https://your-miniapp-url.com/orders/{order_id}")
```

### Bot Token

Ensure `BOT_TOKEN` is set in your `.env` file:

```
BOT_TOKEN=your_bot_token_here
```

## Testing

### Manual Testing

1. Start the bot: `python -m app.main`
2. Start the API: `uvicorn api.main:app --reload`
3. Trigger an event (e.g., create an order)
4. Check if notification appears in Telegram

### Unit Testing

```python
import pytest
from app.services.bot_notifications import send_bot_notification

@pytest.mark.asyncio
async def test_new_order_notification(bot_instance):
    await send_bot_notification(
        notification_type="new_order",
        user_telegram_id=123456789,
        order_id=1,
        product_name="Test Product",
        price=100.0,
        currency="RUB",
        buyer_username="testuser"
    )
```

## Troubleshooting

### Notifications not sending

1. Check if bot instance is initialized: Look for "Bot notification service initialized" in logs
2. Check if user has telegram_id: Query database to verify user.telegram_id is set
3. Check bot permissions: Ensure user has started the bot (sent /start)
4. Check logs: Look for "Failed to send notification" warnings

### Bot blocked by user

If user blocks the bot, you'll see `TelegramForbiddenError` in logs. This is expected and handled gracefully.

### Wrong Mini App URL

Update the URL in `bot_notifications.py` to match your deployed Mini App URL.

## Requirements Mapping

- **Requirement 16.1**: New order notifications ✅
- **Requirement 16.2**: Order status change notifications ✅
- **Requirement 16.3**: New message notifications ✅
- **Requirement 16.4**: Payment confirmed notifications ✅
- **Requirement 16.5**: New review notifications ✅
- **Requirement 16.6**: Withdrawal processed notifications ✅

## Next Steps

1. Update Mini App URL in `bot_notifications.py`
2. Integrate notifications in all 6 event types
3. Test each notification type
4. Deploy and verify in production
