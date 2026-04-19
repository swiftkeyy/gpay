"""Test script to verify referral tracking functionality.

This script tests the AuthService implementation for requirements:
- 1.4: Create user with zero balance
- 1.8: Associate new user with referrer if referral code provided
- 14.1: Generate unique 8-12 character referral code
- 14.2: Associate new user with referrer
- 14.6: Ensure referral code is unique across all users

Run with: python -m pytest test_referral_tracking.py -v
"""
import asyncio
import hashlib
import hmac
import json
from decimal import Decimal
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.services.auth import AuthService
from app.models import Base, Referral, User


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


def create_test_init_data(bot_token: str, user_data: dict) -> str:
    """Create a valid initData string for testing."""
    data = {
        "user": json.dumps(user_data),
        "auth_date": "1234567890",
        "query_id": "test_query_id"
    }
    
    data_check_arr = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(data_check_arr)
    
    secret_key = hmac.new(
        "WebAppData".encode(),
        bot_token.encode(),
        hashlib.sha256
    ).digest()
    
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    data["hash"] = calculated_hash
    return urlencode(data)


@pytest.mark.asyncio
async def test_create_user_with_zero_balance(db_session: AsyncSession):
    """Test that new user is created with zero balance (Req 1.4)."""
    print("\n=== Testing User Creation with Zero Balance (Req 1.4) ===")
    
    bot_token = "test_bot_token_12345"
    user_data = {
        "id": 123456789,
        "username": "testuser",
        "first_name": "Test"
    }
    
    init_data = create_test_init_data(bot_token, user_data)
    
    auth_service = AuthService(db_session, bot_token)
    user, is_new = await auth_service.authenticate_user(init_data)
    
    assert is_new is True, "User should be marked as new"
    assert user.balance == Decimal("0.00"), f"Balance should be 0.00, got {user.balance}"
    assert user.telegram_id == 123456789
    assert user.username == "testuser"
    
    print(f"✓ User created with zero balance: {user.balance}")


@pytest.mark.asyncio
async def test_generate_unique_referral_code(db_session: AsyncSession):
    """Test that each user gets a unique referral code (Req 14.1, 14.6)."""
    print("\n=== Testing Unique Referral Code Generation (Req 14.1, 14.6) ===")
    
    bot_token = "test_bot_token_12345"
    
    # Create multiple users
    referral_codes = []
    for i in range(5):
        user_data = {
            "id": 100000000 + i,
            "username": f"user{i}",
            "first_name": f"User{i}"
        }
        
        init_data = create_test_init_data(bot_token, user_data)
        auth_service = AuthService(db_session, bot_token)
        user, _ = await auth_service.authenticate_user(init_data)
        
        # Check referral code properties
        assert user.referral_code is not None, "Referral code should not be None"
        assert 8 <= len(user.referral_code) <= 12, \
            f"Referral code length should be 8-12 chars, got {len(user.referral_code)}"
        assert user.referral_code.replace("-", "").replace("_", "").isalnum(), \
            "Referral code should be alphanumeric (with possible - or _)"
        
        referral_codes.append(user.referral_code)
        print(f"  User {i}: {user.referral_code} (length: {len(user.referral_code)})")
    
    # Check all codes are unique
    assert len(referral_codes) == len(set(referral_codes)), \
        "All referral codes should be unique"
    
    print(f"✓ All {len(referral_codes)} referral codes are unique")


@pytest.mark.asyncio
async def test_referral_tracking_with_valid_code(db_session: AsyncSession):
    """Test that new user is associated with referrer (Req 1.8, 14.2)."""
    print("\n=== Testing Referral Tracking with Valid Code (Req 1.8, 14.2) ===")
    
    bot_token = "test_bot_token_12345"
    
    # Create referrer user
    referrer_data = {
        "id": 111111111,
        "username": "referrer",
        "first_name": "Referrer"
    }
    init_data_referrer = create_test_init_data(bot_token, referrer_data)
    auth_service = AuthService(db_session, bot_token)
    referrer, _ = await auth_service.authenticate_user(init_data_referrer)
    
    print(f"  Referrer created: {referrer.username} (code: {referrer.referral_code})")
    
    # Create referred user with referral code
    referred_data = {
        "id": 222222222,
        "username": "referred",
        "first_name": "Referred"
    }
    init_data_referred = create_test_init_data(bot_token, referred_data)
    auth_service = AuthService(db_session, bot_token)
    referred, is_new = await auth_service.authenticate_user(
        init_data_referred,
        referral_code=referrer.referral_code
    )
    
    assert is_new is True, "Referred user should be new"
    assert referred.referred_by_user_id == referrer.id, \
        f"Referred user should be linked to referrer, got {referred.referred_by_user_id}"
    
    print(f"  Referred user created: {referred.username}")
    print(f"  ✓ Referred user linked to referrer (ID: {referrer.id})")
    
    # Check Referral record was created
    stmt = select(Referral).where(Referral.referred_user_id == referred.id)
    referral_record = await db_session.scalar(stmt)
    
    assert referral_record is not None, "Referral record should be created"
    assert referral_record.referrer_user_id == referrer.id
    assert referral_record.referred_user_id == referred.id
    assert referral_record.referral_code == referrer.referral_code
    
    print(f"  ✓ Referral record created in database")


@pytest.mark.asyncio
async def test_referral_tracking_with_invalid_code(db_session: AsyncSession):
    """Test that invalid referral code doesn't break user creation."""
    print("\n=== Testing Referral Tracking with Invalid Code ===")
    
    bot_token = "test_bot_token_12345"
    
    # Create user with invalid referral code
    user_data = {
        "id": 333333333,
        "username": "newuser",
        "first_name": "NewUser"
    }
    init_data = create_test_init_data(bot_token, user_data)
    auth_service = AuthService(db_session, bot_token)
    user, is_new = await auth_service.authenticate_user(
        init_data,
        referral_code="INVALID_CODE_12345"
    )
    
    assert is_new is True, "User should be created"
    assert user.referred_by_user_id is None, \
        "User should not be linked to any referrer with invalid code"
    
    print(f"  ✓ User created without referrer link (invalid code ignored)")
    
    # Check no Referral record was created
    stmt = select(Referral).where(Referral.referred_user_id == user.id)
    referral_record = await db_session.scalar(stmt)
    
    assert referral_record is None, "No referral record should be created for invalid code"
    print(f"  ✓ No referral record created for invalid code")


@pytest.mark.asyncio
async def test_referral_tracking_without_code(db_session: AsyncSession):
    """Test that user can be created without referral code."""
    print("\n=== Testing User Creation Without Referral Code ===")
    
    bot_token = "test_bot_token_12345"
    
    # Create user without referral code
    user_data = {
        "id": 444444444,
        "username": "normaluser",
        "first_name": "NormalUser"
    }
    init_data = create_test_init_data(bot_token, user_data)
    auth_service = AuthService(db_session, bot_token)
    user, is_new = await auth_service.authenticate_user(init_data)
    
    assert is_new is True, "User should be created"
    assert user.referred_by_user_id is None, "User should not have referrer"
    assert user.referral_code is not None, "User should have their own referral code"
    
    print(f"  ✓ User created without referrer")
    print(f"  ✓ User has own referral code: {user.referral_code}")
    
    # Check no Referral record was created
    stmt = select(Referral).where(Referral.referred_user_id == user.id)
    referral_record = await db_session.scalar(stmt)
    
    assert referral_record is None, "No referral record should be created without code"


@pytest.mark.asyncio
async def test_existing_user_not_affected_by_referral_code(db_session: AsyncSession):
    """Test that existing user login is not affected by referral code."""
    print("\n=== Testing Existing User Login with Referral Code ===")
    
    bot_token = "test_bot_token_12345"
    
    # Create user first time
    user_data = {
        "id": 555555555,
        "username": "existinguser",
        "first_name": "ExistingUser"
    }
    init_data = create_test_init_data(bot_token, user_data)
    auth_service = AuthService(db_session, bot_token)
    user_first, is_new_first = await auth_service.authenticate_user(init_data)
    
    assert is_new_first is True
    original_referrer_id = user_first.referred_by_user_id
    
    # Try to login again with a referral code
    auth_service = AuthService(db_session, bot_token)
    user_second, is_new_second = await auth_service.authenticate_user(
        init_data,
        referral_code="SOME_CODE"
    )
    
    assert is_new_second is False, "User should not be marked as new"
    assert user_second.id == user_first.id, "Should be the same user"
    assert user_second.referred_by_user_id == original_referrer_id, \
        "Referrer should not change on subsequent logins"
    
    print(f"  ✓ Existing user login not affected by referral code")


@pytest.mark.asyncio
async def test_multiple_users_can_be_referred_by_same_referrer(db_session: AsyncSession):
    """Test that one referrer can refer multiple users."""
    print("\n=== Testing Multiple Referrals from Same Referrer ===")
    
    bot_token = "test_bot_token_12345"
    
    # Create referrer
    referrer_data = {
        "id": 666666666,
        "username": "superreferrer",
        "first_name": "SuperReferrer"
    }
    init_data_referrer = create_test_init_data(bot_token, referrer_data)
    auth_service = AuthService(db_session, bot_token)
    referrer, _ = await auth_service.authenticate_user(init_data_referrer)
    
    # Create multiple referred users
    referred_users = []
    for i in range(3):
        user_data = {
            "id": 700000000 + i,
            "username": f"referred{i}",
            "first_name": f"Referred{i}"
        }
        init_data = create_test_init_data(bot_token, user_data)
        auth_service = AuthService(db_session, bot_token)
        user, _ = await auth_service.authenticate_user(
            init_data,
            referral_code=referrer.referral_code
        )
        referred_users.append(user)
    
    # Verify all users are linked to the same referrer
    for i, user in enumerate(referred_users):
        assert user.referred_by_user_id == referrer.id, \
            f"User {i} should be linked to referrer"
        print(f"  ✓ User {i} ({user.username}) linked to referrer")
    
    # Check Referral records
    stmt = select(Referral).where(Referral.referrer_user_id == referrer.id)
    result = await db_session.execute(stmt)
    referral_records = result.scalars().all()
    
    assert len(referral_records) == 3, "Should have 3 referral records"
    print(f"  ✓ All {len(referral_records)} referral records created")


if __name__ == "__main__":
    print("=" * 70)
    print("REFERRAL TRACKING TESTS")
    print("Testing Requirements: 1.4, 1.8, 14.1, 14.2, 14.6")
    print("=" * 70)
    
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
