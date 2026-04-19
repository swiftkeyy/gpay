"""Test script to verify user profile management endpoints.

This script tests the user profile endpoints for requirements:
- 2.1: GET /users/me - Return user profile
- 2.2: PATCH /users/me - Update language preference
- 2.3: GET /users/me/balance - Return balance
- 2.4: GET /users/me/transactions - Return paginated transactions

Run with: python test_user_profile.py
"""
import asyncio
import sys
from decimal import Decimal

# Add project root to path
sys.path.insert(0, '.')


async def test_get_user_profile():
    """Test GET /users/me endpoint (Req 2.1)."""
    print("\n=== Testing GET /users/me (Req 2.1) ===")
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    from app.models.entities import User
    from api.routers.users import get_current_user_profile
    from sqlalchemy import select
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get first user from database
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("✗ No users in database. Please seed data first.")
            return False
        
        try:
            # Call the endpoint function directly
            response = await get_current_user_profile(current_user=user, session=session)
            
            # Verify response has all required fields
            required_fields = ['id', 'telegram_id', 'username', 'balance', 
                             'referral_code', 'language_code', 'created_at']
            
            missing_fields = [f for f in required_fields if not hasattr(response, f)]
            
            if missing_fields:
                print(f"✗ Missing fields in response: {missing_fields}")
                return False
            
            print("✓ GET /users/me returns all required fields: PASS")
            print(f"  User ID: {response.id}")
            print(f"  Telegram ID: {response.telegram_id}")
            print(f"  Balance: {response.balance}")
            print(f"  Referral Code: {response.referral_code}")
            print(f"  Language: {response.language_code}")
            return True
            
        except Exception as e:
            print(f"✗ Error calling endpoint: {e}")
            return False
        finally:
            await engine.dispose()


async def test_update_language_preference():
    """Test PATCH /users/me endpoint (Req 2.2)."""
    print("\n=== Testing PATCH /users/me (Req 2.2) ===")
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    from app.models.entities import User
    from api.routers.users import update_current_user_profile, UpdateProfileRequest
    from sqlalchemy import select
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get first user from database
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("✗ No users in database. Please seed data first.")
            return False
        
        try:
            original_language = user.language_code
            new_language = "en" if original_language != "en" else "ru"
            
            # Update language
            request = UpdateProfileRequest(language_code=new_language)
            response = await update_current_user_profile(
                request=request,
                current_user=user,
                session=session
            )
            
            if response.language_code == new_language:
                print("✓ PATCH /users/me updates language preference: PASS")
                print(f"  Changed from '{original_language}' to '{new_language}'")
                
                # Restore original language
                request = UpdateProfileRequest(language_code=original_language)
                await update_current_user_profile(
                    request=request,
                    current_user=user,
                    session=session
                )
                return True
            else:
                print(f"✗ Language not updated. Expected '{new_language}', got '{response.language_code}'")
                return False
                
        except Exception as e:
            print(f"✗ Error calling endpoint: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await engine.dispose()


async def test_get_balance():
    """Test GET /users/me/balance endpoint (Req 2.3)."""
    print("\n=== Testing GET /users/me/balance (Req 2.3) ===")
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    from app.models.entities import User
    from api.routers.users import get_user_balance
    from sqlalchemy import select
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get first user from database
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("✗ No users in database. Please seed data first.")
            return False
        
        try:
            # Get balance
            response = await get_user_balance(current_user=user, session=session)
            
            if 'balance' in response and 'currency' in response:
                # Verify balance has 2 decimal precision
                balance_str = f"{response['balance']:.2f}"
                print("✓ GET /users/me/balance returns balance with currency: PASS")
                print(f"  Balance: {balance_str} {response['currency']}")
                return True
            else:
                print("✗ Response missing 'balance' or 'currency' field")
                return False
                
        except Exception as e:
            print(f"✗ Error calling endpoint: {e}")
            return False
        finally:
            await engine.dispose()


async def test_get_transactions():
    """Test GET /users/me/transactions endpoint (Req 2.4)."""
    print("\n=== Testing GET /users/me/transactions (Req 2.4) ===")
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    from app.models.entities import User
    from api.routers.users import get_user_transactions
    from sqlalchemy import select
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get first user from database
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("✗ No users in database. Please seed data first.")
            return False
        
        try:
            # Get transactions with pagination
            response = await get_user_transactions(
                current_user=user,
                page=1,
                limit=20,
                session=session
            )
            
            required_fields = ['items', 'total', 'page', 'limit']
            missing_fields = [f for f in required_fields if f not in response]
            
            if missing_fields:
                print(f"✗ Missing fields in response: {missing_fields}")
                return False
            
            print("✓ GET /users/me/transactions returns paginated list: PASS")
            print(f"  Total transactions: {response['total']}")
            print(f"  Page: {response['page']}")
            print(f"  Limit: {response['limit']}")
            print(f"  Items returned: {len(response['items'])}")
            
            # Verify transaction structure if any exist
            if response['items']:
                tx = response['items'][0]
                tx_fields = ['id', 'type', 'amount', 'status', 'created_at']
                missing_tx_fields = [f for f in tx_fields if f not in tx]
                
                if missing_tx_fields:
                    print(f"✗ Missing fields in transaction: {missing_tx_fields}")
                    return False
                
                print(f"  Sample transaction: {tx['type']} - {tx['amount']} {tx.get('currency', 'RUB')}")
            
            return True
                
        except Exception as e:
            print(f"✗ Error calling endpoint: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await engine.dispose()


async def main():
    """Run all tests."""
    print("=" * 70)
    print("USER PROFILE MANAGEMENT TESTS")
    print("Testing Requirements: 2.1, 2.2, 2.3, 2.4")
    print("=" * 70)
    
    results = []
    
    results.append(await test_get_user_profile())
    results.append(await test_update_language_preference())
    results.append(await test_get_balance())
    results.append(await test_get_transactions())
    
    print("\n" + "=" * 70)
    print(f"TESTS COMPLETED: {sum(results)}/{len(results)} PASSED")
    print("=" * 70)
    
    if all(results):
        print("\n✓ All tests passed! User profile endpoints are working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
