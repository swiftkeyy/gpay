"""
Seed script for marketplace features (sellers, lots, etc.)
Run after initial seed.py
"""
from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.entities import User, Seller, Lot, LotStockItem, Product
from app.models.enums import SellerStatus, LotStatus, LotDeliveryType

settings = get_settings()


async def seed_marketplace():
    async with SessionLocal() as session:
        print("🌱 Seeding marketplace data...")
        
        # Get or create test users for sellers
        test_sellers_data = [
            {"telegram_id": 111111111, "shop_name": "GameShop Pro", "description": "Профессиональный магазин игровых товаров"},
            {"telegram_id": 222222222, "shop_name": "FastGames", "description": "Быстрая доставка, низкие цены"},
            {"telegram_id": 333333333, "shop_name": "TopSeller", "description": "Топовый продавец с лучшими ценами"},
        ]
        
        sellers = []
        for seller_data in test_sellers_data:
            # Get or create user
            result = await session.execute(
                select(User).where(User.telegram_id == seller_data["telegram_id"])
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    telegram_id=seller_data["telegram_id"],
                    username=f"seller_{seller_data['telegram_id']}",
                    first_name=seller_data["shop_name"],
                    balance=Decimal("0.00")
                )
                session.add(user)
                await session.flush()
            
            # Check if seller exists
            result = await session.execute(
                select(Seller).where(Seller.user_id == user.id)
            )
            seller = result.scalar_one_or_none()
            
            if not seller:
                seller = Seller(
                    user_id=user.id,
                    shop_name=seller_data["shop_name"],
                    description=seller_data["description"],
                    status=SellerStatus.ACTIVE,
                    rating=Decimal("4.5"),
                    total_sales=100,
                    total_reviews=50,
                    balance=Decimal("10000.00"),
                    is_verified=True
                )
                session.add(seller)
                await session.flush()
                print(f"✅ Created seller: {seller.shop_name}")
            
            sellers.append(seller)
        
        # Get products
        result = await session.execute(select(Product).limit(10))
        products = list(result.scalars().all())
        
        if not products:
            print("⚠️ No products found. Run seed.py first!")
            return
        
        # Create lots for each seller
        lot_templates = [
            {
                "title_suffix": "Быстрая доставка",
                "price_multiplier": Decimal("1.0"),
                "delivery_type": LotDeliveryType.AUTO,
                "stock_count": 10
            },
            {
                "title_suffix": "Выгодная цена",
                "price_multiplier": Decimal("0.9"),
                "delivery_type": LotDeliveryType.MANUAL,
                "stock_count": 0
            },
            {
                "title_suffix": "Премиум",
                "price_multiplier": Decimal("1.2"),
                "delivery_type": LotDeliveryType.AUTO,
                "stock_count": 5
            },
        ]
        
        lots_created = 0
        for seller in sellers:
            for product in products[:5]:  # Create lots for first 5 products
                for template in lot_templates[:2]:  # 2 lots per product per seller
                    # Check if lot exists
                    result = await session.execute(
                        select(Lot).where(
                            Lot.seller_id == seller.id,
                            Lot.product_id == product.id,
                            Lot.title == f"{product.title} - {template['title_suffix']}"
                        )
                    )
                    existing_lot = result.scalar_one_or_none()
                    
                    if existing_lot:
                        continue
                    
                    # Get product price
                    from app.services.pricing import PricingService
                    pricing_service = PricingService(session)
                    base_price = await pricing_service.get_product_price(product.id)
                    
                    if not base_price:
                        base_price = Decimal("100.00")
                    
                    lot_price = (base_price * template["price_multiplier"]).quantize(Decimal("0.01"))
                    
                    lot = Lot(
                        seller_id=seller.id,
                        product_id=product.id,
                        title=f"{product.title} - {template['title_suffix']}",
                        description=f"Качественный товар от {seller.shop_name}",
                        price=lot_price,
                        delivery_type=template["delivery_type"],
                        stock_count=template["stock_count"],
                        status=LotStatus.ACTIVE if template["stock_count"] > 0 or template["delivery_type"] == LotDeliveryType.MANUAL else LotStatus.DRAFT,
                        delivery_time_minutes=5 if template["delivery_type"] == LotDeliveryType.AUTO else 30
                    )
                    session.add(lot)
                    await session.flush()
                    
                    # Add stock items for auto-delivery lots
                    if template["delivery_type"] == LotDeliveryType.AUTO and template["stock_count"] > 0:
                        for i in range(template["stock_count"]):
                            stock_item = LotStockItem(
                                lot_id=lot.id,
                                data=f"CODE-{lot.id}-{i+1:03d}-XXXX-YYYY-ZZZZ"
                            )
                            session.add(stock_item)
                    
                    lots_created += 1
        
        await session.commit()
        print(f"✅ Created {lots_created} lots")
        print(f"✅ Marketplace seeding completed!")


if __name__ == "__main__":
    asyncio.run(seed_marketplace())
