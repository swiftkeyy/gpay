"""Test deal creation and escrow holding functionality.

Validates: Requirements 8.1, 8.2, 8.3
- 8.1: Deal creation with escrow holding
- 8.2: Auto-delivery with stock item assignment
- 8.3: Manual delivery with seller notification
"""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import (
    Order, OrderItem, User, Seller, Lot, LotStockItem, 
    Deal, DealMessage, Payment, Product, Game, Category
)
from app.models.enums import (
    OrderStatus, DealStatus, LotDeliveryType, SellerStatus,
    LotStatus, NotificationType
)
from api.routers.payments import _process_payment_result
from api.services.payment_providers import WebhookResult


@pytest.mark.asyncio
async def test_deal_creation_with_escrow(db_session: AsyncSession):
    """Test that deal is created with escrow when payment is confirmed.
    
    Validates: Requirement 8.1
    """
    # Create test data
    user = User(
        telegram_id=123456789,
        username="buyer",
        balance=Decimal("0.00"),
        referral_code="BUYER123"
    )
    db_session.add(user)
    
    seller_user = User(
        telegram_id=987654321,
        username="seller",
        balance=Decimal("0.00"),
        referral_code="SELLER123"
    )
    db_session.add(seller_user)
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        status=SellerStatus.ACTIVE,
        shop_name="Test Shop",
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    # Create game, category, product
    game = Game(slug="test-game", title="Test Game")
    db_session.add(game)
    await db_session.flush()
    
    category = Category(game_id=game.id, slug="test-cat", title="Test Category")
    db_session.add(category)
    await db_session.flush()
    
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product",
        title="Test Product"
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create lot
    lot = Lot(
        seller_id=seller.id,
        product_id=product.id,
        title="Test Lot",
        price=Decimal("100.00"),
        delivery_type=LotDeliveryType.MANUAL,
        status=LotStatus.ACTIVE
    )
    db_session.add(lot)
    await db_session.flush()
    
    # Create order
    order = Order(
        order_number="GP-TEST-001",
        user_id=user.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("100.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create order item with lot_id in metadata
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        title_snapshot="Test Product",
        quantity=1,
        unit_price=Decimal("100.00"),
        total_price=Decimal("100.00"),
        fulfillment_type="manual",
        metadata_json={"lot_id": lot.id}
    )
    db_session.add(order_item)
    await db_session.flush()
    
    # Create payment
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
    
    # Process payment success
    webhook_result = WebhookResult(
        payment_id="test_payment_123",
        order_id=order.id,
        status="success",
        amount=Decimal("100.00"),
        provider_data={"provider": "yookassa"}
    )
    
    await _process_payment_result(webhook_result, db_session)
    
    # Verify deal was created
    deal_result = await db_session.execute(
        select(Deal).where(Deal.order_id == order.id)
    )
    deal = deal_result.scalar_one()
    
    # Validate escrow holding (Requirement 8.1)
    assert deal is not None
    assert deal.amount == Decimal("100.00")
    assert deal.commission_amount == Decimal("10.00")  # 10% commission
    assert deal.seller_amount == Decimal("90.00")
    assert deal.escrow_released == False
    assert deal.buyer_id == user.id
    assert deal.seller_id == seller.id
    assert deal.lot_id == lot.id


@pytest.mark.asyncio
async def test_auto_delivery_marks_stock_as_sold(db_session: AsyncSession):
    """Test that auto-delivery immediately marks stock items as sold.
    
    Validates: Requirement 8.2
    """
    # Create test data (similar to above)
    user = User(
        telegram_id=123456789,
        username="buyer",
        balance=Decimal("0.00"),
        referral_code="BUYER123"
    )
    db_session.add(user)
    
    seller_user = User(
        telegram_id=987654321,
        username="seller",
        balance=Decimal("0.00"),
        referral_code="SELLER123"
    )
    db_session.add(seller_user)
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        status=SellerStatus.ACTIVE,
        shop_name="Test Shop",
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    game = Game(slug="test-game", title="Test Game")
    db_session.add(game)
    await db_session.flush()
    
    category = Category(game_id=game.id, slug="test-cat", title="Test Category")
    db_session.add(category)
    await db_session.flush()
    
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product",
        title="Test Product"
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create lot with AUTO delivery
    lot = Lot(
        seller_id=seller.id,
        product_id=product.id,
        title="Test Lot Auto",
        price=Decimal("50.00"),
        delivery_type=LotDeliveryType.AUTO,
        status=LotStatus.ACTIVE,
        stock_count=5
    )
    db_session.add(lot)
    await db_session.flush()
    
    # Create stock items
    stock_items = []
    for i in range(5):
        stock_item = LotStockItem(
            lot_id=lot.id,
            data=f"ITEM-CODE-{i+1}",
            is_sold=False,
            is_reserved=False
        )
        db_session.add(stock_item)
        stock_items.append(stock_item)
    await db_session.flush()
    
    # Create order
    order = Order(
        order_number="GP-TEST-002",
        user_id=user.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("100.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create order item for 2 items
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        title_snapshot="Test Product",
        quantity=2,
        unit_price=Decimal("50.00"),
        total_price=Decimal("100.00"),
        fulfillment_type="manual",
        metadata_json={"lot_id": lot.id}
    )
    db_session.add(order_item)
    await db_session.flush()
    
    # Create payment
    payment = Payment(
        order_id=order.id,
        payment_provider="yookassa",
        external_payment_id="test_payment_456",
        amount=Decimal("100.00"),
        currency="RUB",
        status="pending"
    )
    db_session.add(payment)
    await db_session.flush()
    
    # Process payment success
    webhook_result = WebhookResult(
        payment_id="test_payment_456",
        order_id=order.id,
        status="success",
        amount=Decimal("100.00"),
        provider_data={"provider": "yookassa"}
    )
    
    await _process_payment_result(webhook_result, db_session)
    
    # Verify deal was created
    deal_result = await db_session.execute(
        select(Deal).where(Deal.order_id == order.id)
    )
    deal = deal_result.scalar_one()
    
    # Validate auto-delivery (Requirement 8.2)
    assert deal.status == DealStatus.WAITING_CONFIRMATION
    
    # Verify stock items marked as sold
    sold_items_result = await db_session.execute(
        select(LotStockItem).where(
            LotStockItem.lot_id == lot.id,
            LotStockItem.is_sold == True
        )
    )
    sold_items = sold_items_result.scalars().all()
    
    assert len(sold_items) == 2
    for item in sold_items:
        assert item.deal_id == deal.id
        assert item.sold_at is not None
    
    # Verify lot counters updated
    await db_session.refresh(lot)
    assert lot.sold_count == 2
    assert lot.stock_count == 3
    
    # Verify delivery message created
    message_result = await db_session.execute(
        select(DealMessage).where(
            DealMessage.deal_id == deal.id,
            DealMessage.is_system == True
        )
    )
    delivery_message = message_result.scalar_one()
    
    assert "Auto-delivery completed" in delivery_message.message_text
    assert "ITEM-CODE-" in delivery_message.message_text


@pytest.mark.asyncio
async def test_manual_delivery_notifies_seller(db_session: AsyncSession):
    """Test that manual delivery updates status and notifies seller.
    
    Validates: Requirement 8.3
    """
    # Create test data
    user = User(
        telegram_id=123456789,
        username="buyer",
        balance=Decimal("0.00"),
        referral_code="BUYER123"
    )
    db_session.add(user)
    
    seller_user = User(
        telegram_id=987654321,
        username="seller",
        balance=Decimal("0.00"),
        referral_code="SELLER123"
    )
    db_session.add(seller_user)
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        status=SellerStatus.ACTIVE,
        shop_name="Test Shop",
        commission_percent=Decimal("15.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    game = Game(slug="test-game", title="Test Game")
    db_session.add(game)
    await db_session.flush()
    
    category = Category(game_id=game.id, slug="test-cat", title="Test Category")
    db_session.add(category)
    await db_session.flush()
    
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product",
        title="Test Product"
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create lot with MANUAL delivery
    lot = Lot(
        seller_id=seller.id,
        product_id=product.id,
        title="Test Lot Manual",
        price=Decimal("200.00"),
        delivery_type=LotDeliveryType.MANUAL,
        status=LotStatus.ACTIVE
    )
    db_session.add(lot)
    await db_session.flush()
    
    # Create order
    order = Order(
        order_number="GP-TEST-003",
        user_id=user.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("200.00"),
        total_amount=Decimal("200.00"),
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
        unit_price=Decimal("200.00"),
        total_price=Decimal("200.00"),
        fulfillment_type="manual",
        metadata_json={"lot_id": lot.id}
    )
    db_session.add(order_item)
    await db_session.flush()
    
    # Create payment
    payment = Payment(
        order_id=order.id,
        payment_provider="yookassa",
        external_payment_id="test_payment_789",
        amount=Decimal("200.00"),
        currency="RUB",
        status="pending"
    )
    db_session.add(payment)
    await db_session.flush()
    
    # Process payment success
    webhook_result = WebhookResult(
        payment_id="test_payment_789",
        order_id=order.id,
        status="success",
        amount=Decimal("200.00"),
        provider_data={"provider": "yookassa"}
    )
    
    await _process_payment_result(webhook_result, db_session)
    
    # Verify deal was created
    deal_result = await db_session.execute(
        select(Deal).where(Deal.order_id == order.id)
    )
    deal = deal_result.scalar_one()
    
    # Validate manual delivery (Requirement 8.3)
    assert deal.status == DealStatus.IN_PROGRESS
    
    # Verify notification was created for seller
    from app.models.entities import Notification
    notification_result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == seller_user.id,
            Notification.notification_type == NotificationType.NEW_ORDER
        )
    )
    notification = notification_result.scalar_one()
    
    assert notification is not None
    assert "New Order Received" in notification.title
    assert lot.title in notification.message
    assert notification.reference_type == "deal"
    assert notification.reference_id == deal.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
