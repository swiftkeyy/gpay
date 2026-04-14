"""
Auto-complete expired deals
Run this script periodically (e.g., every hour via cron)
"""
import asyncio
import logging

from app.db.session import SessionLocal
from app.services.deal import DealService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting auto-complete deals task...")
    
    async with SessionLocal() as session:
        try:
            deal_service = DealService(session)
            count = await deal_service.auto_complete_expired_deals()
            await session.commit()
            logger.info(f"✅ Auto-completed {count} deals")
        except Exception as e:
            logger.error(f"❌ Error auto-completing deals: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
