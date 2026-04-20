"""Test bot notification service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from app.services.bot_notifications import (
    BotNotificationService,
    set_bot_instance,
    get_bot_notification_service,
    send_bot_notification
)


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def notification_service(mock_bot):
    """Create a notification service with mock bot."""
    return BotNotificationService(mock_bot)


@pytest.mark.asyncio
async def test_send_new_order_notification(notification_service, mock_bot):
    """Test sending new order notification."""
    await notification_service.send_new_order_notification(
        seller_telegram_id=123456789,
        order_id=1,
        product_name="Fortnite V-Bucks 1000",
        price=500.0,
        currency="RUB",
        buyer_username="testbuyer",
        deal_id=1
    )
    
    # Verify bot.send_message was called
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    
    # Check arguments
    assert call_args.kwargs["chat_id"] == 123456789
    assert "New Order #1" in call_args.kwargs["text"]
    assert "Fortnite V-Bucks 1000" in call_args.kwargs["text"]
    assert "500.00 RUB" in call_args.kwargs["text"]
    assert "@testbuyer" in call_args.kwargs["text"]
    
    # Check keyboard has buttons
    keyboard = call_args.kwargs["reply_markup"]
    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 2  # Open Order + Chat buttons


@pytest.mark.asyncio
async def test_send_order_status_notification(notification_service, mock_bot):
    """Test sending order status notification."""
    await notification_service.send_order_status_notification(
        buyer_telegram_id=987654321,
        order_id=2,
        status="completed",
        product_name="Test Product"
    )
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    
    assert call_args.kwargs["chat_id"] == 987654321
    assert "Order #2" in call_args.kwargs["text"]
    assert "Completed" in call_args.kwargs["text"]
    assert "Test Product" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_send_new_message_notification(notification_service, mock_bot):
    """Test sending new message notification."""
    await notification_service.send_new_message_notification(
        recipient_telegram_id=111222333,
        sender_username="sender123",
        deal_id=5,
        message_preview="Hello, when will you deliver?"
    )
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    
    assert call_args.kwargs["chat_id"] == 111222333
    assert "@sender123" in call_args.kwargs["text"]
    assert "Hello, when will you deliver?" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_send_payment_confirmed_notification(notification_service, mock_bot):
    """Test sending payment confirmed notification."""
    await notification_service.send_payment_confirmed_notification(
        buyer_telegram_id=444555666,
        order_id=10,
        amount=1500.50,
        currency="RUB"
    )
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    
    assert call_args.kwargs["chat_id"] == 444555666
    assert "Payment Confirmed" in call_args.kwargs["text"]
    assert "Order #10" in call_args.kwargs["text"]
    assert "1500.50 RUB" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_send_new_review_notification(notification_service, mock_bot):
    """Test sending new review notification."""
    await notification_service.send_new_review_notification(
        seller_telegram_id=777888999,
        rating=5,
        review_text="Great seller, fast delivery!",
        reviewer_username="happybuyer",
        product_name="Game Currency"
    )
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    
    assert call_args.kwargs["chat_id"] == 777888999
    assert "New Review" in call_args.kwargs["text"]
    assert "⭐⭐⭐⭐⭐" in call_args.kwargs["text"]  # 5 stars
    assert "(5/5)" in call_args.kwargs["text"]
    assert "Great seller" in call_args.kwargs["text"]
    assert "@happybuyer" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_send_withdrawal_processed_notification(notification_service, mock_bot):
    """Test sending withdrawal processed notification."""
    await notification_service.send_withdrawal_processed_notification(
        seller_telegram_id=123123123,
        withdrawal_id=7,
        amount=5000.0,
        currency="RUB",
        status="completed"
    )
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    
    assert call_args.kwargs["chat_id"] == 123123123
    assert "Withdrawal Completed" in call_args.kwargs["text"]
    assert "Withdrawal #7" in call_args.kwargs["text"]
    assert "5000.00 RUB" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_send_bot_notification_helper(mock_bot):
    """Test the send_bot_notification helper function."""
    set_bot_instance(mock_bot)
    
    await send_bot_notification(
        notification_type="new_order",
        user_telegram_id=999888777,
        order_id=99,
        product_name="Test Item",
        price=250.0,
        currency="RUB",
        buyer_username="buyer99"
    )
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args.kwargs["chat_id"] == 999888777


@pytest.mark.asyncio
async def test_bot_notification_with_telegram_error(notification_service, mock_bot):
    """Test that Telegram errors are handled gracefully."""
    from aiogram.exceptions import TelegramForbiddenError
    
    # Simulate bot blocked by user
    mock_bot.send_message.side_effect = TelegramForbiddenError(
        method="sendMessage",
        message="Forbidden: bot was blocked by the user"
    )
    
    # Should not raise exception
    await notification_service.send_new_order_notification(
        seller_telegram_id=123456789,
        order_id=1,
        product_name="Test",
        price=100.0,
        currency="RUB",
        buyer_username="test"
    )
    
    # Verify it tried to send
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_message_preview_truncation(notification_service, mock_bot):
    """Test that long message previews are truncated."""
    long_message = "A" * 200  # 200 characters
    
    await notification_service.send_new_message_notification(
        recipient_telegram_id=111222333,
        sender_username="sender",
        deal_id=1,
        message_preview=long_message
    )
    
    call_args = mock_bot.send_message.call_args
    message_text = call_args.kwargs["text"]
    
    # Should be truncated to 100 chars + "..."
    assert len(long_message) == 200
    assert "..." in message_text


@pytest.mark.asyncio
async def test_review_text_truncation(notification_service, mock_bot):
    """Test that long review texts are truncated."""
    long_review = "B" * 200  # 200 characters
    
    await notification_service.send_new_review_notification(
        seller_telegram_id=777888999,
        rating=4,
        review_text=long_review,
        reviewer_username="reviewer",
        product_name="Product"
    )
    
    call_args = mock_bot.send_message.call_args
    message_text = call_args.kwargs["text"]
    
    # Should be truncated to 150 chars + "..."
    assert "..." in message_text


def test_get_bot_notification_service_without_bot():
    """Test that service returns None when bot not initialized."""
    # Reset global bot instance
    import app.services.bot_notifications as bot_notif_module
    bot_notif_module._bot_instance = None
    
    service = get_bot_notification_service()
    assert service is None


def test_set_and_get_bot_instance(mock_bot):
    """Test setting and getting bot instance."""
    set_bot_instance(mock_bot)
    service = get_bot_notification_service()
    
    assert service is not None
    assert isinstance(service, BotNotificationService)
    assert service.bot == mock_bot


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
