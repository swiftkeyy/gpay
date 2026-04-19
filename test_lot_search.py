"""Test script for lot search endpoints."""
import asyncio
from decimal import Decimal
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Lot, Seller, User, Product, Game, Category, SellerStatus, LotStatus, LotDeliveryType


async def create_test_data():
    """Create test sellers and lots for testing."""
    async with SessionLocal() as session:
        # Check if we already have test data
        result = await session.execute(select(Lot).limit(1))
        existing_lot = result.scalar_one_or_none()
        
        if existing_lot:
            print("✅ Test data already exists")
            return
        
        print("Creating test data...")
        
        # Get or create test user
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=123456789,
                username="test_seller",
                first_name="Test",
                last_name="Seller",
                referral_code="TEST123"
            )
            session.add(user)
            await session.flush()
        
        # Create seller
        result = await session.execute(select(Seller).where(Seller.user_id == user.id))
        seller = result.scalar_one_or_none()
        
        if not seller:
            seller = Seller(
                user_id=user.id,
                shop_name="Test Shop",
                description="Test shop for testing",
                status=SellerStatus.ACTIVE,
                rating=Decimal("4.5"),
                total_sales=100,
                is_verified=True
            )
            session.add(seller)
            await session.flush()
        
        # Get games and products
        result = await session.execute(select(Game).limit(2))
        games = result.scalars().all()
        
        if not games:
            print("❌ No games found. Run seed.py first!")
            return
        
        # Get products
        result = await session.execute(select(Product).limit(5))
        products = result.scalars().all()
        
        if not products:
            print("❌ No products found. Run seed.py first!")
            return
        
        # Create test lots
        lots_data = [
            {
                "product": products[0],
                "title": "Brawl Stars Gems 30 - Fast Delivery",
                "description": "Quick and safe delivery of 30 gems",
                "price": Decimal("99.00"),
                "delivery_type": LotDeliveryType.AUTO,
                "stock_count": 50,
                "is_featured": True
            },
            {
                "product": products[1],
                "title": "Brawl Stars Gems 80 - Best Price",
                "description": "80 gems with best price guarantee",
                "price": Decimal("189.00"),
                "delivery_type": LotDeliveryType.MANUAL,
                "stock_count": 30,
                "is_featured": False
            },
            {
                "product": products[2],
                "title": "Brawl Stars Gems 170 - Premium",
                "description": "Premium package with bonus",
                "price": Decimal("329.00"),
                "delivery_type": LotDeliveryType.AUTO,
                "stock_count": 20,
                "is_featured": True
            },
        ]
        
        if len(products) > 3:
            lots_data.extend([
                {
                    "product": products[3],
                    "title": "Brawl Pass - Season Pass",
                    "description": "Full season pass with all rewards",
                    "price": Decimal("699.00"),
                    "delivery_type": LotDeliveryType.MANUAL,
                    "stock_count": 10,
                    "is_featured": False
                },
                {
                    "product": products[4],
                    "title": "Standoff 2 Gold 100",
                    "description": "100 gold for Standoff 2",
                    "price": Decimal("89.00"),
                    "delivery_type": LotDeliveryType.AUTO,
                    "stock_count": 100,
                    "is_featured": False
                },
            ])
        
        for lot_data in lots_data:
            lot = Lot(
                seller_id=seller.id,
                product_id=lot_data["product"].id,
                title=lot_data["title"],
                description=lot_data["description"],
                price=lot_data["price"],
                currency_code="RUB",
                delivery_type=lot_data["delivery_type"],
                stock_count=lot_data["stock_count"],
                status=LotStatus.ACTIVE,
                is_featured=lot_data["is_featured"],
                sold_count=0,
                reserved_count=0
            )
            session.add(lot)
        
        await session.commit()
        print(f"✅ Created {len(lots_data)} test lots")


async def test_search():
    """Test the search functionality."""
    async with SessionLocal() as session:
        # Test 1: Get all active lots
        print("\n=== Test 1: Get all active lots ===")
        result = await session.execute(
            select(Lot).where(Lot.status == LotStatus.ACTIVE, Lot.is_deleted == False)
        )
        lots = result.scalars().all()
        print(f"Found {len(lots)} active lots")
        
        # Test 2: Filter by price range
        print("\n=== Test 2: Filter by price range (100-400) ===")
        result = await session.execute(
            select(Lot).where(
                Lot.status == LotStatus.ACTIVE,
                Lot.is_deleted == False,
                Lot.price >= 100,
                Lot.price <= 400
            )
        )
        lots = result.scalars().all()
        print(f"Found {len(lots)} lots in price range")
        for lot in lots:
            print(f"  - {lot.title}: {lot.price} RUB")
        
        # Test 3: Filter by delivery type
        print("\n=== Test 3: Filter by delivery type (auto) ===")
        result = await session.execute(
            select(Lot).where(
                Lot.status == LotStatus.ACTIVE,
                Lot.is_deleted == False,
                Lot.delivery_type == LotDeliveryType.AUTO
            )
        )
        lots = result.scalars().all()
        print(f"Found {len(lots)} lots with auto delivery")
        for lot in lots:
            print(f"  - {lot.title}")
        
        # Test 4: Sort by price ascending
        print("\n=== Test 4: Sort by price ascending ===")
        result = await session.execute(
            select(Lot).where(
                Lot.status == LotStatus.ACTIVE,
                Lot.is_deleted == False
            ).order_by(Lot.price.asc())
        )
        lots = result.scalars().all()
        print(f"Lots sorted by price:")
        for lot in lots:
            print(f"  - {lot.title}: {lot.price} RUB")
        
        # Test 5: Featured lots (popularity)
        print("\n=== Test 5: Featured lots (popularity) ===")
        result = await session.execute(
            select(Lot).where(
                Lot.status == LotStatus.ACTIVE,
                Lot.is_deleted == False
            ).order_by(Lot.is_featured.desc(), Lot.sold_count.desc())
        )
        lots = result.scalars().all()
        print(f"Lots sorted by popularity:")
        for lot in lots:
            featured = "⭐" if lot.is_featured else ""
            print(f"  - {featured} {lot.title}: {lot.sold_count} sales")


async def main():
    """Main test function."""
    print("🧪 Testing Lot Search Implementation\n")
    
    # Create test data
    await create_test_data()
    
    # Run tests
    await test_search()
    
    print("\n✅ All tests completed!")
    print("\nYou can now test the API endpoints:")
    print("  GET http://localhost:8000/api/v1/lots")
    print("  GET http://localhost:8000/api/v1/lots?min_price=100&max_price=400")
    print("  GET http://localhost:8000/api/v1/lots?delivery_type=auto")
    print("  GET http://localhost:8000/api/v1/lots?sort=price_asc")
    print("  GET http://localhost:8000/api/v1/lots?sort=popularity")
    print("  GET http://localhost:8000/api/v1/lots/{lot_id}")


if __name__ == "__main__":
    asyncio.run(main())
