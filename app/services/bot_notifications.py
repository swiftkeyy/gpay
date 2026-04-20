"""Bot notification service for sending push notifications via Telegram bot."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BotNotificationService:
    """Service for sending push notifications via Telegram bot."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_new_order_notification(
        self,
        seller_telegram_id: int,
        order_id: int,
        product_name: str,
        price: float,
        currency: str,
        buyer_username: str | None,
        deal_id: int | None = None
    ):
        """
        Send notification to seller about new order.
        
        Requirements: 16.1
        """
        # Format message
        buyer_display = f"@{buyer_username}" if buyer_username else "Anonymous"
        message = (
            f"🔔 <b>New Order #{order_id}</b>\n\n"
            f"Product: {product_name}\n"
            f"Price: {price:.2f} {currency}\n"
            f"Buyer: {buyer_display}"
        )
        
        # Create action buttons
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        # Add "Open Order" button
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="📦 Open Order",
                web_app=WebAppInfo(url=f"https://your-miniapp-url.com/orders/{order_id}")
            )
        ])
        
        # Add "Chat with Buyer" button if deal exists
        if deal_id:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="💬 Chat with Buyer",
                    web_app=WebAppInfo(url=f"https://your-miniapp-url.com/chat/{deal_id}")
                )
            ])
        
        try:
            await self.bot.send_message(
                chat_id=seller_telegram_id,
                text=message,
                reply_markup=keyboard
            )
            logger.info(f"New order notification sent to seller {seller_telegram_id} for order {order_id}")
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Failed to send notification to seller {seller_telegram_id}: {e}")
    
    async def send_order_status_notification(
        self,
        buyer_telegram_id: int,
        order_id: int,
        status: str,
        product_name: str
    ):
        """
        Send notification to buyer about order status change.
        
        Requirements: 16.2
        """
        # Map status to emoji and text
        status_map = {
            "paid": ("✅", "Payment Confirmed"),
            "in_progress": ("⏳", "In Progress"),
            "waiting_confirmation": ("⏰", "Awaiting Confirmation"),
            "completed": ("🎉", "Completed"),
            "canceled": ("❌", "Canceled"),
            "dispute": ("⚠️", "Dispute Opened"),
            "refunded": ("💰", "Refunded")
        }
        
        emoji, status_text = status_map.get(status, ("📦", status.replace("_", " ").title()))
        
        message = (
            f"{emoji} <b>Order Status Update</b>\n\n"
            f"Order #{order_id}\n"
            f"Product: {product_name}\n"
            f"Status: {status_text}"
        )
        
        # Create action button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="📦 View Order",
                web_app=WebAppInfo(url=f"https://your-miniapp-url.com/orders/{order_id}")
            )
        ]])
        
        try:
            await self.bot.send_message(
                chat_id=buyer_telegram_id,
                text=message,
                reply_markup=keyboard
            )
            logger.info(f"Order status notification sent to buyer {buyer_telegram_id} for order {order_id}")
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Failed to send notification to buyer {buyer_telegram_id}: {e}")
    
    async def send_new_message_notification(
        self,
        recipient_telegram_id: int,
        sender_username: str | None,
        deal_id: int,
        message_preview: str
    ):
        """
        Send notification about new message in deal chat.
        
        Requirements: 16.3
        """
        sender_display = f"@{sender_username}" if sender_username else "User"
        
        # Truncate message preview if too long
        if len(message_preview) > 100:
            message_preview = message_preview[:97] + "..."
        
        message = (
            f"💬 <b>New Message</b>\n\n"
            f"From: {sender_display}\n"
            f"Message: {message_preview}"
        )
        
        # Create action button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="💬 Open Chat",
                web_app=WebAppInfo(url=f"https://your-miniapp-url.com/chat/{deal_id}")
            )
        ]])
        
        try:
            await self.bot.send_message(
                chat_id=recipient_telegram_id,
                text=message,
                reply_markup=keyboard
            )
            logger.info(f"New message notification sent to user {recipient_telegram_id} for deal {deal_id}")
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Failed to send notification to user {recipient_telegram_id}: {e}")
    
    async def send_payment_confirmed_notification(
        self,
        buyer_telegram_id: int,
        order_id: int,
        amount: float,
        currency: str
    ):
        """
        Send notification about successful payment.
        
        Requirements: 16.4
        """
        message = (
            f"✅ <b>Payment Confirmed</b>\n\n"
            f"Order #{order_id}\n"
            f"Amount: {amount:.2f} {currency}\n\n"
            f"Your order is being processed."
        )
        
        # Create action button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="📦 View Order",
                web_app=WebAppInfo(url=f"https://your-miniapp-url.com/orders/{order_id}")
            )
        ]])
        
        try:
            await self.bot.send_message(
                chat_id=buyer_telegram_id,
                text=message,
                reply_markup=keyboard
            )
            logger.info(f"Payment confirmed notification sent to buyer {buyer_telegram_id} for order {order_id}")
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Failed to send notification to buyer {buyer_telegram_id}: {e}")
    
    async def send_new_review_notification(
        self,
        seller_telegram_id: int,
        rating: int,
        review_text: str | None,
        reviewer_username: str | None,
        product_name: str
    ):
        """
        Send notification to seller about new review.
        
        Requirements: 16.5
        """
        # Create star rating display
        stars = "⭐" * rating
        
        reviewer_display = f"@{reviewer_username}" if reviewer_username else "Anonymous"
        
        message = (
            f"⭐ <b>New Review</b>\n\n"
            f"Product: {product_name}\n"
            f"Rating: {stars} ({rating}/5)\n"
            f"From: {reviewer_display}"
        )
        
        if review_text:
            # Truncate review text if too long
            review_preview = review_text[:150] + "..." if len(review_text) > 150 else review_text
            message += f"\n\nReview: {review_preview}"
        
        # Create action button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="📝 View Reviews",
                web_app=WebAppInfo(url="https://your-miniapp-url.com/seller/reviews")
            )
        ]])
        
        try:
            await self.bot.send_message(
                chat_id=seller_telegram_id,
                text=message,
                reply_markup=keyboard
            )
            logger.info(f"New review notification sent to seller {seller_telegram_id}")
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Failed to send notification to seller {seller_telegram_id}: {e}")
    
    async def send_withdrawal_processed_notification(
        self,
        seller_telegram_id: int,
        withdrawal_id: int,
        amount: float,
        currency: str,
        status: str
    ):
        """
        Send notification about withdrawal processing.
        
        Requirements: 16.6
        """
        # Map status to emoji and text
        if status == "completed":
            emoji = "✅"
            status_text = "Completed"
            message_text = "Your withdrawal has been processed successfully."
        elif status == "rejected":
            emoji = "❌"
            status_text = "Rejected"
            message_text = "Your withdrawal request was rejected. Please contact support for details."
        else:
            emoji = "⏳"
            status_text = "Processing"
            message_text = "Your withdrawal is being processed."
        
        message = (
            f"{emoji} <b>Withdrawal {status_text}</b>\n\n"
            f"Withdrawal #{withdrawal_id}\n"
            f"Amount: {amount:.2f} {currency}\n\n"
            f"{message_text}"
        )
        
        # Create action button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="💰 View Balance",
                web_app=WebAppInfo(url="https://your-miniapp-url.com/seller/balance")
            )
        ]])
        
        try:
            await self.bot.send_message(
                chat_id=seller_telegram_id,
                text=message,
                reply_markup=keyboard
            )
            logger.info(f"Withdrawal notification sent to seller {seller_telegram_id} for withdrawal {withdrawal_id}")
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Failed to send notification to seller {seller_telegram_id}: {e}")


# Global bot instance (will be set during bot startup)
_bot_instance: Bot | None = None


def set_bot_instance(bot: Bot):
    """Set the global bot instance for notifications."""
    global _bot_instance
    _bot_instance = bot
    logger.info("Bot instance set for notifications")


def get_bot_notification_service() -> BotNotificationService | None:
    """Get the bot notification service instance."""
    if _bot_instance is None:
        logger.warning("Bot instance not set, notifications will not be sent")
        return None
    return BotNotificationService(_bot_instance)


async def send_bot_notification(
    notification_type: str,
    user_telegram_id: int,
    **kwargs
):
    """
    Helper function to send bot notifications.
    
    This can be called from other services to send push notifications.
    
    Args:
        notification_type: Type of notification (new_order, order_status, new_message, etc.)
        user_telegram_id: Telegram ID of the recipient
        **kwargs: Additional parameters specific to notification type
    """
    service = get_bot_notification_service()
    if service is None:
        logger.warning(f"Cannot send {notification_type} notification - bot service not available")
        return
    
    try:
        if notification_type == "new_order":
            await service.send_new_order_notification(
                seller_telegram_id=user_telegram_id,
                order_id=kwargs["order_id"],
                product_name=kwargs["product_name"],
                price=kwargs["price"],
                currency=kwargs["currency"],
                buyer_username=kwargs.get("buyer_username"),
                deal_id=kwargs.get("deal_id")
            )
        
        elif notification_type == "order_status":
            await service.send_order_status_notification(
                buyer_telegram_id=user_telegram_id,
                order_id=kwargs["order_id"],
                status=kwargs["status"],
                product_name=kwargs["product_name"]
            )
        
        elif notification_type == "new_message":
            await service.send_new_message_notification(
                recipient_telegram_id=user_telegram_id,
                sender_username=kwargs.get("sender_username"),
                deal_id=kwargs["deal_id"],
                message_preview=kwargs["message_preview"]
            )
        
        elif notification_type == "payment_confirmed":
            await service.send_payment_confirmed_notification(
                buyer_telegram_id=user_telegram_id,
                order_id=kwargs["order_id"],
                amount=kwargs["amount"],
                currency=kwargs["currency"]
            )
        
        elif notification_type == "new_review":
            await service.send_new_review_notification(
                seller_telegram_id=user_telegram_id,
                rating=kwargs["rating"],
                review_text=kwargs.get("review_text"),
                reviewer_username=kwargs.get("reviewer_username"),
                product_name=kwargs["product_name"]
            )
        
        elif notification_type == "withdrawal_processed":
            await service.send_withdrawal_processed_notification(
                seller_telegram_id=user_telegram_id,
                withdrawal_id=kwargs["withdrawal_id"],
                amount=kwargs["amount"],
                currency=kwargs["currency"],
                status=kwargs["status"]
            )
        
        else:
            logger.warning(f"Unknown notification type: {notification_type}")
    
    except Exception as e:
        logger.error(f"Error sending {notification_type} notification: {e}")
