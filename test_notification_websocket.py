"""Test notification WebSocket implementation."""
import asyncio
import sys
from decimal import Decimal

# Add project root to path
sys.path.insert(0, '.')


async def test_notification_endpoints():
    """Test notification REST API endpoints."""
    print("\n=== Testing Notification Endpoints ===")
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.core.config import get_settings
    from app.models.entities import User, Notification
    from app.models.enums import NotificationType
    from api.routers.notifications import (
        get_notifications,
        mark_as_read,
        mark_all_as_read,
        get_unread_count
    )
    
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
        
        print(f"Using test user: {user.username} (ID: {user.id})")
        
        # Test 1: Create test notifications
        print("\n1. Creating test notifications...")
        notifications = [
            Notification(
                user_id=user.id,
                notification_type=NotificationType.NEW_ORDER,
                title="New Order",
                message="You have a new order #123",
                reference_type="order",
                reference_id=123,
                is_read=False
            ),
            Notification(
                user_id=user.id,
                notification_type=NotificationType.PAYMENT,
                title="Payment Received",
                message="Payment confirmed for order #123",
                reference_type="order",
                reference_id=123,
                is_read=False
            ),
            Notification(
                user_id=user.id,
                notification_type=NotificationType.SYSTEM,
                title="Welcome",
                message="Welcome to the marketplace!",
                is_read=True
            )
        ]
        
        for notif in notifications:
            session.add(notif)
        await session.commit()
        print("✓ Created 3 test notifications")
        
        # Test 2: GET /api/v1/notifications
        print("\n2. Testing GET /api/v1/notifications...")
        response = await get_notifications(
            page=1,
            limit=20,
            current_user=user,
            session=session
        )
        
        assert "items" in response
        assert "total" in response
        assert response["total"] >= 3
        assert len(response["items"]) >= 3
        
        # Verify notification structure
        notif = response["items"][0]
        assert "id" in notif
        assert "type" in notif
        assert "title" in notif
        assert "message" in notif
        assert "is_read" in notif
        assert "reference_type" in notif
        assert "reference_id" in notif
        assert "created_at" in notif
        print(f"✓ Retrieved {response['total']} notifications")
        print(f"  First notification: {notif['title']}")
        
        # Test 3: GET /api/v1/notifications/unread-count
        print("\n3. Testing GET /api/v1/notifications/unread-count...")
        response = await get_unread_count(current_user=user, session=session)
        assert "count" in response
        unread_count = response["count"]
        print(f"✓ Unread count: {unread_count}")
        
        # Test 4: PATCH /api/v1/notifications/{id}/read
        print("\n4. Testing PATCH /api/v1/notifications/{id}/read...")
        notification_id = notifications[0].id
        response = await mark_as_read(
            notification_id=notification_id,
            current_user=user,
            session=session
        )
        
        assert response["is_read"] is True
        assert "read_at" in response
        print(f"✓ Marked notification {notification_id} as read")
        
        # Verify unread count decreased
        response = await get_unread_count(current_user=user, session=session)
        new_unread_count = response["count"]
        assert new_unread_count == unread_count - 1
        print(f"✓ Unread count decreased to {new_unread_count}")
        
        # Test 5: POST /api/v1/notifications/read-all
        print("\n5. Testing POST /api/v1/notifications/read-all...")
        response = await mark_all_as_read(current_user=user, session=session)
        assert "message" in response
        assert "updated_count" in response
        print(f"✓ Marked all notifications as read (updated {response['updated_count']})")
        
        # Verify all are read
        response = await get_unread_count(current_user=user, session=session)
        assert response["count"] == 0
        print("✓ All notifications marked as read")
        
        # Cleanup
        for notif in notifications:
            await session.delete(notif)
        await session.commit()
        print("\n✓ Cleanup completed")
        
        return True


async def test_notification_pagination():
    """Test notification pagination."""
    print("\n=== Testing Notification Pagination ===")
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.core.config import get_settings
    from app.models.entities import User, Notification
    from app.models.enums import NotificationType
    from api.routers.notifications import get_notifications
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get first user
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("✗ No users in database")
            return False
        
        # Create 25 test notifications
        print("Creating 25 test notifications...")
        notifications = []
        for i in range(25):
            notif = Notification(
                user_id=user.id,
                notification_type=NotificationType.SYSTEM,
                title=f"Notification {i}",
                message=f"Test message {i}",
                is_read=False
            )
            session.add(notif)
            notifications.append(notif)
        await session.commit()
        print("✓ Created 25 notifications")
        
        # Test first page
        print("\nTesting page 1...")
        response = await get_notifications(
            page=1,
            limit=10,
            current_user=user,
            session=session
        )
        assert len(response["items"]) == 10
        assert response["page"] == 1
        assert response["limit"] == 10
        print(f"✓ Page 1: {len(response['items'])} items")
        
        # Test second page
        print("Testing page 2...")
        response = await get_notifications(
            page=2,
            limit=10,
            current_user=user,
            session=session
        )
        assert len(response["items"]) == 10
        print(f"✓ Page 2: {len(response['items'])} items")
        
        # Test third page
        print("Testing page 3...")
        response = await get_notifications(
            page=3,
            limit=10,
            current_user=user,
            session=session
        )
        assert len(response["items"]) >= 5
        print(f"✓ Page 3: {len(response['items'])} items")
        
        # Cleanup
        for notif in notifications:
            await session.delete(notif)
        await session.commit()
        print("\n✓ Cleanup completed")
        
        return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("NOTIFICATION SYSTEM TESTS")
    print("=" * 60)
    
    try:
        # Test notification endpoints
        result1 = await test_notification_endpoints()
        
        # Test pagination
        result2 = await test_notification_pagination()
        
        if result1 and result2:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ SOME TESTS FAILED")
            print("=" * 60)
            return False
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

