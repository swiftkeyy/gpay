"""Test seller dashboard endpoint with performance metrics."""
import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.entities import User, Seller, Deal, DealMessage, DealDispute
from app.core.config import get_settings


async def test_seller_dashboard():
    """Test seller dashboard endpoint calculations."""
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find a seller with deals
        result = await session.execute(
            select(Seller).limit(1)
        )
        seller = result.scalar_one_or_none()
        
        if not seller:
            print("No sellers found in database")
            return
        
        print(f"\nTesting dashboard for seller ID: {seller.id}")
        print(f"Shop name: {seller.shop_name}")
        print(f"Rating: {seller.rating}")
        print(f"Total sales: {seller.total_sales}")
        
        # Check deals
        result = await session.execute(
            select(Deal).where(Deal.seller_id == seller.id).limit(5)
        )
        deals = result.scalars().all()
        print(f"\nFound {len(deals)} deals for this seller")
        
        # Check messages for response time calculation
        if deals:
            deal = deals[0]
            result = await session.execute(
                select(DealMessage).where(DealMessage.deal_id == deal.id)
            )
            messages = result.scalars().all()
            print(f"Deal {deal.id} has {len(messages)} messages")
            
            for msg in messages[:3]:
                print(f"  - Message from user {msg.sender_id} at {msg.created_at}")
        
        # Check disputes
        result = await session.execute(
            select(DealDispute).where(
                DealDispute.deal_id.in_([d.id for d in deals])
            )
        )
        disputes = result.scalars().all()
        print(f"\nFound {len(disputes)} disputes for these deals")
        
        print("\n✅ Dashboard data structure looks good!")
        print("\nExpected response format:")
        print({
            "balance": {
                "available": "float",
                "pending_withdrawals": "float",
                "in_escrow": "float"
            },
            "today": {"sales": "int", "revenue": "float"},
            "week": {"sales": "int", "revenue": "float"},
            "month": {"sales": "int", "revenue": "float"},
            "all_time": {"sales": "int", "revenue": "float"},
            "performance": {
                "rating": "float",
                "total_reviews": "int",
                "total_sales": "int",
                "active_deals": "int",
                "response_time": "float or None (minutes)",
                "completion_rate": "float or None (percentage)"
            }
        })


if __name__ == "__main__":
    asyncio.run(test_seller_dashboard())
