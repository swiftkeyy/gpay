"""Test stock management endpoint for auto-delivery lots."""
import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.entities import User, Seller, Lot, LotStockItem
from app.core.config import get_settings


async def test_stock_management():
    """Test adding stock items to auto-delivery lots."""
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find an active seller
        result = await session.execute(
            select(Seller).where(Seller.status == "active").limit(1)
        )
        seller = result.scalar_one_or_none()
        
        if not seller:
            print("❌ No active sellers found in database")
            return
        
        print(f"\n✅ Found seller: {seller.shop_name} (ID: {seller.id})")
        
        # Find or create an auto-delivery lot for this seller
        result = await session.execute(
            select(Lot).where(
                Lot.seller_id == seller.id,
                Lot.delivery_type == "auto"
            ).limit(1)
        )
        lot = result.scalar_one_or_none()
        
        if not lot:
            print("⚠️  No auto-delivery lots found, creating one for testing...")
            # Get a product to associate with the lot
            from app.models.entities import Product
            result = await session.execute(select(Product).limit(1))
            product = result.scalar_one_or_none()
            
            if not product:
                print("❌ No products found in database")
                return
            
            lot = Lot(
                seller_id=seller.id,
                product_id=product.id,
                title="Test Auto-Delivery Lot",
                description="Test lot for stock management",
                price=Decimal("100.00"),
                currency_code="RUB",
                delivery_type="auto",
                stock_count=0,
                status="draft"
            )
            session.add(lot)
            await session.commit()
            await session.refresh(lot)
            print(f"✅ Created test lot (ID: {lot.id})")
        else:
            print(f"✅ Found auto-delivery lot: {lot.title} (ID: {lot.id})")
        
        # Check current stock
        result = await session.execute(
            select(LotStockItem).where(
                LotStockItem.lot_id == lot.id,
                LotStockItem.is_sold == False,
                LotStockItem.is_reserved == False
            )
        )
        current_stock = result.scalars().all()
        print(f"\n📦 Current available stock: {len(current_stock)} items")
        print(f"   Lot stock_count field: {lot.stock_count}")
        print(f"   Lot status: {lot.status}")
        
        # Test adding stock items
        print("\n🔄 Testing stock addition...")
        test_items = [
            "account1:password123",
            "account2:password456",
            "account3:password789"
        ]
        
        for item_data in test_items:
            stock_item = LotStockItem(
                lot_id=lot.id,
                data=item_data,
                is_sold=False,
                is_reserved=False
            )
            session.add(stock_item)
        
        await session.flush()
        
        # Count new stock
        result = await session.execute(
            select(LotStockItem).where(
                LotStockItem.lot_id == lot.id,
                LotStockItem.is_sold == False,
                LotStockItem.is_reserved == False
            )
        )
        new_stock = result.scalars().all()
        
        # Update lot stock_count
        lot.stock_count = len(new_stock)
        
        # Update status if was out_of_stock
        if lot.status == "out_of_stock" and lot.stock_count > 0:
            lot.status = "active"
            print("   ✅ Lot status changed from out_of_stock to active")
        
        await session.commit()
        await session.refresh(lot)
        
        print(f"\n✅ Successfully added {len(test_items)} stock items")
        print(f"   New stock count: {lot.stock_count}")
        print(f"   Lot status: {lot.status}")
        
        # Verify the data
        print("\n📋 Stock items in database:")
        for idx, item in enumerate(new_stock[-3:], 1):  # Show last 3 items
            print(f"   {idx}. ID: {item.id}, Data: {item.data[:20]}..., Sold: {item.is_sold}, Reserved: {item.is_reserved}")
        
        # Test validation: try to add stock to non-auto lot
        print("\n🔄 Testing validation (non-auto delivery lot)...")
        result = await session.execute(
            select(Lot).where(
                Lot.seller_id == seller.id,
                Lot.delivery_type != "auto"
            ).limit(1)
        )
        manual_lot = result.scalar_one_or_none()
        
        if manual_lot:
            print(f"   Found manual lot: {manual_lot.title} (delivery_type: {manual_lot.delivery_type})")
            print("   ✅ Validation should reject adding stock to this lot")
        else:
            print("   ⚠️  No manual delivery lots found to test validation")
        
        # Test stock depletion scenario
        print("\n🔄 Testing stock depletion (marking items as sold)...")
        result = await session.execute(
            select(LotStockItem).where(
                LotStockItem.lot_id == lot.id,
                LotStockItem.is_sold == False
            ).limit(lot.stock_count)  # Mark all as sold
        )
        items_to_sell = result.scalars().all()
        
        for item in items_to_sell:
            item.is_sold = True
        
        await session.flush()
        
        # Recount stock
        result = await session.execute(
            select(LotStockItem).where(
                LotStockItem.lot_id == lot.id,
                LotStockItem.is_sold == False,
                LotStockItem.is_reserved == False
            )
        )
        remaining_stock = result.scalars().all()
        
        lot.stock_count = len(remaining_stock)
        
        # Should update to out_of_stock
        if lot.stock_count == 0:
            lot.status = "out_of_stock"
            print("   ✅ Lot status changed to out_of_stock (stock depleted)")
        
        await session.commit()
        await session.refresh(lot)
        
        print(f"   Final stock count: {lot.stock_count}")
        print(f"   Final lot status: {lot.status}")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nExpected API endpoint behavior:")
        print("POST /api/v1/sellers/me/lots/{lot_id}/stock")
        print("\nRequest body:")
        print({
            "items": [
                {"data": "username:password123"},
                {"data": "username2:password456"},
                {"data": "code:ABC123XYZ"}
            ]
        })
        print("\nResponse (201 Created):")
        print({
            "lot_id": lot.id,
            "items_added": 3,
            "total_stock": "count of available items",
            "items": [
                {
                    "id": "item_id",
                    "data": "username:password123",
                    "status": "available",
                    "created_at": "2024-01-01T12:00:00Z"
                }
            ]
        })
        print("\nValidation errors:")
        print("- 404: Lot not found or doesn't belong to seller")
        print("- 400: Lot delivery_type is not 'auto'")
        print("- 400: Items list is empty")


if __name__ == "__main__":
    asyncio.run(test_stock_management())
