"""Test dispute system implementation.

Tests for Task 9.3: Implement dispute system
Validates Requirements 10.1-10.8
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    User, Seller, Lot, Deal, DealDispute, Notification, Admin, Transaction
)
from app.models.enums import (
    DealStatus, DisputeStatus, NotificationType, TransactionType, TransactionStatus
)


@pytest.mark.asyncio
async def test_open_dispute_creates_record(db_session: AsyncSession):
    """Test Requirement 10.1: Create dispute record with initiator, reason, and timestamp."""
    # Create test data
    buyer = User(
        telegram_id=123456,
        username="buyer",
        balance=Decimal("1000.00")
    )
    seller_user = User(
        telegram_id=789012,
        username="seller",
        balance=Decimal("0.00")
    )
    db_session.add_all([buyer, seller_user])
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        shop_name="Test Shop",
        status="active",
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    lot = Lot(
        seller_id=seller.id,
        product_id=1,
        title="Test Lot",
        price=Decimal("100.00"),
        status="active"
    )
    db_session.add(lot)
    await db_session.flush()
    
    deal = Deal(
        order_id=1,
        buyer_id=buyer.id,
        seller_id=seller.id,
        lot_id=lot.id,
        status=DealStatus.WAITING_CONFIRMATION,
        amount=Decimal("100.00"),
        commission_amount=Decimal("10.00"),
        seller_amount=Decimal("90.00")
    )
    db_session.add(deal)
    await db_session.flush()
    
    # Open dispute
    dispute = DealDispute(
        deal_id=deal.id,
        initiator_id=buyer.id,
        reason="Product not received",
        description="I paid but didn't receive the product",
        status=DisputeStatus.OPEN
    )
    db_session.add(dispute)
    await db_session.commit()
    
    # Verify dispute was created
    result = await db_session.execute(
        select(DealDispute).where(DealDispute.deal_id == deal.id)
    )
    created_dispute = result.scalar_one()
    
    assert created_dispute.initiator_id == buyer.id
    assert created_dispute.reason == "Product not received"
    assert created_dispute.description == "I paid but didn't receive the product"
    assert created_dispute.status == DisputeStatus.OPEN
    assert created_dispute.created_at is not None


@pytest.mark.asyncio
async def test_dispute_prevents_auto_completion(db_session: AsyncSession):
    """Test Requirement 10.2: Update deal status to dispute and prevent automatic completion."""
    # Create test data
    buyer = User(telegram_id=123456, username="buyer", balance=Decimal("1000.00"))
    seller_user = User(telegram_id=789012, username="seller", balance=Decimal("0.00"))
    db_session.add_all([buyer, seller_user])
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        shop_name="Test Shop",
        status="active",
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    lot = Lot(
        seller_id=seller.id,
        product_id=1,
        title="Test Lot",
        price=Decimal("100.00"),
        status="active"
    )
    db_session.add(lot)
    await db_session.flush()
    
    # Create deal with auto_complete_at set
    deal = Deal(
        order_id=1,
        buyer_id=buyer.id,
        seller_id=seller.id,
        lot_id=lot.id,
        status=DealStatus.WAITING_CONFIRMATION,
        amount=Decimal("100.00"),
        commission_amount=Decimal("10.00"),
        seller_amount=Decimal("90.00"),
        auto_complete_at=datetime.utcnow() + timedelta(hours=72)
    )
    db_session.add(deal)
    await db_session.flush()
    
    # Open dispute and update deal
    dispute = DealDispute(
        deal_id=deal.id,
        initiator_id=buyer.id,
        reason="Product not received",
        status=DisputeStatus.OPEN
    )
    db_session.add(dispute)
    
    # Update deal status to dispute and clear auto_complete_at
    deal.status = DealStatus.DISPUTE
    deal.auto_complete_at = None
    
    await db_session.commit()
    
    # Verify deal status and auto_complete_at
    result = await db_session.execute(
        select(Deal).where(Deal.id == deal.id)
    )
    updated_deal = result.scalar_one()
    
    assert updated_deal.status == DealStatus.DISPUTE
    assert updated_deal.auto_complete_at is None


@pytest.mark.asyncio
async def test_dispute_notifies_admin(db_session: AsyncSession):
    """Test Requirement 10.3: Notify admin via notification system."""
    # Create admin user
    admin_user = User(telegram_id=999999, username="admin", balance=Decimal("0.00"))
    db_session.add(admin_user)
    await db_session.flush()
    
    admin = Admin(
        user_id=admin_user.id,
        role="super_admin",
        is_active=True
    )
    db_session.add(admin)
    await db_session.flush()
    
    # Create test data
    buyer = User(telegram_id=123456, username="buyer", balance=Decimal("1000.00"))
    seller_user = User(telegram_id=789012, username="seller", balance=Decimal("0.00"))
    db_session.add_all([buyer, seller_user])
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        shop_name="Test Shop",
        status="active",
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    lot = Lot(
        seller_id=seller.id,
        product_id=1,
        title="Test Lot",
        price=Decimal("100.00"),
        status="active"
    )
    db_session.add(lot)
    await db_session.flush()
    
    deal = Deal(
        order_id=1,
        buyer_id=buyer.id,
        seller_id=seller.id,
        lot_id=lot.id,
        status=DealStatus.WAITING_CONFIRMATION,
        amount=Decimal("100.00"),
        commission_amount=Decimal("10.00"),
        seller_amount=Decimal("90.00")
    )
    db_session.add(deal)
    await db_session.flush()
    
    # Open dispute
    dispute = DealDispute(
        deal_id=deal.id,
        initiator_id=buyer.id,
        reason="Product not received",
        status=DisputeStatus.OPEN
    )
    db_session.add(dispute)
    await db_session.flush()
    
    # Create notification for admin
    notification = Notification(
        user_id=admin_user.id,
        notification_type=NotificationType.DISPUTE_OPENED,
        title="New Dispute Opened",
        message=f"A dispute has been opened for deal #{deal.id}. Reason: Product not received",
        reference_type="dispute",
        reference_id=dispute.id
    )
    db_session.add(notification)
    await db_session.commit()
    
    # Verify notification was created
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == admin_user.id,
            Notification.notification_type == NotificationType.DISPUTE_OPENED
        )
    )
    created_notification = result.scalar_one()
    
    assert created_notification.title == "New Dispute Opened"
    assert "Product not received" in created_notification.message
    assert created_notification.reference_type == "dispute"
    assert created_notification.reference_id == dispute.id


@pytest.mark.asyncio
async def test_resolve_dispute_release_to_seller(db_session: AsyncSession):
    """Test Requirements 10.5, 10.6, 10.8: Resolve dispute with release to seller."""
    # Create test data
    buyer = User(telegram_id=123456, username="buyer", balance=Decimal("1000.00"))
    seller_user = User(telegram_id=789012, username="seller", balance=Decimal("0.00"))
    db_session.add_all([buyer, seller_user])
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        shop_name="Test Shop",
        status="active",
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    lot = Lot(
        seller_id=seller.id,
        product_id=1,
        title="Test Lot",
        price=Decimal("100.00"),
        status="active"
    )
    db_session.add(lot)
    await db_session.flush()
    
    deal = Deal(
        order_id=1,
        buyer_id=buyer.id,
        seller_id=seller.id,
        lot_id=lot.id,
        status=DealStatus.DISPUTE,
        amount=Decimal("100.00"),
        commission_amount=Decimal("10.00"),
        seller_amount=Decimal("90.00"),
        escrow_released=False
    )
    db_session.add(deal)
    await db_session.flush()
    
    dispute = DealDispute(
        deal_id=deal.id,
        initiator_id=buyer.id,
        reason="Product not received",
        status=DisputeStatus.OPEN
    )
    db_session.add(dispute)
    await db_session.flush()
    
    # Create admin
    admin_user = User(telegram_id=999999, username="admin", balance=Decimal("0.00"))
    db_session.add(admin_user)
    await db_session.flush()
    
    admin = Admin(
        user_id=admin_user.id,
        role="super_admin",
        is_active=True
    )
    db_session.add(admin)
    await db_session.flush()
    
    # Resolve dispute - release to seller
    old_balance = seller_user.balance
    seller_user.balance += deal.seller_amount
    
    # Create transaction
    transaction = Transaction(
        user_id=seller_user.id,
        transaction_type=TransactionType.SALE,
        amount=deal.seller_amount,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=old_balance,
        balance_after=seller_user.balance,
        description=f"Payment for deal #{deal.id}",
        reference_type="deal",
        reference_id=deal.id
    )
    db_session.add(transaction)
    
    # Update dispute
    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution = "release_to_seller"
    dispute.admin_comment = "Seller provided proof of delivery"
    dispute.resolved_at = datetime.utcnow()
    dispute.resolved_by_id = admin.id
    
    # Update deal
    deal.status = DealStatus.COMPLETED
    deal.completed_at = datetime.utcnow()
    deal.escrow_released = True
    deal.escrow_released_at = datetime.utcnow()
    
    await db_session.commit()
    
    # Verify resolution
    result = await db_session.execute(
        select(DealDispute).where(DealDispute.id == dispute.id)
    )
    resolved_dispute = result.scalar_one()
    
    assert resolved_dispute.status == DisputeStatus.RESOLVED
    assert resolved_dispute.resolution == "release_to_seller"
    assert resolved_dispute.admin_comment == "Seller provided proof of delivery"
    assert resolved_dispute.resolved_at is not None
    assert resolved_dispute.resolved_by_id == admin.id
    
    # Verify seller received funds
    result = await db_session.execute(
        select(User).where(User.id == seller_user.id)
    )
    updated_seller_user = result.scalar_one()
    assert updated_seller_user.balance == Decimal("90.00")
    
    # Verify deal is completed
    result = await db_session.execute(
        select(Deal).where(Deal.id == deal.id)
    )
    updated_deal = result.scalar_one()
    assert updated_deal.status == DealStatus.COMPLETED
    assert updated_deal.escrow_released is True


@pytest.mark.asyncio
async def test_resolve_dispute_refund_to_buyer(db_session: AsyncSession):
    """Test Requirements 10.5, 10.7, 10.8: Resolve dispute with refund to buyer."""
    # Create test data
    buyer = User(telegram_id=123456, username="buyer", balance=Decimal("900.00"))
    seller_user = User(telegram_id=789012, username="seller", balance=Decimal("0.00"))
    db_session.add_all([buyer, seller_user])
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        shop_name="Test Shop",
        status="active",
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    lot = Lot(
        seller_id=seller.id,
        product_id=1,
        title="Test Lot",
        price=Decimal("100.00"),
        status="active"
    )
    db_session.add(lot)
    await db_session.flush()
    
    deal = Deal(
        order_id=1,
        buyer_id=buyer.id,
        seller_id=seller.id,
        lot_id=lot.id,
        status=DealStatus.DISPUTE,
        amount=Decimal("100.00"),
        commission_amount=Decimal("10.00"),
        seller_amount=Decimal("90.00"),
        escrow_released=False
    )
    db_session.add(deal)
    await db_session.flush()
    
    dispute = DealDispute(
        deal_id=deal.id,
        initiator_id=buyer.id,
        reason="Product not received",
        status=DisputeStatus.OPEN
    )
    db_session.add(dispute)
    await db_session.flush()
    
    # Create admin
    admin_user = User(telegram_id=999999, username="admin", balance=Decimal("0.00"))
    db_session.add(admin_user)
    await db_session.flush()
    
    admin = Admin(
        user_id=admin_user.id,
        role="super_admin",
        is_active=True
    )
    db_session.add(admin)
    await db_session.flush()
    
    # Resolve dispute - refund to buyer
    old_balance = buyer.balance
    buyer.balance += deal.amount
    
    # Create transaction
    transaction = Transaction(
        user_id=buyer.id,
        transaction_type=TransactionType.REFUND,
        amount=deal.amount,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=old_balance,
        balance_after=buyer.balance,
        description=f"Refund for deal #{deal.id}",
        reference_type="deal",
        reference_id=deal.id
    )
    db_session.add(transaction)
    
    # Update dispute
    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution = "refund_to_buyer"
    dispute.admin_comment = "Seller failed to deliver"
    dispute.resolved_at = datetime.utcnow()
    dispute.resolved_by_id = admin.id
    
    # Update deal
    deal.status = DealStatus.REFUNDED
    
    await db_session.commit()
    
    # Verify resolution
    result = await db_session.execute(
        select(DealDispute).where(DealDispute.id == dispute.id)
    )
    resolved_dispute = result.scalar_one()
    
    assert resolved_dispute.status == DisputeStatus.RESOLVED
    assert resolved_dispute.resolution == "refund_to_buyer"
    assert resolved_dispute.admin_comment == "Seller failed to deliver"
    
    # Verify buyer received refund
    result = await db_session.execute(
        select(User).where(User.id == buyer.id)
    )
    updated_buyer = result.scalar_one()
    assert updated_buyer.balance == Decimal("1000.00")
    
    # Verify deal is refunded
    result = await db_session.execute(
        select(Deal).where(Deal.id == deal.id)
    )
    updated_deal = result.scalar_one()
    assert updated_deal.status == DealStatus.REFUNDED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
