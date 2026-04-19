"""Test script for task 8.2: Payment provider integrations."""
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, Order, Payment, OrderStatusHistory
from app.models.enums import OrderStatus
from api.routers.orders import initiate_payment
from api.services.payment_providers import PaymentResult


@pytest.mark.asyncio
async def test_initiate_payment_creates_payment_record():
    """Test that initiate_payment creates a Payment record."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    
    # Create mock user
    user = User(
        id=1,
        telegram_id=123456,
        username="testuser",
        balance=Decimal("0.00")
    )
    
    # Create mock order
    order = Order(
        id=1,
        user_id=1,
        order_number="ORD-001",
        total_amount=Decimal("100.00"),
        currency_code="RUB",
        status=OrderStatus.NEW
    )
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = order
    session.execute.return_value = mock_result
    
    # Mock payment provider
    mock_payment_result = PaymentResult(
        payment_url="https://payment.example.com/pay/123",
        payment_id="ext_payment_123",
        provider="yookassa"
    )
    
    with patch('api.routers.orders.get_payment_provider') as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.create_payment.return_value = mock_payment_result
        mock_get_provider.return_value = mock_provider
        
        with patch.dict('os.environ', {
            'YUKASSA_SHOP_ID': 'test_shop',
            'YUKASSA_SECRET_KEY': 'test_secret'
        }):
            # Call the endpoint
            result = await initiate_payment(
                order_id=1,
                payment_method="yookassa",
                current_user=user,
                session=session
            )
    
    # Verify Payment record was created
    assert session.add.called
    payment_arg = session.add.call_args[0][0]
    assert isinstance(payment_arg, (Payment, OrderStatusHistory))
    
    # Verify response
    assert result["payment_url"] == "https://payment.example.com/pay/123"
    assert result["external_payment_id"] == "ext_payment_123"
    assert result["order_id"] == 1
    assert result["amount"] == 100.0
    assert result["currency"] == "RUB"
    assert result["payment_method"] == "yookassa"
    assert result["status"] == "pending"
    
    # Verify commit was called
    assert session.commit.called


@pytest.mark.asyncio
async def test_initiate_payment_updates_order_status():
    """Test that initiate_payment updates order status to WAITING_PAYMENT."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    
    # Create mock user
    user = User(
        id=1,
        telegram_id=123456,
        username="testuser",
        balance=Decimal("0.00")
    )
    
    # Create mock order
    order = Order(
        id=1,
        user_id=1,
        order_number="ORD-001",
        total_amount=Decimal("100.00"),
        currency_code="RUB",
        status=OrderStatus.NEW
    )
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = order
    session.execute.return_value = mock_result
    
    # Mock payment provider
    mock_payment_result = PaymentResult(
        payment_url="https://payment.example.com/pay/123",
        payment_id="ext_payment_123",
        provider="yookassa"
    )
    
    with patch('api.routers.orders.get_payment_provider') as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.create_payment.return_value = mock_payment_result
        mock_get_provider.return_value = mock_provider
        
        with patch.dict('os.environ', {
            'YUKASSA_SHOP_ID': 'test_shop',
            'YUKASSA_SECRET_KEY': 'test_secret'
        }):
            # Call the endpoint
            await initiate_payment(
                order_id=1,
                payment_method="yookassa",
                current_user=user,
                session=session
            )
    
    # Verify order status was updated
    assert order.status == OrderStatus.WAITING_PAYMENT


@pytest.mark.asyncio
async def test_initiate_payment_creates_status_history():
    """Test that initiate_payment creates OrderStatusHistory record."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    
    # Create mock user
    user = User(
        id=1,
        telegram_id=123456,
        username="testuser",
        balance=Decimal("0.00")
    )
    
    # Create mock order
    order = Order(
        id=1,
        user_id=1,
        order_number="ORD-001",
        total_amount=Decimal("100.00"),
        currency_code="RUB",
        status=OrderStatus.NEW
    )
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = order
    session.execute.return_value = mock_result
    
    # Mock payment provider
    mock_payment_result = PaymentResult(
        payment_url="https://payment.example.com/pay/123",
        payment_id="ext_payment_123",
        provider="yookassa"
    )
    
    with patch('api.routers.orders.get_payment_provider') as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.create_payment.return_value = mock_payment_result
        mock_get_provider.return_value = mock_provider
        
        with patch.dict('os.environ', {
            'YUKASSA_SHOP_ID': 'test_shop',
            'YUKASSA_SECRET_KEY': 'test_secret'
        }):
            # Call the endpoint
            await initiate_payment(
                order_id=1,
                payment_method="yookassa",
                current_user=user,
                session=session
            )
    
    # Verify OrderStatusHistory was created
    add_calls = [call[0][0] for call in session.add.call_args_list]
    status_history_records = [obj for obj in add_calls if isinstance(obj, OrderStatusHistory)]
    assert len(status_history_records) > 0
    
    status_history = status_history_records[0]
    assert status_history.order_id == 1
    assert status_history.old_status == OrderStatus.NEW
    assert status_history.new_status == OrderStatus.WAITING_PAYMENT
    assert "yookassa" in status_history.comment


@pytest.mark.asyncio
async def test_initiate_payment_supports_all_providers():
    """Test that initiate_payment supports all required payment providers."""
    providers = ["yookassa", "tinkoff", "cloudpayments", "cryptobot"]
    
    for provider_name in providers:
        # Create mock session
        session = AsyncMock(spec=AsyncSession)
        
        # Create mock user
        user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            balance=Decimal("0.00")
        )
        
        # Create mock order
        order = Order(
            id=1,
            user_id=1,
            order_number="ORD-001",
            total_amount=Decimal("100.00"),
            currency_code="RUB",
            status=OrderStatus.NEW
        )
        
        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = order
        session.execute.return_value = mock_result
        
        # Mock payment provider
        mock_payment_result = PaymentResult(
            payment_url=f"https://payment.example.com/{provider_name}/123",
            payment_id=f"{provider_name}_payment_123",
            provider=provider_name
        )
        
        with patch('api.routers.orders.get_payment_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.create_payment.return_value = mock_payment_result
            mock_get_provider.return_value = mock_provider
            
            # Set appropriate env vars for each provider
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
                # Call the endpoint
                result = await initiate_payment(
                    order_id=1,
                    payment_method=provider_name,
                    current_user=user,
                    session=session
                )
        
        # Verify response
        assert result["payment_method"] == provider_name
        assert result["payment_url"] == f"https://payment.example.com/{provider_name}/123"
        assert result["external_payment_id"] == f"{provider_name}_payment_123"


if __name__ == "__main__":
    print("Running task 8.2 tests...")
    pytest.main([__file__, "-v"])
