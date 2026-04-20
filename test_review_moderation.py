"""
Test for Task 11.3: Review Moderation and Replies

This test verifies the review moderation and reply endpoints implementation.

Requirements tested:
- 11.5: Admin approval/rejection endpoints for reviews
- 11.6: POST /api/v1/reviews/{id}/reply endpoint for sellers
- 11.7: Calculate average rating as mean of published reviews
- 11.8: GET /api/v1/products/{id}/reviews with pagination
- 11.9: GET /api/v1/sellers/{id}/reviews with pagination
"""

import asyncio
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.entities import (
    User, Admin, Seller, Product, Order, OrderItem, Deal, Review, SellerReview
)
from app.models.enums import (
    ReviewStatus, OrderStatus, DealStatus, SellerStatus, AdminRole
)
from api.routers.reviews import (
    get_product_reviews,
    get_seller_reviews,
    reply_to_review,
    get_pending_reviews,
    moderate_product_review,
    moderate_seller_review,
    ReviewReply,
    ReviewModeration
)


async def test_review_moderation_and_replies():
    """Test review moderation and reply endpoints."""
    
    # Create test database engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create test data
        print("\n📦 Creating test data...")
        
        # Create users
        buyer = User(
            telegram_id=123456,
            username="buyer_user",
            balance=Decimal("1000.00")
        )
        seller_user = User(
            telegram_id=789012,
            username="seller_user",
            balance=Decimal("0.00")
        )
        admin_user = User(
            telegram_id=111222,
            username="admin_user",
            balance=Decimal("0.00")
        )
        session.add_all([buyer, seller_user, admin_user])
        await session.flush()
        
        # Create admin
        admin = Admin(
            user_id=admin_user.id,
            role=AdminRole.SUPER_ADMIN
        )
        session.add(admin)
        await session.flush()
        
        # Create seller
        seller = Seller(
            user_id=seller_user.id,
            shop_name="Test Shop",
            status=SellerStatus.ACTIVE,
            verified=True,
            rating=Decimal("0.00")
        )
        session.add(seller)
        await session.flush()
        
        # Create product
        product = Product(
            name="Test Product",
            description="Test Description",
            rating=Decimal("0.00")
        )
        session.add(product)
        await session.flush()
        
        # Create order
        order = Order(
            user_id=buyer.id,
            total_amount=Decimal("100.00"),
            status=OrderStatus.COMPLETED
        )
        session.add(order)
        await session.flush()
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            price=Decimal("100.00")
        )
        session.add(order_item)
        await session.flush()
        
        # Create deal
        deal = Deal(
            order_id=order.id,
            seller_id=seller.id,
            buyer_id=buyer.id,
            amount=Decimal("100.00"),
            status=DealStatus.COMPLETED
        )
        session.add(deal)
        await session.flush()
        
        # Create product reviews (pending moderation)
        review1 = Review(
            user_id=buyer.id,
            order_id=order.id,
            product_id=product.id,
            rating=5,
            text="Great product!",
            status=ReviewStatus.HIDDEN  # Pending moderation
        )
        review2 = Review(
            user_id=buyer.id,
            order_id=order.id,
            product_id=product.id,
            rating=4,
            text="Good product",
            status=ReviewStatus.HIDDEN
        )
        session.add_all([review1, review2])
        await session.flush()
        
        # Create seller review (pending moderation)
        seller_review = SellerReview(
            buyer_id=buyer.id,
            deal_id=deal.id,
            seller_id=seller.id,
            rating=5,
            text="Excellent seller!",
            status=ReviewStatus.HIDDEN
        )
        session.add(seller_review)
        await session.flush()
        
        await session.commit()
        
        print(f"✅ Test data created")
        print(f"   Buyer ID: {buyer.id}")
        print(f"   Seller ID: {seller.id}")
        print(f"   Admin ID: {admin_user.id}")
        print(f"   Product ID: {product.id}")
        print(f"   Review 1 ID: {review1.id}")
        print(f"   Review 2 ID: {review2.id}")
        print(f"   Seller Review ID: {seller_review.id}")
        
        # Test 1: Get pending reviews (admin)
        print("\n📝 Test 1: Getting pending reviews...")
        try:
            # Mock the dependency
            class MockRequest:
                pass
            
            result = await get_pending_reviews(
                review_type="all",
                skip=0,
                limit=20,
                current_admin=admin_user,
                db=session
            )
            
            assert len(result["items"]) == 3, f"Expected 3 pending reviews, got {len(result['items'])}"
            assert result["total"] == 3
            print(f"✅ Found {len(result['items'])} pending reviews")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 2: Moderate product review (approve)
        print("\n📝 Test 2: Moderating product review (approve)...")
        try:
            moderation_request = ReviewModeration(
                status="published",
                rejection_reason=None
            )
            
            result = await moderate_product_review(
                review_id=review1.id,
                request=moderation_request,
                current_admin=admin_user,
                db=session
            )
            
            await session.refresh(review1)
            assert review1.status == ReviewStatus.PUBLISHED
            assert review1.moderated_by_admin_id == admin_user.id
            assert review1.moderated_at is not None
            print(f"✅ Product review approved successfully")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 3: Moderate product review (reject)
        print("\n📝 Test 3: Moderating product review (reject)...")
        try:
            moderation_request = ReviewModeration(
                status="rejected",
                rejection_reason="Inappropriate content"
            )
            
            result = await moderate_product_review(
                review_id=review2.id,
                request=moderation_request,
                current_admin=admin_user,
                db=session
            )
            
            await session.refresh(review2)
            assert review2.status == ReviewStatus.REJECTED
            assert review2.rejection_reason == "Inappropriate content"
            print(f"✅ Product review rejected successfully")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 4: Moderate seller review (approve)
        print("\n📝 Test 4: Moderating seller review (approve)...")
        try:
            moderation_request = ReviewModeration(
                status="published",
                rejection_reason=None
            )
            
            result = await moderate_seller_review(
                review_id=seller_review.id,
                request=moderation_request,
                current_admin=admin_user,
                db=session
            )
            
            await session.refresh(seller_review)
            assert seller_review.status == ReviewStatus.PUBLISHED
            print(f"✅ Seller review approved successfully")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 5: Get product reviews (public)
        print("\n📝 Test 5: Getting product reviews (public)...")
        try:
            result = await get_product_reviews(
                product_id=product.id,
                skip=0,
                limit=20,
                db=session
            )
            
            # Only published reviews should be returned
            assert len(result["items"]) == 1, f"Expected 1 published review, got {len(result['items'])}"
            assert result["items"][0]["rating"] == 5
            assert result["average_rating"] == 5.0
            print(f"✅ Found {len(result['items'])} published product reviews")
            print(f"   Average rating: {result['average_rating']}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 6: Get seller reviews (public)
        print("\n📝 Test 6: Getting seller reviews (public)...")
        try:
            result = await get_seller_reviews(
                seller_id=seller.id,
                skip=0,
                limit=20,
                db=session
            )
            
            assert len(result["items"]) == 1
            assert result["items"][0]["rating"] == 5
            assert result["average_rating"] == 5.0
            print(f"✅ Found {len(result['items'])} published seller reviews")
            print(f"   Average rating: {result['average_rating']}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 7: Seller replies to product review
        print("\n📝 Test 7: Seller replying to product review...")
        try:
            reply_request = ReviewReply(
                reply_text="Thank you for your feedback!"
            )
            
            result = await reply_to_review(
                review_id=review1.id,
                request=reply_request,
                current_user=seller_user,
                db=session
            )
            
            await session.refresh(review1)
            assert review1.reply_text == "Thank you for your feedback!"
            assert review1.replied_at is not None
            print(f"✅ Seller replied to product review successfully")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 8: Seller replies to seller review
        print("\n📝 Test 8: Seller replying to seller review...")
        try:
            reply_request = ReviewReply(
                reply_text="Thank you for your business!"
            )
            
            result = await reply_to_review(
                review_id=seller_review.id,
                request=reply_request,
                current_user=seller_user,
                db=session
            )
            
            await session.refresh(seller_review)
            assert seller_review.seller_reply == "Thank you for your business!"
            assert seller_review.seller_replied_at is not None
            print(f"✅ Seller replied to seller review successfully")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 9: Verify average rating calculation
        print("\n📝 Test 9: Verifying average rating calculation...")
        try:
            # Create another published review
            review3 = Review(
                user_id=buyer.id,
                order_id=order.id,
                product_id=product.id,
                rating=3,
                text="Average product",
                status=ReviewStatus.PUBLISHED
            )
            session.add(review3)
            await session.commit()
            
            result = await get_product_reviews(
                product_id=product.id,
                skip=0,
                limit=20,
                db=session
            )
            
            # Average of 5 and 3 should be 4.0
            expected_avg = 4.0
            assert result["average_rating"] == expected_avg, f"Expected {expected_avg}, got {result['average_rating']}"
            print(f"✅ Average rating calculated correctly: {result['average_rating']}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        # Test 10: Pagination test
        print("\n📝 Test 10: Testing pagination...")
        try:
            result = await get_product_reviews(
                product_id=product.id,
                skip=0,
                limit=1,
                db=session
            )
            
            assert len(result["items"]) == 1
            assert result["total"] == 2
            assert result["skip"] == 0
            assert result["limit"] == 1
            print(f"✅ Pagination working correctly")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
        return True


if __name__ == "__main__":
    print("="*60)
    print("Task 11.3: Review Moderation and Replies Test")
    print("="*60)
    result = asyncio.run(test_review_moderation_and_replies())
    exit(0 if result else 1)
