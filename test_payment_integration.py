"""Test payment provider integration endpoint."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Order, User, Payment
from app.models.enums import OrderStatus
from api.services.payment_providers import PaymentResult


@pytest.mark.asyncio
async def test_initiate_payment_success(db_session: AsyncSession):
    """Test successful payment initiation."""
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
        status=OrderStatus.NEW,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Mock payment provider
    mock_result = PaymentResult(
        payment_url="https://payment.example.com/pay/12345",
        payment_id="ext_payment_12345",
        provider="yookassa"
    )
    
    with patch('api.routers.orders.get_payment_provider') as mock_provider:
        mock_provider_instance = AsyncMock()
        mock_provider_instance.create_payment = AsyncMock(return_value=mock_result)
        mock_provider.return_value = mock_provider_instance
        
        # Import after patching
        from api.routers.orders import initiate_payment
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'YUKASSA_SHOP_ID': 'test_shop',
            'YUKASSA_SECRET_KEY': 'test_secret'
        }):
            # Call endpoint
            result = await initiate_payment(
                order_id=order.id,
                payment_method="yookassa",
                current_user=user,
                session=db_session
            )
    
    # Verify response
    assert result["payment_url"] == "https://payment.example.com/pay/12345"
    assert result["external_payment_id"] == "ext_payment_12345"
    assert result["order_id"] == order.id
    assert result["amount"] == 100.0
    assert result["currency"] == "RUB"
    assert result["payment_method"] == "yookassa"
    assert result["status"] == "pending"
    
    # Verify order status updated
    await db_session.refresh(order)
    assert order.status == OrderStatus.WAITING_PAYMENT
    
    # Verify payment record created
    from sqlalchemy import select
    payment_result = await db_session.execute(
        select(Payment).where(Payment.order_id == order.id)
    )
    payment = payment_result.scalar_one()
    
    assert payment.payment_provider == "yookassa"
    assert payment.external_payment_id == "ext_payment_12345"
    assert payment.amount == Decimal("100.00")
    assert payment.currency == "RUB"
    assert payment.status == "pending"
    assert payment.payment_url == "https://payment.example.com/pay/12345"


@pytest.mark.asyncio
async def test_initiate_payment_wrong_status(db_session: AsyncSession):
    """Test payment initiation fails for wrong order status."""
    # Create test user
    user = User(
        telegram_id=123456789,
        username="testuser",
        balance=Decimal("0.00"),
        referral_code="TEST123"
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create order with COMPLETED status
    order = Order(
        order_number="GP-20240420-TEST1234",
        user_id=user.id,
        status=OrderStatus.COMPLETED,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    from api.routers.orders import initiate_payment
    
    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await initiate_payment(
            order_id=order.id,
            payment_method="yookassa",
            current_user=user,
            session=db_session
        )
    
    assert exc_info.value.status_code == 400
    assert "Cannot pay for order with status" in exc_info.value.detail


@pytest.mark.asyncio
async def test_initiate_payment_order_not_found(db_session: AsyncSession):
    """Test payment initiation fails for non-existent order."""
    # Create test user
    user = User(
        telegram_id=123456789,
        username="testuser",
        balance=Decimal("0.00"),
        referral_code="TEST123"
    )
    db_session.add(user)
    await db_session.flush()
    
    from api.routers.orders import initiate_payment
    
    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await initiate_payment(
            order_id=99999,
            payment_method="yookassa",
            current_user=user,
            session=db_session
        )
    
    assert exc_info.value.status_code == 404
    assert "Order not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_initiate_payment_unknown_provider(db_session: AsyncSession):
    """Test payment initiation fails for unknown payment provider."""
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
        status=OrderStatus.NEW,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    from api.routers.orders import initiate_payment
    
    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await initiate_payment(
            order_id=order.id,
            payment_method="unknown_provider",
            current_user=user,
            session=db_session
        )
    
    assert exc_info.value.status_code == 400
    assert "Unknown payment method" in exc_info.value.detail


@pytest.mark.asyncio
async def test_initiate_payment_provider_error(db_session: AsyncSession):
    """Test payment initiation handles provider errors gracefully."""
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
        status=OrderStatus.NEW,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Mock payment provider to raise error
    with patch('api.routers.orders.get_payment_provider') as mock_provider:
        mock_provider_instance = AsyncMock()
        mock_provider_instance.create_payment = AsyncMock(
            side_effect=Exception("Provider API error")
        )
        mock_provider.return_value = mock_provider_instance
        
        from api.routers.orders import initiate_payment
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'YUKASSA_SHOP_ID': 'test_shop',
            'YUKASSA_SECRET_KEY': 'test_secret'
        }):
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await initiate_payment(
                    order_id=order.id,
                    payment_method="yookassa",
                    current_user=user,
                    session=db_session
                )
    
    assert exc_info.value.status_code == 500
    assert "Payment creation failed" in exc_info.value.detail
    
    # Verify payment record created with error
    from sqlalchemy import select
    payment_result = await db_session.execute(
        select(Payment).where(Payment.order_id == order.id)
    )
    payment = payment_result.scalar_one()
    
    assert payment.status == "failed"
    assert payment.error_message == "Provider API error"


@pytest.mark.asyncio
async def test_initiate_payment_all_providers(db_session: AsyncSession):
    """Test payment initiation works for all supported providers."""
    providers = ["yookassa", "tinkoff", "cloudpayments", "cryptobot"]
    
    for provider_name in providers:
        # Create test user
        user = User(
            telegram_id=123456789 + providers.index(provider_name),
            username=f"testuser_{provider_name}",
            balance=Decimal("0.00"),
            referral_code=f"TEST{provider_name.upper()}"
        )
        db_session.add(user)
        await db_session.flush()
        
        # Create test order
        order = Order(
            order_number=f"GP-20240420-{provider_name.upper()}",
            user_id=user.id,
            status=OrderStatus.NEW,
            subtotal_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("100.00"),
            currency_code="RUB"
        )
        db_session.add(order)
        await db_session.flush()
        
        # Mock payment provider
        mock_result = PaymentResult(
            payment_url=f"https://{provider_name}.example.com/pay/12345",
            payment_id=f"{provider_name}_payment_12345",
            provider=provider_name
        )
        
        with patch('api.routers.orders.get_payment_provider') as mock_provider:
            mock_provider_instance = AsyncMock()
            mock_provider_instance.create_payment = AsyncMock(return_value=mock_result)
            mock_provider.return_value = mock_provider_instance
            
            from api.routers.orders import initiate_payment
            
            # Mock environment variables based on provider
            env_vars = {}
            if provider_name == "yookassa":
                env_vars = {
                    'YUKASSA_SHOP_ID': 'test_shop',
                    'YUKASSA_SECRET_KEY': 'test_secret'
                }
            elif provider_name == "tinkoff":
                env_vars = {
                    'TINKOFF_TERMINAL_KEY': 'test_terminal',
                    'TINKOFF_SECRET_KEY': 'test_secret'
                }
            elif provider_name == "cloudpayments":
                env_vars = {
                    'CLOUDPAYMENTS_PUBLIC_ID': 'test_public',
                    'CLOUDPAYMENTS_API_SECRET': 'test_secret'
                }
            elif provider_name == "cryptobot":
                env_vars = {
                    'CRYPTOBOT_TOKEN': 'test_token'
                }
            
            with patch.dict('os.environ', env_vars):
                # Call endpoint
                result = await initiate_payment(
                    order_id=order.id,
                    payment_method=provider_name,
                    current_user=user,
                    session=db_session
                )
        
        # Verify response
        assert result["payment_method"] == provider_name
        assert result["status"] == "pending"
        assert provider_name in result["payment_url"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
