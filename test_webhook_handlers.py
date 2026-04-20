"""Test webhook handlers for payment providers."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Order, User, Payment, OrderItem, Product, Game, Price, OrderStatusHistory
from app.models.enums import OrderStatus, FulfillmentType
from api.services.payment_providers import WebhookResult


@pytest.mark.asyncio
async def test_yookassa_webhook_success(db_session: AsyncSession):
    """Test ЮKassa webhook processes successful payment."""
    # Create test user
    user = User(
        telegram_id=123456789,
        username="testuser",
        balance=Decimal("0.00"),
        referral_code="TEST123"
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create test order
    order = Order(
        order_number="GP-20240420-TEST1234",
        user_id=user.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create payment record
    payment = Payment(
        order_id=order.id,
        payment_provider="yookassa",
        external_payment_id="test_payment_123",
        amount=Decimal("100.00"),
        currency="RUB",
        status="pending"
    )
    db_session.add(payment)
    await db_session.flush()
    
    # Mock webhook result
    mock_result = WebhookResult(
        payment_id="test_payment_123",
        order_id=order.id,
        amount=Decimal("100.00"),
        status="success",
        provider_data={"provider": "yookassa"}
    )
    
    # Mock payment provider
    with patch('api.routers.payments.get_payment_provider') as mock_provider:
        mock_provider_instance = AsyncMock()
        mock_provider_instance.verify_webhook = AsyncMock(return_value=True)
        mock_provider_instance.process_webhook = AsyncMock(return_value=mock_result)
        mock_provider.return_value = mock_provider_instance
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'YUKASSA_SHOP_ID': 'test_shop',
            'YUKASSA_SECRET_KEY': 'test_secret'
        }):
            from api.routers.payments import yookassa_webhook
            from fastapi import Request
            
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.json = AsyncMock(return_value={
                "event": "payment.succeeded",
                "object": {
                    "id": "test_payment_123",
                    "status": "succeeded",
                    "amount": {"value": "100.00"},
                    "metadata": {"order_id": order.id}
                }
            })
            
            # Call webhook
            result = await yookassa_webhook(mock_request, db_session)
    
    # Verify response
    assert result == {"status": "ok"}
    
    # Verify order status updated
    await db_session.refresh(order)
    assert order.status == OrderStatus.PAID
    
    # Verify payment status updated
    await db_session.refresh(payment)
    assert payment.status == "success"
    
    # Verify status history created
    from sqlalchemy import select
    history_result = await db_session.execute(
        select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id)
    )
    history = history_result.scalar_one()
    assert history.old_status == OrderStatus.WAITING_PAYMENT
    assert history.new_status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_tinkoff_webhook_invalid_signature(db_session: AsyncSession):
    """Test Tinkoff webhook rejects invalid signature."""
    # Mock payment provider with invalid signature
    with patch('api.routers.payments.get_payment_provider') as mock_provider:
        mock_provider_instance = AsyncMock()
        mock_provider_instance.verify_webhook = AsyncMock(return_value=False)
        mock_provider.return_value = mock_provider_instance
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'TINKOFF_TERMINAL_KEY': 'test_terminal',
            'TINKOFF_SECRET_KEY': 'test_secret'
        }):
            from api.routers.payments import tinkoff_webhook
            from fastapi import Request
            
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.json = AsyncMock(return_value={
                "PaymentId": "test_payment_123",
                "OrderId": "1",
                "Status": "CONFIRMED",
                "Token": "invalid_token"
            })
            
            # Call webhook - should raise 403
            with pytest.raises(HTTPException) as exc_info:
                await tinkoff_webhook(mock_request, db_session)
    
    assert exc_info.value.status_code == 403
    assert "Invalid signature" in exc_info.value.detail


@pytest.mark.asyncio
async def test_payment_failure_releases_stock(db_session: AsyncSession):
    """Test payment failure releases reserved stock."""
    # Create test user
    user = User(
        telegram_id=123456789,
        username="testuser",
        balance=Decimal("0.00"),
        referral_code="TEST123"
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create test game
    game = Game(
        slug="test-game",
        name="Test Game",
        description="Test game description",
        is_active=True
    )
    db_session.add(game)
    await db_session.flush()
    
    # Create test product
    product = Product(
        game_id=game.id,
        title="Test Product",
        description="Test product description",
        fulfillment_type=FulfillmentType.DIGITAL,
        is_active=True
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create price
    price = Price(
        product_id=product.id,
        base_price=Decimal("100.00"),
        currency_code="RUB",
        is_active=True
    )
    db_session.add(price)
    await db_session.flush()
    
    # Create test order
    order = Order(
        order_number="GP-20240420-TEST1234",
        user_id=user.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create order item
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        title_snapshot="Test Product",
        quantity=1,
        unit_price=Decimal("100.00"),
        total_price=Decimal("100.00"),
        fulfillment_type=FulfillmentType.DIGITAL
    )
    db_session.add(order_item)
    await db_session.flush()
    
    # Create payment record
    payment = Payment(
        order_id=order.id,
        payment_provider="yookassa",
        external_payment_id="test_payment_123",
        amount=Decimal("100.00"),
        currency="RUB",
        status="pending"
    )
    db_session.add(payment)
    await db_session.flush()
    
    # Mock webhook result with failure
    mock_result = WebhookResult(
        payment_id="test_payment_123",
        order_id=order.id,
        amount=Decimal("100.00"),
        status="failed",
        provider_data={"provider": "yookassa"}
    )
    
    # Mock payment provider
    with patch('api.routers.payments.get_payment_provider') as mock_provider:
        mock_provider_instance = AsyncMock()
        mock_provider_instance.verify_webhook = AsyncMock(return_value=True)
        mock_provider_instance.process_webhook = AsyncMock(return_value=mock_result)
        mock_provider.return_value = mock_provider_instance
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'YUKASSA_SHOP_ID': 'test_shop',
            'YUKASSA_SECRET_KEY': 'test_secret'
        }):
            from api.routers.payments import yookassa_webhook
            from fastapi import Request
            
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.json = AsyncMock(return_value={
                "event": "payment.canceled",
                "object": {
                    "id": "test_payment_123",
                    "status": "canceled",
                    "amount": {"value": "100.00"},
                    "metadata": {"order_id": order.id}
                }
            })
            
            # Call webhook
            result = await yookassa_webhook(mock_request, db_session)
    
    # Verify response
    assert result == {"status": "ok"}
    
    # Verify order status updated to CANCELLED
    await db_session.refresh(order)
    assert order.status == OrderStatus.CANCELLED
    
    # Verify payment status updated
    await db_session.refresh(payment)
    assert payment.status == "failed"
    
    # Verify status history created
    from sqlalchemy import select
    history_result = await db_session.execute(
        select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id)
    )
    history = history_result.scalar_one()
    assert history.old_status == OrderStatus.WAITING_PAYMENT
    assert history.new_status == OrderStatus.CANCELLED
    assert "Payment failed" in history.comment


@pytest.mark.asyncio
async def test_cloudpayments_webhook_success(db_session: AsyncSession):
    """Test CloudPayments webhook processes successful payment."""
    # Create test user
    user = User(
        telegram_id=123456789,
        username="testuser",
        balance=Decimal("0.00"),
        referral_code="TEST123"
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create test order
    order = Order(
        order_number="GP-20240420-TEST1234",
        user_id=user.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create payment record
    payment = Payment(
        order_id=order.id,
        payment_provider="cloudpayments",
        external_payment_id="test_payment_123",
        amount=Decimal("100.00"),
        currency="RUB",
        status="pending"
    )
    db_session.add(payment)
    await db_session.flush()
    
    # Mock webhook result
    mock_result = WebhookResult(
        payment_id="test_payment_123",
        order_id=order.id,
        amount=Decimal("100.00"),
        status="success",
        provider_data={"provider": "cloudpayments"}
    )
    
    # Mock payment provider
    with patch('api.routers.payments.get_payment_provider') as mock_provider:
        mock_provider_instance = AsyncMock()
        mock_provider_instance.verify_webhook = AsyncMock(return_value=True)
        mock_provider_instance.process_webhook = AsyncMock(return_value=mock_result)
        mock_provider.return_value = mock_provider_instance
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'CLOUDPAYMENTS_PUBLIC_ID': 'test_public',
            'CLOUDPAYMENTS_API_SECRET': 'test_secret'
        }):
            from api.routers.payments import cloudpayments_webhook
            from fastapi import Request
            
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.json = AsyncMock(return_value={
                "TransactionId": "test_payment_123",
                "InvoiceId": str(order.id),
                "Amount": "100.00",
                "Status": "Completed"
            })
            
            # Call webhook
            result = await cloudpayments_webhook(
                mock_request,
                x_content_hmac="valid_signature",
                session=db_session
            )
    
    # Verify response
    assert result == {"code": 0}
    
    # Verify order status updated
    await db_session.refresh(order)
    assert order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_cryptobot_webhook_success(db_session: AsyncSession):
    """Test Crypto Bot webhook processes successful payment."""
    # Create test user
    user = User(
        telegram_id=123456789,
        username="testuser",
        balance=Decimal("0.00"),
        referral_code="TEST123"
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create test order
    order = Order(
        order_number="GP-20240420-TEST1234",
        user_id=user.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create payment record
    payment = Payment(
        order_id=order.id,
        payment_provider="cryptobot",
        external_payment_id="test_payment_123",
        amount=Decimal("100.00"),
        currency="RUB",
        status="pending"
    )
    db_session.add(payment)
    await db_session.flush()
    
    # Mock webhook result
    mock_result = WebhookResult(
        payment_id="test_payment_123",
        order_id=order.id,
        amount=Decimal("100.00"),
        status="success",
        provider_data={"provider": "cryptobot"}
    )
    
    # Mock payment provider
    with patch('api.routers.payments.get_payment_provider') as mock_provider:
        mock_provider_instance = AsyncMock()
        mock_provider_instance.verify_webhook = AsyncMock(return_value=True)
        mock_provider_instance.process_webhook = AsyncMock(return_value=mock_result)
        mock_provider.return_value = mock_provider_instance
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'CRYPTOBOT_TOKEN': 'test_token'
        }):
            from api.routers.payments import cryptobot_webhook
            from fastapi import Request
            
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.json = AsyncMock(return_value={
                "update_type": "invoice_paid",
                "payload": {
                    "invoice_id": "test_payment_123",
                    "payload": str(order.id),
                    "amount": "100.00",
                    "status": "paid"
                }
            })
            
            # Call webhook
            result = await cryptobot_webhook(
                mock_request,
                crypto_pay_api_signature="valid_signature",
                session=db_session
            )
    
    # Verify response
    assert result == {"status": "ok"}
    
    # Verify order status updated
    await db_session.refresh(order)
    assert order.status == OrderStatus.PAID


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
