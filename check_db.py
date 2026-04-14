"""
Simple script to check database connection and current state.
Run this from bothost.ru web terminal: python check_db.py
"""
import asyncio
import logging
from sqlalchemy import text
from app.db.session import session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_database():
    """Check database connection and table status."""
    
    try:
        async with session_factory() as session:
            logger.info("✅ Database connection successful!")
            
            # Check if users table has balance column
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'balance'
            """))
            has_balance = result.fetchone() is not None
            
            if has_balance:
                logger.info("✅ users.balance column exists - migration already applied")
            else:
                logger.warning("⚠️  users.balance column NOT found - migration needed")
            
            # Check if sellers table exists
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'sellers'
            """))
            has_sellers = result.fetchone() is not None
            
            if has_sellers:
                logger.info("✅ sellers table exists")
            else:
                logger.warning("⚠️  sellers table NOT found - migration needed")
            
            # List all tables
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
            
            return has_balance and has_sellers
            
    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(check_database())
    if success:
        print("\n✅ Database is ready!")
    else:
        print("\n⚠️  Migration required! Run: python run_migrations.py")
    exit(0 if success else 1)
