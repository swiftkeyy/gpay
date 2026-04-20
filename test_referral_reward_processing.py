"""Test script to verify referral reward processing functionality.

This script tests the referral reward implementation for requirements:
- 14.3: Calculate referral reward as configured percentage of order amount
- 14.4: Add the reward amount to referrer balance
- 14.5: Return count of invited users and total rewards earned

Run with: python -m pytest test_referral_reward_processing.py -v
"""
import asyncio
from decimal import Decimal
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base, User, Order, OrderItem, OrderStatus, Referral, ReferralReward,
    Transaction, TransactionType, TransactionStatus, Product, Game, Category,
    ReferralRewardType
)


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_referral_reward_on_first_purchase(db_session: AsyncSession):
    """Test that referral reward is calculated and added on first purchase (Req 14.3, 14.4)."""
    print("\n=== Testing Referral Reward on First Purchase (Req 14.3, 14.4) ===")
    
    # Create referrer user
    referrer = User(
        telegram_id=111111111,
        username="referrer",
        first_name="Referrer",
        balance=Decimal("0.00"),
        referral_code="REF123456"
    )
    db_session.add(referrer)
    await db_session.flush()
    
    # Create referred user
    referred = User(
        telegram_id=222222222,
        username="referred",
        first_name="Referred",
        balance=Decimal("0.00"),
        referred_by_user_id=referrer.id,
        referral_code="REF789012"
    )
    db_session.add(referred)
    await db_session.flush()
    
    # Create referral record
    referral = Referral(
        referrer_user_id=referrer.id,
        referred_user_id=referred.id,
        referral_code=referrer.referral_code
    )
    db_session.add(referral)
    await db_session.flush()
    
    # Create a game and category for the product
    game = Game(
        slug="test-game",
        title="Test Game",
        is_active=True
    )
    db_session.add(game)
    await db_session.flush()
    
    category = Category(
        game_id=game.id,
        slug="test-category",
        title="Test Category",
        is_active=True
    )
    db_session.add(category)
    await db_session.flush()
    
    # Create a product
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product",
        title="Test Product",
        is_active=True
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create order for referred user (first purchase)
    order = Order(
        order_number="ORD001",
        user_id=referred.id,
        status=OrderStatus.PAID,
        subtotal_amount=Decimal("1000.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("1000.00"),
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
        unit_price=Decimal("1000.00"),
        total_price=Decimal("1000.00"),
        fulfillment_type="manual"
    )
    db_session.add(order_item)
    await db_session.flush()
    
    print(f"  Order created: {order.order_number}, total: {order.total_amount}")
    print(f"  Referrer balance before: {referrer.balance}")
    
    # Import and call the referral reward processing function
    from api.routers.payments import _process_referral_reward
    await _process_referral_reward(order, db_session)
    await db_session.commit()
    
    # Refresh referrer to get updated balance
    await db_session.refresh(referrer)
    
    # Calculate expected reward (5% of 1000.00 = 50.00)
    expected_reward = Decimal("50.00")
    
    # Verify referrer balance increased (Requirement 14.4)
    assert referrer.balance == expected_reward, \
        f"Referrer balance should be {expected_reward}, got {referrer.balance}"
    print(f"  ✓ Referrer balance after: {referrer.balance}")
    
    # Verify ReferralReward record was created
    stmt = select(ReferralReward).where(ReferralReward.referral_id == referral.id)
    reward_record = await db_session.scalar(stmt)
    
    assert reward_record is not None, "ReferralReward record should be created"
    assert reward_record.order_id == order.id
    assert reward_record.reward_value == expected_reward
    assert reward_record.reward_type == ReferralRewardType.PERCENT
    assert reward_record.issued_at is not None
    print(f"  ✓ ReferralReward record created: {reward_record.reward_value}")
    
    # Verify Transaction record was created (Requirement 14.4)
    stmt = select(Transaction).where(
        Transaction.user_id == referrer.id,
        Transaction.transaction_type == TransactionType.REFERRAL_REWARD
    )
    transaction = await db_session.scalar(stmt)
    
    assert transaction is not None, "Transaction record should be created"
    assert transaction.amount == expected_reward
    assert transaction.status == TransactionStatus.COMPLETED
    assert transaction.balance_before == Decimal("0.00")
    assert transaction.balance_after == expected_reward
    print(f"  ✓ Transaction record created: {transaction.amount}")


@pytest.mark.asyncio
async def test_no_reward_on_second_purchase(db_session: AsyncSession):
    """Test that no reward is given on second purchase."""
    print("\n=== Testing No Reward on Second Purchase ===")
    
    # Create referrer user
    referrer = User(
        telegram_id=333333333,
        username="referrer2",
        first_name="Referrer2",
        balance=Decimal("50.00"),  # Already has reward from first purchase
        referral_code="REF234567"
    )
    db_session.add(referrer)
    await db_session.flush()
    
    # Create referred user
    referred = User(
        telegram_id=444444444,
        username="referred2",
        first_name="Referred2",
        balance=Decimal("0.00"),
        referred_by_user_id=referrer.id,
        referral_code="REF890123"
    )
    db_session.add(referred)
    await db_session.flush()
    
    # Create referral record
    referral = Referral(
        referrer_user_id=referrer.id,
        referred_user_id=referred.id,
        referral_code=referrer.referral_code
    )
    db_session.add(referral)
    await db_session.flush()
    
    # Create a game and category for the product
    game = Game(
        slug="test-game-2",
        title="Test Game 2",
        is_active=True
    )
    db_session.add(game)
    await db_session.flush()
    
    category = Category(
        game_id=game.id,
        slug="test-category-2",
        title="Test Category 2",
        is_active=True
    )
    db_session.add(category)
    await db_session.flush()
    
    # Create a product
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product-2",
        title="Test Product 2",
        is_active=True
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create first order (already completed)
    first_order = Order(
        order_number="ORD002",
        user_id=referred.id,
        status=OrderStatus.PAID,
        subtotal_amount=Decimal("500.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("500.00"),
        currency_code="RUB"
    )
    db_session.add(first_order)
    await db_session.flush()
    
    # Create order item for first order
    first_order_item = OrderItem(
        order_id=first_order.id,
        product_id=product.id,
        title_snapshot="Test Product 2",
        quantity=1,
        unit_price=Decimal("500.00"),
        total_price=Decimal("500.00"),
        fulfillment_type="manual"
    )
    db_session.add(first_order_item)
    await db_session.flush()
    
    # Create reward for first order
    first_reward = ReferralReward(
        referral_id=referral.id,
        order_id=first_order.id,
        reward_type=ReferralRewardType.PERCENT,
        reward_value=Decimal("25.00"),
        issued_at=datetime.utcnow()
    )
    db_session.add(first_reward)
    await db_session.flush()
    
    # Create second order
    second_order = Order(
        order_number="ORD003",
        user_id=referred.id,
        status=OrderStatus.PAID,
        subtotal_amount=Decimal("1000.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("1000.00"),
        currency_code="RUB"
    )
    db_session.add(second_order)
    await db_session.flush()
    
    # Create order item for second order
    second_order_item = OrderItem(
        order_id=second_order.id,
        product_id=product.id,
        title_snapshot="Test Product 2",
        quantity=1,
        unit_price=Decimal("1000.00"),
        total_price=Decimal("1000.00"),
        fulfillment_type="manual"
    )
    db_session.add(second_order_item)
    await db_session.flush()
    
    print(f"  Second order created: {second_order.order_number}, total: {second_order.total_amount}")
    print(f"  Referrer balance before: {referrer.balance}")
    
    # Import and call the referral reward processing function
    from api.routers.payments import _process_referral_reward
    await _process_referral_reward(second_order, db_session)
    await db_session.commit()
    
    # Refresh referrer to get updated balance
    await db_session.refresh(referrer)
    
    # Verify referrer balance did NOT increase
    assert referrer.balance == Decimal("50.00"), \
        f"Referrer balance should remain 50.00, got {referrer.balance}"
    print(f"  ✓ Referrer balance unchanged: {referrer.balance}")
    
    # Verify no new ReferralReward record was created
    stmt = select(ReferralReward).where(ReferralReward.order_id == second_order.id)
    reward_record = await db_session.scalar(stmt)
    
    assert reward_record is None, "No new ReferralReward record should be created for second purchase"
    print(f"  ✓ No new reward record created for second purchase")


@pytest.mark.asyncio
async def test_no_reward_for_non_referred_user(db_session: AsyncSession):
    """Test that no reward is given for users without referrer."""
    print("\n=== Testing No Reward for Non-Referred User ===")
    
    # Create user without referrer
    user = User(
        telegram_id=555555555,
        username="normaluser",
        first_name="NormalUser",
        balance=Decimal("0.00"),
        referral_code="REF345678"
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create a game and category for the product
    game = Game(
        slug="test-game-3",
        title="Test Game 3",
        is_active=True
    )
    db_session.add(game)
    await db_session.flush()
    
    category = Category(
        game_id=game.id,
        slug="test-category-3",
        title="Test Category 3",
        is_active=True
    )
    db_session.add(category)
    await db_session.flush()
    
    # Create a product
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product-3",
        title="Test Product 3",
        is_active=True
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create order
    order = Order(
        order_number="ORD004",
        user_id=user.id,
        status=OrderStatus.PAID,
        subtotal_amount=Decimal("1000.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("1000.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create order item
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        title_snapshot="Test Product 3",
        quantity=1,
        unit_price=Decimal("1000.00"),
        total_price=Decimal("1000.00"),
        fulfillment_type="manual"
    )
    db_session.add(order_item)
    await db_session.flush()
    
    print(f"  Order created for non-referred user: {order.order_number}")
    
    # Import and call the referral reward processing function
    from api.routers.payments import _process_referral_reward
    await _process_referral_reward(order, db_session)
    await db_session.commit()
    
    # Verify no ReferralReward record was created
    stmt = select(ReferralReward).where(ReferralReward.order_id == order.id)
    reward_record = await db_session.scalar(stmt)
    
    assert reward_record is None, "No ReferralReward record should be created for non-referred user"
    print(f"  ✓ No reward record created for non-referred user")
    
    # Verify no Transaction record was created
    stmt = select(Transaction).where(
        Transaction.reference_type == "referral_reward",
        Transaction.reference_id == order.id
    )
    transaction = await db_session.scalar(stmt)
    
    assert transaction is None, "No transaction record should be created"
    print(f"  ✓ No transaction record created")


@pytest.mark.asyncio
async def test_referral_stats_endpoint_data(db_session: AsyncSession):
    """Test that referral stats return correct data (Req 14.5)."""
    print("\n=== Testing Referral Stats Data (Req 14.5) ===")
    
    # Create referrer user
    referrer = User(
        telegram_id=666666666,
        username="referrer3",
        first_name="Referrer3",
        balance=Decimal("150.00"),
        referral_code="REF456789"
    )
    db_session.add(referrer)
    await db_session.flush()
    
    # Create 3 referred users
    referred_users = []
    for i in range(3):
        referred = User(
            telegram_id=700000000 + i,
            username=f"referred{i}",
            first_name=f"Referred{i}",
            balance=Decimal("0.00"),
            referred_by_user_id=referrer.id,
            referral_code=f"REF{800000 + i}"
        )
        db_session.add(referred)
        await db_session.flush()
        referred_users.append(referred)
    
    # Create referral records
    for referred in referred_users:
        referral = Referral(
            referrer_user_id=referrer.id,
            referred_user_id=referred.id,
            referral_code=referrer.referral_code
        )
        db_session.add(referral)
    await db_session.flush()
    
    # Create transaction records for rewards
    total_rewards = Decimal("0.00")
    for i, amount in enumerate([Decimal("50.00"), Decimal("75.00"), Decimal("25.00")]):
        transaction = Transaction(
            user_id=referrer.id,
            transaction_type=TransactionType.REFERRAL_REWARD,
            amount=amount,
            currency_code="RUB",
            status=TransactionStatus.COMPLETED,
            balance_before=total_rewards,
            balance_after=total_rewards + amount,
            description=f"Referral reward {i+1}"
        )
        db_session.add(transaction)
        total_rewards += amount
    await db_session.flush()
    await db_session.commit()
    
    # Query referral stats (simulating the endpoint logic)
    from sqlalchemy import func
    
    # Get total referrals count (Requirement 14.5)
    result = await db_session.execute(
        select(func.count(User.id)).where(User.referred_by_user_id == referrer.id)
    )
    total_referrals = result.scalar() or 0
    
    # Get total earned from referrals (Requirement 14.5)
    result = await db_session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == referrer.id,
            Transaction.transaction_type == TransactionType.REFERRAL_REWARD
        )
    )
    total_earned = float(result.scalar() or 0)
    
    # Verify stats
    assert total_referrals == 3, f"Should have 3 referrals, got {total_referrals}"
    assert total_earned == 150.00, f"Should have earned 150.00, got {total_earned}"
    
    print(f"  ✓ Total referrals: {total_referrals}")
    print(f"  ✓ Total earned: {total_earned}")
    print(f"  ✓ Referral code: {referrer.referral_code}")


if __name__ == "__main__":
    print("=" * 70)
    print("REFERRAL REWARD PROCESSING TESTS")
    print("Testing Requirements: 14.3, 14.4, 14.5")
    print("=" * 70)
    
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
