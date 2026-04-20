"""Test withdrawal system implementation.

Tests for Task 12.1: Withdrawal System
- POST /api/v1/sellers/me/withdrawals endpoint
- Validate sufficient balance
- Deduct amount and create pending withdrawal
- Admin processing endpoints
- Refund if withdrawal fails
"""
import pytest
import pytest_asyncio
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, Seller, SellerWithdrawal, Transaction, Admin
from app.models.enums import TransactionType, TransactionStatus, WithdrawalStatus, AdminRole


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create test user."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        balance=Decimal("0.00")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession, test_user: User):
    """Create test admin."""
    admin = Admin(
        user_id=test_user.id,
        role=AdminRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_seller(db_session: AsyncSession, test_user: User):
    """Create test seller."""
    seller = Seller(
        user_id=test_user.id,
        shop_name="Test Shop",
        status="active",
        balance=Decimal("0.00"),
        rating=Decimal("0.00"),
        total_sales=0
    )
    db_session.add(seller)
    await db_session.commit()
    await db_session.refresh(seller)
    return seller


@pytest_asyncio.fixture
async def test_withdrawal(db_session: AsyncSession, test_user: User, test_seller: Seller):
    """Create test withdrawal."""
    # Set seller balance and deduct withdrawal amount
    test_seller.balance = Decimal("500.00")
    
    withdrawal = SellerWithdrawal(
        seller_id=test_seller.id,
        amount=Decimal("300.00"),
        payment_method="card",
        payment_details="1234 5678 9012 3456",
        status=WithdrawalStatus.PENDING
    )
    db_session.add(withdrawal)
    await db_session.flush()
    
    # Create associated transaction
    transaction = Transaction(
        user_id=test_user.id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount=Decimal("-300.00"),
        currency_code="RUB",
        status=TransactionStatus.PENDING,
        balance_before=Decimal("800.00"),
        balance_after=Decimal("500.00"),
        description=f"Withdrawal request #{withdrawal.id}",
        reference_type="withdrawal",
        reference_id=withdrawal.id
    )
    db_session.add(transaction)
    
    await db_session.commit()
    await db_session.refresh(withdrawal)
    return withdrawal


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession, test_user: User):
    """Create async HTTP client with mocked authentication."""
    from api.main import app
    from api.dependencies.auth import get_current_user
    
    # Mock authentication to return test_user
    async def mock_get_current_user():
        return test_user
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_withdrawal_request_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    test_seller: Seller
):
    """Test successful withdrawal request.
    
    Requirements: 13.1, 13.2, 13.3, 13.7
    """
    # Set seller balance
    test_seller.balance = Decimal("1000.00")
    await db_session.commit()
    
    # Request withdrawal
    response = await async_client.post(
        "/api/v1/sellers/me/withdrawals",
        json={
            "amount": 500.00,
            "payment_method": "card",
            "payment_details": "1234 5678 9012 3456"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response
    assert data["amount"] == 500.00
    assert data["status"] == "pending"
    assert "withdrawal_id" in data
    assert "transaction_id" in data
    
    # Verify withdrawal record created
    result = await db_session.execute(
        select(SellerWithdrawal).where(SellerWithdrawal.id == data["withdrawal_id"])
    )
    withdrawal = result.scalar_one()
    
    assert withdrawal.seller_id == test_seller.id
    assert withdrawal.amount == Decimal("500.00")
    assert withdrawal.payment_method == "card"
    assert withdrawal.status == WithdrawalStatus.PENDING
    
    # Verify balance deducted (Requirement 13.3)
    await db_session.refresh(test_seller)
    assert test_seller.balance == Decimal("500.00")
    
    # Verify transaction record created (Requirement 13.7)
    result = await db_session.execute(
        select(Transaction).where(Transaction.id == data["transaction_id"])
    )
    transaction = result.scalar_one()
    
    assert transaction.user_id == test_user.id
    assert transaction.transaction_type == TransactionType.WITHDRAWAL
    assert transaction.amount == Decimal("-500.00")  # Negative for withdrawal
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.balance_before == Decimal("1000.00")
    assert transaction.balance_after == Decimal("500.00")
    assert transaction.reference_type == "withdrawal"
    assert transaction.reference_id == withdrawal.id


@pytest.mark.asyncio
async def test_withdrawal_insufficient_balance(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_seller: Seller
):
    """Test withdrawal request with insufficient balance.
    
    Requirements: 13.2
    """
    # Set low balance
    test_seller.balance = Decimal("50.00")
    await db_session.commit()
    
    # Request withdrawal exceeding balance
    response = await async_client.post(
        "/api/v1/sellers/me/withdrawals",
        json={
            "amount": 500.00,
            "payment_method": "card",
            "payment_details": "1234 5678 9012 3456"
        }
    )
    
    assert response.status_code == 400
    assert "Insufficient balance" in response.json()["detail"]


@pytest.mark.asyncio
async def test_withdrawal_minimum_amount(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_seller: Seller
):
    """Test withdrawal request below minimum amount.
    
    Requirements: 13.1
    """
    test_seller.balance = Decimal("1000.00")
    await db_session.commit()
    
    # Request withdrawal below minimum
    response = await async_client.post(
        "/api/v1/sellers/me/withdrawals",
        json={
            "amount": 50.00,  # Below 100 RUB minimum
            "payment_method": "card",
            "payment_details": "1234 5678 9012 3456"
        }
    )
    
    assert response.status_code == 400
    assert "Minimum withdrawal amount" in response.json()["detail"]


@pytest.mark.asyncio
async def test_admin_approve_withdrawal(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_seller: Seller,
    test_withdrawal: SellerWithdrawal
):
    """Test admin approving withdrawal.
    
    Requirements: 13.4
    """
    # Approve withdrawal
    response = await async_client.post(
        f"/api/v1/admin/withdrawals/{test_withdrawal.id}/approve"
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Withdrawal approved"
    
    # Verify withdrawal status updated
    await db_session.refresh(test_withdrawal)
    assert test_withdrawal.status == WithdrawalStatus.COMPLETED
    assert test_withdrawal.processed_at is not None
    
    # Verify transaction status updated
    result = await db_session.execute(
        select(Transaction).where(
            Transaction.reference_type == "withdrawal",
            Transaction.reference_id == test_withdrawal.id,
            Transaction.transaction_type == TransactionType.WITHDRAWAL
        )
    )
    transaction = result.scalar_one()
    assert transaction.status == TransactionStatus.COMPLETED


@pytest.mark.asyncio
async def test_admin_reject_withdrawal_with_refund(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    test_seller: Seller,
    test_withdrawal: SellerWithdrawal
):
    """Test admin rejecting withdrawal with refund.
    
    Requirements: 13.4, 13.5
    """
    # Record initial balance
    initial_balance = test_seller.balance
    withdrawal_amount = test_withdrawal.amount
    
    # Reject withdrawal
    response = await async_client.post(
        f"/api/v1/admin/withdrawals/{test_withdrawal.id}/reject",
        params={"rejection_reason": "Invalid payment details"}
    )
    
    assert response.status_code == 200
    assert "funds returned" in response.json()["message"]
    
    # Verify withdrawal status updated
    await db_session.refresh(test_withdrawal)
    assert test_withdrawal.status == WithdrawalStatus.REJECTED
    assert test_withdrawal.processed_at is not None
    assert test_withdrawal.rejection_reason == "Invalid payment details"
    
    # Verify balance refunded (Requirement 13.5)
    await db_session.refresh(test_seller)
    assert test_seller.balance == initial_balance + withdrawal_amount
    
    # Verify original transaction marked as failed
    result = await db_session.execute(
        select(Transaction).where(
            Transaction.reference_type == "withdrawal",
            Transaction.reference_id == test_withdrawal.id,
            Transaction.transaction_type == TransactionType.WITHDRAWAL
        )
    )
    original_transaction = result.scalar_one()
    assert original_transaction.status == TransactionStatus.FAILED
    
    # Verify refund transaction created
    result = await db_session.execute(
        select(Transaction).where(
            Transaction.reference_type == "withdrawal",
            Transaction.reference_id == test_withdrawal.id,
            Transaction.transaction_type == TransactionType.REFUND
        )
    )
    refund_transaction = result.scalar_one()
    
    assert refund_transaction.user_id == test_user.id
    assert refund_transaction.amount == withdrawal_amount  # Positive for refund
    assert refund_transaction.status == TransactionStatus.COMPLETED


@pytest.mark.asyncio
async def test_get_seller_balance_breakdown(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_seller: Seller
):
    """Test getting seller balance breakdown.
    
    Requirements: 13.6
    """
    # Set seller balance
    test_seller.balance = Decimal("1000.00")
    await db_session.commit()
    
    # Create pending withdrawal
    withdrawal = SellerWithdrawal(
        seller_id=test_seller.id,
        amount=Decimal("200.00"),
        payment_method="card",
        payment_details="1234",
        status=WithdrawalStatus.PENDING
    )
    db_session.add(withdrawal)
    await db_session.commit()
    
    # Get balance breakdown
    response = await async_client.get("/api/v1/sellers/me/balance")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify balance breakdown (Requirement 13.6)
    assert data["available_balance"] == 1000.00
    assert data["pending_withdrawals"] == 200.00
    assert "in_escrow" in data
    assert data["currency"] == "RUB"


@pytest.mark.asyncio
async def test_get_withdrawal_history(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_seller: Seller
):
    """Test getting withdrawal history."""
    # Create multiple withdrawals
    for i in range(3):
        withdrawal = SellerWithdrawal(
            seller_id=test_seller.id,
            amount=Decimal(f"{(i+1)*100}.00"),
            payment_method="card",
            payment_details=f"Card {i+1}",
            status=WithdrawalStatus.PENDING if i == 0 else WithdrawalStatus.COMPLETED
        )
        db_session.add(withdrawal)
    
    await db_session.commit()
    
    # Get withdrawal history
    response = await async_client.get("/api/v1/sellers/me/withdrawals")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 3
    assert data["items"][0]["amount"] == 300.00  # Most recent first
    assert data["items"][1]["amount"] == 200.00
    assert data["items"][2]["amount"] == 100.00


@pytest.mark.asyncio
async def test_withdrawal_not_seller(
    async_client: AsyncClient,
    db_session: AsyncSession
):
    """Test withdrawal request from non-seller user."""
    response = await async_client.post(
        "/api/v1/sellers/me/withdrawals",
        json={
            "amount": 500.00,
            "payment_method": "card",
            "payment_details": "1234 5678 9012 3456"
        }
    )
    
    assert response.status_code == 404
    assert "Not a seller" in response.json()["detail"]


@pytest.mark.asyncio
async def test_admin_approve_non_pending_withdrawal(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_withdrawal: SellerWithdrawal
):
    """Test admin cannot approve non-pending withdrawal."""
    # Mark withdrawal as completed
    test_withdrawal.status = WithdrawalStatus.COMPLETED
    await db_session.commit()
    
    # Try to approve again
    response = await async_client.post(
        f"/api/v1/admin/withdrawals/{test_withdrawal.id}/approve"
    )
    
    assert response.status_code == 400
    assert "not pending" in response.json()["detail"]
