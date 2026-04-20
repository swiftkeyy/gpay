"""Test delivery confirmation and escrow release functionality.

Validates: Requirements 8.4, 8.5, 8.6, 8.7, 8.8, 8.9
- 8.4: Seller delivers goods and updates status to waiting_confirmation
- 8.5: Buyer confirms delivery and releases escrow to seller
- 8.6: Auto-complete deals after 72 hours timeout
- 8.7: Calculate commission and seller amount correctly
- 8.8: Create transaction records for seller payment and commission
- 8.9: Set auto-completion timeout to 72 hours after delivery
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import (
    Order, OrderItem, User, Seller, Lot, Deal, Transaction,
    Payment, Product, Game, Category
)
from app.models.enums import (
    OrderStatus, DealStatus, LotDeliveryType, SellerStatus,
    LotStatus, TransactionType, TransactionStatus
)
from api.routers.deals import deliver_goods, confirm_delivery, auto_complete_deals
from api.routers.payments import _process_payment_result
from api.services.payment_providers import WebhookResult


async def create_test_deal(db_session: AsyncSession, delivery_type: LotDeliveryType = LotDeliveryType.MANUAL):
    """Helper function to create a test deal."""
    # Create buyer
    buyer = User(
        telegram_id=123456789,
        username="buyer",
        balance=Decimal("0.00"),
        referral_code="BUYER123"
    )
    db_session.add(buyer)
    
    # Create seller user
    seller_user = User(
        telegram_id=987654321,
        username="seller",
        balance=Decimal("0.00"),
        referral_code="SELLER123"
    )
    db_session.add(seller_user)
    await db_session.flush()
    
    # Create seller
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
        delivery_type=delivery_type,
        status=LotStatus.ACTIVE
    )
    db_session.add(lot)
    await db_session.flush()
    
    # Create order
    order = Order(
        order_number="GP-TEST-001",
        user_id=buyer.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("100.00"),
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
    
    # Process payment success to create deal
    webhook_result = WebhookResult(
        payment_id="test_payment_123",
        order_id=order.id,
        status="success",
        amount=Decimal("100.00"),
        provider_data={"provider": "yookassa"}
    )
    
    await _process_payment_result(webhook_result, db_session)
    
    # Get created deal
    deal_result = await db_session.execute(
        select(Deal).where(Deal.order_id == order.id)
    )
    deal = deal_result.scalar_one()
    
    return {
        "buyer": buyer,
        "seller_user": seller_user,
        "seller": seller,
        "lot": lot,
        "order": order,
        "deal": deal
    }


@pytest.mark.asyncio
async def test_seller_delivers_goods(db_session: AsyncSession):
    """Test that seller can deliver goods and status updates correctly.
    
    Validates: Requirements 8.4, 8.9
    - 8.4: Update deal status to waiting_confirmation when seller delivers
    - 8.9: Set auto-completion timeout to 72 hours after delivery
    """
    # Create test deal
    test_data = await create_test_deal(db_session)
    deal = test_data["deal"]
    seller_user = test_data["seller_user"]
    
    # Verify initial state
    assert deal.status == DealStatus.IN_PROGRESS
    assert deal.delivered_at is None
    assert deal.auto_complete_at is None
    
    # Mock the request
    from api.routers.deals import DeliverGoodsRequest
    request = DeliverGoodsRequest(
        delivery_data="Account credentials: user123 / pass456",
        comment="Please check and confirm delivery"
    )
    
    # Deliver goods
    before_delivery = datetime.utcnow()
    response = await deliver_goods(
        deal_id=deal.id,
        request=request,
        user_id=seller_user.id,
        session=db_session
    )
    after_delivery = datetime.utcnow()
    
    # Refresh deal
    await db_session.refresh(deal)
    
    # Validate status update (Requirement 8.4)
    assert deal.status == DealStatus.WAITING_CONFIRMATION
    assert deal.delivered_at is not None
    assert before_delivery <= deal.delivered_at <= after_delivery
    
    # Validate auto-completion timeout (Requirement 8.9)
    assert deal.auto_complete_at is not None
    expected_auto_complete = deal.delivered_at + timedelta(hours=72)
    # Allow 1 second tolerance
    assert abs((deal.auto_complete_at - expected_auto_complete).total_seconds()) < 1
    
    # Verify response
    assert response["status"] == DealStatus.WAITING_CONFIRMATION.value
    assert "auto_complete_at" in response


@pytest.mark.asyncio
async def test_buyer_confirms_delivery_releases_escrow(db_session: AsyncSession):
    """Test that buyer confirmation releases escrow to seller.
    
    Validates: Requirements 8.5, 8.7, 8.8
    - 8.5: Release escrow funds to seller balance minus commission
    - 8.7: Calculate commission amount and seller amount correctly
    - 8.8: Create transaction records for seller payment and commission
    """
    # Create test deal
    test_data = await create_test_deal(db_session)
    deal = test_data["deal"]
    buyer = test_data["buyer"]
    seller_user = test_data["seller_user"]
    seller = test_data["seller"]
    
    # Deliver goods first
    from api.routers.deals import DeliverGoodsRequest
    deliver_request = DeliverGoodsRequest(
        delivery_data="Account credentials",
        comment="Delivered"
    )
    await deliver_goods(
        deal_id=deal.id,
        request=deliver_request,
        user_id=seller_user.id,
        session=db_session
    )
    
    # Refresh deal
    await db_session.refresh(deal)
    assert deal.status == DealStatus.WAITING_CONFIRMATION
    
    # Record initial balance
    await db_session.refresh(seller_user)
    initial_balance = seller_user.balance
    
    # Buyer confirms delivery
    from api.routers.deals import ConfirmDeliveryRequest
    confirm_request = ConfirmDeliveryRequest(
        rating=5,
        comment="Great service!"
    )
    
    response = await confirm_delivery(
        deal_id=deal.id,
        request=confirm_request,
        user_id=buyer.id,
        session=db_session
    )
    
    # Refresh entities
    await db_session.refresh(deal)
    await db_session.refresh(seller_user)
    
    # Validate deal completion (Requirement 8.5)
    assert deal.status == DealStatus.COMPLETED
    assert deal.completed_at is not None
    assert deal.buyer_confirmed == True
    assert deal.buyer_confirmed_at is not None
    assert deal.escrow_released == True
    assert deal.escrow_released_at is not None
    
    # Validate commission calculation (Requirement 8.7)
    assert deal.amount == Decimal("100.00")
    assert deal.commission_amount == Decimal("10.00")  # 10% of 100
    assert deal.seller_amount == Decimal("90.00")  # 100 - 10
    
    # Validate seller balance update (Requirement 8.5)
    assert seller_user.balance == initial_balance + deal.seller_amount
    assert seller_user.balance == Decimal("90.00")
    
    # Validate transaction records (Requirement 8.8)
    transactions_result = await db_session.execute(
        select(Transaction).where(
            Transaction.user_id == seller_user.id,
            Transaction.reference_type == "deal",
            Transaction.reference_id == deal.id
        ).order_by(Transaction.id)
    )
    transactions = transactions_result.scalars().all()
    
    assert len(transactions) == 2
    
    # Check seller payment transaction
    seller_transaction = transactions[0]
    assert seller_transaction.transaction_type == TransactionType.SALE
    assert seller_transaction.amount == Decimal("90.00")
    assert seller_transaction.status == TransactionStatus.COMPLETED
    assert seller_transaction.balance_before == Decimal("0.00")
    assert seller_transaction.balance_after == Decimal("90.00")
    assert f"deal #{deal.id}" in seller_transaction.description.lower()
    
    # Check commission transaction
    commission_transaction = transactions[1]
    assert commission_transaction.transaction_type == TransactionType.COMMISSION
    assert commission_transaction.amount == Decimal("-10.00")
    assert commission_transaction.status == TransactionStatus.COMPLETED
    assert f"deal #{deal.id}" in commission_transaction.description.lower()


@pytest.mark.asyncio
async def test_auto_complete_after_timeout(db_session: AsyncSession):
    """Test that deals auto-complete after 72 hours timeout.
    
    Validates: Requirements 8.6, 8.7, 8.8, 8.9
    - 8.6: Automatically release escrow and complete deal after timeout
    - 8.7: Calculate commission and seller amount correctly
    - 8.8: Create transaction records
    - 8.9: Timeout is 72 hours after delivery
    """
    # Create test deal
    test_data = await create_test_deal(db_session)
    deal = test_data["deal"]
    seller_user = test_data["seller_user"]
    
    # Deliver goods
    from api.routers.deals import DeliverGoodsRequest
    deliver_request = DeliverGoodsRequest(
        delivery_data="Account credentials",
        comment="Delivered"
    )
    await deliver_goods(
        deal_id=deal.id,
        request=deliver_request,
        user_id=seller_user.id,
        session=db_session
    )
    
    # Refresh deal
    await db_session.refresh(deal)
    assert deal.status == DealStatus.WAITING_CONFIRMATION
    
    # Manually set auto_complete_at to past (simulate 72 hours passed)
    deal.auto_complete_at = datetime.utcnow() - timedelta(hours=1)
    await db_session.commit()
    
    # Record initial balance
    await db_session.refresh(seller_user)
    initial_balance = seller_user.balance
    
    # Run auto-complete
    response = await auto_complete_deals(session=db_session)
    
    # Refresh entities
    await db_session.refresh(deal)
    await db_session.refresh(seller_user)
    
    # Validate auto-completion (Requirement 8.6)
    assert deal.status == DealStatus.COMPLETED
    assert deal.completed_at is not None
    assert deal.buyer_confirmed == False  # Auto-completed, not manually confirmed
    assert deal.escrow_released == True
    assert deal.escrow_released_at is not None
    
    # Validate commission calculation (Requirement 8.7)
    assert deal.commission_amount == Decimal("10.00")
    assert deal.seller_amount == Decimal("90.00")
    
    # Validate seller balance (Requirement 8.6)
    assert seller_user.balance == initial_balance + deal.seller_amount
    
    # Validate transaction records (Requirement 8.8)
    transactions_result = await db_session.execute(
        select(Transaction).where(
            Transaction.user_id == seller_user.id,
            Transaction.reference_type == "deal",
            Transaction.reference_id == deal.id
        )
    )
    transactions = transactions_result.scalars().all()
    
    assert len(transactions) == 2
    assert any(t.transaction_type == TransactionType.SALE for t in transactions)
    assert any(t.transaction_type == TransactionType.COMMISSION for t in transactions)
    
    # Validate response
    assert response["count"] == 1
    assert "Auto-completed" in response["message"]


@pytest.mark.asyncio
async def test_auto_complete_does_not_affect_already_released(db_session: AsyncSession):
    """Test that auto-complete skips deals with already released escrow."""
    # Create test deal
    test_data = await create_test_deal(db_session)
    deal = test_data["deal"]
    seller_user = test_data["seller_user"]
    buyer = test_data["buyer"]
    
    # Deliver and confirm manually
    from api.routers.deals import DeliverGoodsRequest, ConfirmDeliveryRequest
    
    deliver_request = DeliverGoodsRequest(
        delivery_data="Account credentials",
        comment="Delivered"
    )
    await deliver_goods(
        deal_id=deal.id,
        request=deliver_request,
        user_id=seller_user.id,
        session=db_session
    )
    
    confirm_request = ConfirmDeliveryRequest(rating=5)
    await confirm_delivery(
        deal_id=deal.id,
        request=confirm_request,
        user_id=buyer.id,
        session=db_session
    )
    
    # Refresh deal
    await db_session.refresh(deal)
    assert deal.escrow_released == True
    
    # Record balance
    await db_session.refresh(seller_user)
    balance_after_confirm = seller_user.balance
    
    # Set auto_complete_at to past
    deal.auto_complete_at = datetime.utcnow() - timedelta(hours=1)
    await db_session.commit()
    
    # Run auto-complete
    response = await auto_complete_deals(session=db_session)
    
    # Refresh seller
    await db_session.refresh(seller_user)
    
    # Validate that nothing changed
    assert seller_user.balance == balance_after_confirm
    assert response["count"] == 0


@pytest.mark.asyncio
async def test_commission_calculation_with_different_percentages(db_session: AsyncSession):
    """Test commission calculation with different seller commission percentages.
    
    Validates: Requirement 8.7
    """
    # Test with 15% commission
    buyer = User(
        telegram_id=111111111,
        username="buyer2",
        balance=Decimal("0.00"),
        referral_code="BUYER456"
    )
    db_session.add(buyer)
    
    seller_user = User(
        telegram_id=222222222,
        username="seller2",
        balance=Decimal("0.00"),
        referral_code="SELLER456"
    )
    db_session.add(seller_user)
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        status=SellerStatus.ACTIVE,
        shop_name="Test Shop 2",
        commission_percent=Decimal("15.00")  # 15% commission
    )
    db_session.add(seller)
    await db_session.flush()
    
    game = Game(slug="test-game-2", title="Test Game 2")
    db_session.add(game)
    await db_session.flush()
    
    category = Category(game_id=game.id, slug="test-cat-2", title="Test Category 2")
    db_session.add(category)
    await db_session.flush()
    
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product-2",
        title="Test Product 2"
    )
    db_session.add(product)
    await db_session.flush()
    
    lot = Lot(
        seller_id=seller.id,
        product_id=product.id,
        title="Test Lot 2",
        price=Decimal("200.00"),
        delivery_type=LotDeliveryType.MANUAL,
        status=LotStatus.ACTIVE
    )
    db_session.add(lot)
    await db_session.flush()
    
    order = Order(
        order_number="GP-TEST-002",
        user_id=buyer.id,
        status=OrderStatus.WAITING_PAYMENT,
        subtotal_amount=Decimal("200.00"),
        total_amount=Decimal("200.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        title_snapshot="Test Product 2",
        quantity=1,
        unit_price=Decimal("200.00"),
        total_price=Decimal("200.00"),
        fulfillment_type="manual",
        metadata_json={"lot_id": lot.id}
    )
    db_session.add(order_item)
    await db_session.flush()
    
    payment = Payment(
        order_id=order.id,
        payment_provider="yookassa",
        external_payment_id="test_payment_999",
        amount=Decimal("200.00"),
        currency="RUB",
        status="pending"
    )
    db_session.add(payment)
    await db_session.flush()
    
    # Process payment
    webhook_result = WebhookResult(
        payment_id="test_payment_999",
        order_id=order.id,
        status="success",
        amount=Decimal("200.00"),
        provider_data={"provider": "yookassa"}
    )
    
    await _process_payment_result(webhook_result, db_session)
    
    # Get deal
    deal_result = await db_session.execute(
        select(Deal).where(Deal.order_id == order.id)
    )
    deal = deal_result.scalar_one()
    
    # Validate commission calculation (Requirement 8.7)
    assert deal.amount == Decimal("200.00")
    assert deal.commission_amount == Decimal("30.00")  # 15% of 200
    assert deal.seller_amount == Decimal("170.00")  # 200 - 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
