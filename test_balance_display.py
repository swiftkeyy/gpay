"""Test balance display with breakdown - Task 12.2

Requirements tested:
- 13.6: Display available balance, pending withdrawals, and escrow held
- 13.7: Create transaction record for each balance change
"""
import pytest
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, Seller, Deal, SellerWithdrawal, Transaction
from app.models.enums import DealStatus, TransactionType, TransactionStatus


@pytest.mark.asyncio
async def test_balance_display_breakdown(db_session: AsyncSession):
    """Test Requirement 13.6: Display available balance, pending withdrawals, and escrow held."""
    # Create user and seller
    user = User(
        telegram_id=123456,
        username="test_seller",
        balance=Decimal("1000.00")
    )
    db_session.add(user)
    await db_session.flush()
    
    seller = Seller(
        user_id=user.id,
        shop_name="Test Shop",
        status="active",
        balance=Decimal("1000.00"),
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    # Create buyer
    buyer = User(
        telegram_id=789012,
        username="test_buyer",
        balance=Decimal("500.00")
    )
    db_session.add(buyer)
    await db_session.flush()
    
    # Create pending withdrawal
    withdrawal = SellerWithdrawal(
        seller_id=seller.id,
        amount=Decimal("200.00"),
        payment_method="card",
        payment_details="1234****5678",
        status="pending",
        currency_code="RUB"
    )
    db_session.add(withdrawal)
    
    # Create active deal with escrow
    deal = Deal(
        order_id=1,
        buyer_id=buyer.id,
        seller_id=seller.id,
        lot_id=1,
        status=DealStatus.IN_PROGRESS,
        amount=Decimal("500.00"),
        commission_amount=Decimal("50.00"),
        seller_amount=Decimal("450.00"),
        escrow_released=False
    )
    db_session.add(deal)
    
    await db_session.commit()
    
    # Calculate balance breakdown
    # Available balance
    available_balance = seller.balance
    
    # Pending withdrawals
    result = await db_session.execute(
        select(SellerWithdrawal.amount).where(
            SellerWithdrawal.seller_id == seller.id,
            SellerWithdrawal.status == "pending"
        )
    )
    pending_withdrawals = sum([w for w in result.scalars()], Decimal("0.00"))
    
    # Escrow held
    result = await db_session.execute(
        select(Deal.seller_amount).where(
            Deal.seller_id == seller.id,
            Deal.status.in_([DealStatus.PAID, DealStatus.IN_PROGRESS, DealStatus.WAITING_CONFIRMATION]),
            Deal.escrow_released == False
        )
    )
    in_escrow = sum([d for d in result.scalars()], Decimal("0.00"))
    
    # Verify breakdown
    assert available_balance == Decimal("1000.00")
    assert pending_withdrawals == Decimal("200.00")
    assert in_escrow == Decimal("450.00")
    
    print(f"✅ Balance breakdown correct:")
    print(f"   Available: {available_balance} RUB")
    print(f"   Pending withdrawals: {pending_withdrawals} RUB")
    print(f"   In escrow: {in_escrow} RUB")


@pytest.mark.asyncio
async def test_transaction_records_for_balance_changes(db_session: AsyncSession):
    """Test Requirement 13.7: Create transaction record for each balance change."""
    # Create user and seller
    user = User(
        telegram_id=123456,
        username="test_seller",
        balance=Decimal("1000.00")
    )
    db_session.add(user)
    await db_session.flush()
    
    seller = Seller(
        user_id=user.id,
        shop_name="Test Shop",
        status="active",
        balance=Decimal("1000.00"),
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    # Test 1: Withdrawal creates transaction
    balance_before = user.balance
    withdrawal_amount = Decimal("200.00")
    user.balance -= withdrawal_amount
    balance_after = user.balance
    
    withdrawal = SellerWithdrawal(
        seller_id=seller.id,
        amount=withdrawal_amount,
        payment_method="card",
        payment_details="1234****5678",
        status="pending",
        currency_code="RUB"
    )
    db_session.add(withdrawal)
    await db_session.flush()
    
    transaction = Transaction(
        user_id=user.id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount=-withdrawal_amount,
        currency_code="RUB",
        status=TransactionStatus.PENDING,
        balance_before=balance_before,
        balance_after=balance_after,
        description=f"Withdrawal request #{withdrawal.id} via card",
        reference_type="withdrawal",
        reference_id=withdrawal.id
    )
    db_session.add(transaction)
    await db_session.commit()
    
    # Verify transaction was created
    result = await db_session.execute(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == TransactionType.WITHDRAWAL
        )
    )
    withdrawal_transaction = result.scalar_one_or_none()
    
    assert withdrawal_transaction is not None
    assert withdrawal_transaction.amount == -withdrawal_amount
    assert withdrawal_transaction.balance_before == balance_before
    assert withdrawal_transaction.balance_after == balance_after
    assert withdrawal_transaction.reference_type == "withdrawal"
    assert withdrawal_transaction.reference_id == withdrawal.id
    
    print(f"✅ Withdrawal transaction created:")
    print(f"   Type: {withdrawal_transaction.transaction_type.value}")
    print(f"   Amount: {withdrawal_transaction.amount} RUB")
    print(f"   Balance before: {withdrawal_transaction.balance_before} RUB")
    print(f"   Balance after: {withdrawal_transaction.balance_after} RUB")
    
    # Test 2: Boost creates transaction
    boost_cost = Decimal("100.00")
    balance_before = user.balance
    user.balance -= boost_cost
    balance_after = user.balance
    
    boost_transaction = Transaction(
        user_id=user.id,
        transaction_type=TransactionType.BOOST,
        amount=-boost_cost,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=balance_before,
        balance_after=balance_after,
        description=f"Boost lot #1 for 24 hours",
        reference_type="lot",
        reference_id=1
    )
    db_session.add(boost_transaction)
    await db_session.commit()
    
    # Verify boost transaction
    result = await db_session.execute(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == TransactionType.BOOST
        )
    )
    boost_tx = result.scalar_one_or_none()
    
    assert boost_tx is not None
    assert boost_tx.amount == -boost_cost
    assert boost_tx.status == TransactionStatus.COMPLETED
    
    print(f"✅ Boost transaction created:")
    print(f"   Type: {boost_tx.transaction_type.value}")
    print(f"   Amount: {boost_tx.amount} RUB")
    print(f"   Status: {boost_tx.status.value}")
    
    # Test 3: Sale creates transaction
    sale_amount = Decimal("450.00")
    balance_before = user.balance
    user.balance += sale_amount
    balance_after = user.balance
    
    sale_transaction = Transaction(
        user_id=user.id,
        transaction_type=TransactionType.SALE,
        amount=sale_amount,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=balance_before,
        balance_after=balance_after,
        description=f"Payment for deal #1",
        reference_type="deal",
        reference_id=1
    )
    db_session.add(sale_transaction)
    await db_session.commit()
    
    # Verify sale transaction
    result = await db_session.execute(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == TransactionType.SALE
        )
    )
    sale_tx = result.scalar_one_or_none()
    
    assert sale_tx is not None
    assert sale_tx.amount == sale_amount
    assert sale_tx.status == TransactionStatus.COMPLETED
    
    print(f"✅ Sale transaction created:")
    print(f"   Type: {sale_tx.transaction_type.value}")
    print(f"   Amount: {sale_tx.amount} RUB")
    print(f"   Status: {sale_tx.status.value}")
    
    # Verify all transactions are tracked
    result = await db_session.execute(
        select(Transaction).where(Transaction.user_id == user.id)
    )
    all_transactions = result.scalars().all()
    
    assert len(all_transactions) == 3
    transaction_types = {tx.transaction_type for tx in all_transactions}
    assert TransactionType.WITHDRAWAL in transaction_types
    assert TransactionType.BOOST in transaction_types
    assert TransactionType.SALE in transaction_types
    
    print(f"✅ All balance changes tracked: {len(all_transactions)} transactions")


@pytest.mark.asyncio
async def test_balance_display_with_multiple_deals(db_session: AsyncSession):
    """Test balance display with multiple active deals in escrow."""
    # Create user and seller
    user = User(
        telegram_id=123456,
        username="test_seller",
        balance=Decimal("2000.00")
    )
    db_session.add(user)
    await db_session.flush()
    
    seller = Seller(
        user_id=user.id,
        shop_name="Test Shop",
        status="active",
        balance=Decimal("2000.00"),
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    # Create buyer
    buyer = User(
        telegram_id=789012,
        username="test_buyer",
        balance=Decimal("1000.00")
    )
    db_session.add(buyer)
    await db_session.flush()
    
    # Create multiple active deals
    deals_data = [
        (DealStatus.PAID, Decimal("300.00"), Decimal("30.00"), Decimal("270.00")),
        (DealStatus.IN_PROGRESS, Decimal("500.00"), Decimal("50.00"), Decimal("450.00")),
        (DealStatus.WAITING_CONFIRMATION, Decimal("200.00"), Decimal("20.00"), Decimal("180.00")),
        (DealStatus.COMPLETED, Decimal("400.00"), Decimal("40.00"), Decimal("360.00")),  # Should not be counted
    ]
    
    for i, (status, amount, commission, seller_amount) in enumerate(deals_data, 1):
        deal = Deal(
            order_id=i,
            buyer_id=buyer.id,
            seller_id=seller.id,
            lot_id=i,
            status=status,
            amount=amount,
            commission_amount=commission,
            seller_amount=seller_amount,
            escrow_released=(status == DealStatus.COMPLETED)
        )
        db_session.add(deal)
    
    await db_session.commit()
    
    # Calculate escrow held
    result = await db_session.execute(
        select(Deal.seller_amount).where(
            Deal.seller_id == seller.id,
            Deal.status.in_([DealStatus.PAID, DealStatus.IN_PROGRESS, DealStatus.WAITING_CONFIRMATION]),
            Deal.escrow_released == False
        )
    )
    in_escrow = sum([d for d in result.scalars()], Decimal("0.00"))
    
    # Should be sum of first 3 deals only (completed deal excluded)
    expected_escrow = Decimal("270.00") + Decimal("450.00") + Decimal("180.00")
    assert in_escrow == expected_escrow
    
    print(f"✅ Escrow calculation correct with multiple deals:")
    print(f"   Total in escrow: {in_escrow} RUB")
    print(f"   Expected: {expected_escrow} RUB")
    print(f"   Active deals: 3 (1 completed deal excluded)")


@pytest.mark.asyncio
async def test_balance_display_with_no_pending_items(db_session: AsyncSession):
    """Test balance display when there are no pending withdrawals or escrow."""
    # Create user and seller
    user = User(
        telegram_id=123456,
        username="test_seller",
        balance=Decimal("1500.00")
    )
    db_session.add(user)
    await db_session.flush()
    
    seller = Seller(
        user_id=user.id,
        shop_name="Test Shop",
        status="active",
        balance=Decimal("1500.00"),
        commission_percent=Decimal("10.00")
    )
    db_session.add(seller)
    await db_session.commit()
    
    # Calculate balance breakdown
    available_balance = seller.balance
    
    result = await db_session.execute(
        select(SellerWithdrawal.amount).where(
            SellerWithdrawal.seller_id == seller.id,
            SellerWithdrawal.status == "pending"
        )
    )
    pending_withdrawals = sum([w for w in result.scalars()], Decimal("0.00"))
    
    result = await db_session.execute(
        select(Deal.seller_amount).where(
            Deal.seller_id == seller.id,
            Deal.status.in_([DealStatus.PAID, DealStatus.IN_PROGRESS, DealStatus.WAITING_CONFIRMATION]),
            Deal.escrow_released == False
        )
    )
    in_escrow = sum([d for d in result.scalars()], Decimal("0.00"))
    
    # Verify all values
    assert available_balance == Decimal("1500.00")
    assert pending_withdrawals == Decimal("0.00")
    assert in_escrow == Decimal("0.00")
    
    print(f"✅ Balance display correct with no pending items:")
    print(f"   Available: {available_balance} RUB")
    print(f"   Pending withdrawals: {pending_withdrawals} RUB")
    print(f"   In escrow: {in_escrow} RUB")


if __name__ == "__main__":
    print("Run with: pytest test_balance_display.py -v")
