"""
Cleanup expired stock reservations
Run this script periodically (e.g., every 15 minutes via cron)
"""
import asyncio
import logging

from app.db.session import SessionLocal
from app.services.lot import LotService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting cleanup reservations task...")
    
    async with SessionLocal() as session:
        try:
            lot_service = LotService(session)
            count = await lot_service.cleanup_expired_reservations()
            await session.commit()
            logger.info(f"✅ Released {count} expired reservations")
        except Exception as e:
            logger.error(f"❌ Error cleaning up reservations: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
