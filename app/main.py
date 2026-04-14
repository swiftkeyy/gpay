from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import session_factory
from app.handlers.admin import broadcasts as admin_broadcasts
from app.handlers.admin import catalog as admin_catalog
from app.handlers.admin import misc as admin_misc
from app.handlers.admin import orders as admin_orders
from app.handlers.admin import panel
from app.handlers.admin import prices as admin_prices
from app.handlers.admin import promos as admin_promos
from app.handlers.admin import reviews as admin_reviews
from app.handlers.user import cart, catalog, checkout, orders, profile, reviews, start, support
from app.middlewares.block import BlockMiddleware
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.user_context import UserContextMiddleware

settings = get_settings()
logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """Run database migrations on startup."""
    logger.info("🔄 Checking database migrations...")
    
    try:
        async with session_factory() as session:
            # Check if balance column exists
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'balance'
            """))
            has_balance = result.fetchone() is not None
            
            if has_balance:
                logger.info("✅ Database is up to date")
                return
            
            logger.info("🔄 Applying marketplace migrations...")
            
            # Add balance column
            await session.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00"
            ))
            
            # Create enum types
            enums = [
                "CREATE TYPE seller_status_enum AS ENUM ('pending', 'active', 'suspended', 'banned')",
                "CREATE TYPE lot_status_enum AS ENUM ('draft', 'active', 'paused', 'out_of_stock', 'deleted')",
                "CREATE TYPE lot_delivery_type_enum AS ENUM ('auto', 'manual', 'coordinates')",
                "CREATE TYPE deal_status_enum AS ENUM ('created', 'paid', 'in_progress', 'waiting_confirmation', 'completed', 'canceled', 'dispute', 'refunded')",
                "CREATE TYPE transaction_type_enum AS ENUM ('deposit', 'purchase', 'sale', 'refund', 'withdrawal', 'commission', 'bonus', 'penalty')",
                "CREATE TYPE transaction_status_enum AS ENUM ('pending', 'completed', 'failed', 'canceled')",
                "CREATE TYPE withdrawal_status_enum AS ENUM ('pending', 'processing', 'completed', 'rejected', 'canceled')",
                "CREATE TYPE dispute_status_enum AS ENUM ('open', 'in_review', 'resolved', 'closed')",
                "CREATE TYPE notification_type_enum AS ENUM ('new_message', 'new_order', 'order_status', 'payment', 'review', 'system', 'price_alert')",
                "CREATE TYPE promo_type_enum AS ENUM ('percent', 'fixed')",
                "CREATE TYPE review_status_enum AS ENUM ('pending', 'published', 'rejected')",
                "CREATE TYPE broadcast_status_enum AS ENUM ('draft', 'scheduled', 'in_progress', 'completed', 'failed')",
                "CREATE TYPE audit_action_enum AS ENUM ('create', 'update', 'delete', 'view', 'login', 'logout', 'other')",
                "CREATE TYPE block_action_scope_enum AS ENUM ('global', 'catalog', 'orders', 'support', 'reviews')",
            ]
            
            for enum_sql in enums:
                try:
                    await session.execute(text(f"DO $$ BEGIN {enum_sql}; EXCEPTION WHEN duplicate_object THEN null; END $$;"))
                except Exception:
                    pass  # Enum already exists
            
            # Create tables (simplified - only if not exists)
            tables = [
                # Promo codes
                """CREATE TABLE IF NOT EXISTS promo_codes (
                    id SERIAL PRIMARY KEY, code VARCHAR(50) NOT NULL UNIQUE,
                    promo_type promo_type_enum NOT NULL, value NUMERIC(12, 2) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT true, max_usages INTEGER,
                    used_count INTEGER NOT NULL DEFAULT 0, starts_at TIMESTAMP WITH TIME ZONE,
                    ends_at TIMESTAMP WITH TIME ZONE, game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
                    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                    only_new_users BOOLEAN NOT NULL DEFAULT false, is_deleted BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_promo_codes_code ON promo_codes(code)",
                
                """CREATE TABLE IF NOT EXISTS promo_code_usages (
                    id SERIAL PRIMARY KEY, promo_code_id INTEGER NOT NULL REFERENCES promo_codes(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_promo_code_usages_promo_user ON promo_code_usages(promo_code_id, user_id)",
                
                # Referrals
                """CREATE TABLE IF NOT EXISTS referrals (
                    id SERIAL PRIMARY KEY, referrer_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    referred_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    referral_code VARCHAR(50) NOT NULL, first_order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
                    is_rewarded BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_referrals_referred_user_id UNIQUE (referred_user_id)
                )""",
                "CREATE INDEX IF NOT EXISTS ix_referrals_referrer ON referrals(referrer_user_id)",
                
                """CREATE TABLE IF NOT EXISTS referral_rewards (
                    id SERIAL PRIMARY KEY, referral_id INTEGER NOT NULL REFERENCES referrals(id) ON DELETE CASCADE,
                    referrer_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    referred_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    amount NUMERIC(12, 2) NOT NULL, description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_referral_rewards_referrer ON referral_rewards(referrer_user_id)",
                
                # Reviews
                """CREATE TABLE IF NOT EXISTS reviews (
                    id SERIAL PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5), text TEXT,
                    status review_status_enum NOT NULL DEFAULT 'published',
                    admin_reply TEXT, admin_replied_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_reviews_status_created ON reviews(status, created_at)",
                
                # Bot settings
                """CREATE TABLE IF NOT EXISTS bot_settings (
                    id SERIAL PRIMARY KEY, key VARCHAR(100) NOT NULL UNIQUE,
                    value TEXT NOT NULL, description TEXT, is_public BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_bot_settings_key ON bot_settings(key)",
                
                # Broadcasts
                """CREATE TABLE IF NOT EXISTS broadcasts (
                    id SERIAL PRIMARY KEY, message_text TEXT NOT NULL,
                    media_id INTEGER REFERENCES media_files(id) ON DELETE SET NULL,
                    status broadcast_status_enum NOT NULL DEFAULT 'draft',
                    scheduled_at TIMESTAMP WITH TIME ZONE, started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE, total_users INTEGER NOT NULL DEFAULT 0,
                    sent_count INTEGER NOT NULL DEFAULT 0, failed_count INTEGER NOT NULL DEFAULT 0,
                    created_by_admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_broadcasts_status ON broadcasts(status)",
                
                # Audit logs
                """CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY, admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
                    action audit_action_enum NOT NULL, entity_type VARCHAR(50),
                    entity_id INTEGER, description TEXT, metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    ip_address VARCHAR(45), user_agent TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_created ON audit_logs(entity_type, created_at)",
                "CREATE INDEX IF NOT EXISTS ix_audit_logs_admin_created ON audit_logs(admin_id, created_at)",
                
                # User blocks
                """CREATE TABLE IF NOT EXISTS user_blocks (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    scope block_action_scope_enum NOT NULL, reason TEXT,
                    blocked_by_admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_user_blocks_user_scope ON user_blocks(user_id, scope)",
                
                # Marketplace tables
                """CREATE TABLE IF NOT EXISTS sellers (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    status seller_status_enum NOT NULL DEFAULT 'pending', shop_name VARCHAR(120) NOT NULL,
                    description TEXT, rating NUMERIC(3, 2) NOT NULL DEFAULT 0.00,
                    total_sales INTEGER NOT NULL DEFAULT 0, total_reviews INTEGER NOT NULL DEFAULT 0,
                    balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00, commission_percent NUMERIC(5, 2) NOT NULL DEFAULT 10.00,
                    is_verified BOOLEAN NOT NULL DEFAULT false, verified_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_sellers_user_id UNIQUE (user_id)
                )""",
                "CREATE INDEX IF NOT EXISTS ix_sellers_status_rating ON sellers(status, rating)",
                
                """CREATE TABLE IF NOT EXISTS lots (
                    id SERIAL PRIMARY KEY, seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL, description TEXT, price NUMERIC(12, 2) NOT NULL,
                    currency_code VARCHAR(10) NOT NULL DEFAULT 'RUB',
                    delivery_type lot_delivery_type_enum NOT NULL DEFAULT 'manual',
                    stock_count INTEGER NOT NULL DEFAULT 0, reserved_count INTEGER NOT NULL DEFAULT 0,
                    sold_count INTEGER NOT NULL DEFAULT 0, status lot_status_enum NOT NULL DEFAULT 'draft',
                    auto_delivery_data JSONB NOT NULL DEFAULT '{}'::jsonb, delivery_time_minutes INTEGER,
                    is_featured BOOLEAN NOT NULL DEFAULT false, is_deleted BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_lots_product_seller_status ON lots(product_id, seller_id, status)",
                "CREATE INDEX IF NOT EXISTS ix_lots_status_price ON lots(status, price)",
                
                """CREATE TABLE IF NOT EXISTS deals (
                    id SERIAL PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    buyer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
                    lot_id INTEGER NOT NULL REFERENCES lots(id) ON DELETE CASCADE,
                    status deal_status_enum NOT NULL DEFAULT 'created', amount NUMERIC(12, 2) NOT NULL,
                    commission_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00, seller_amount NUMERIC(12, 2) NOT NULL,
                    escrow_released BOOLEAN NOT NULL DEFAULT false, escrow_released_at TIMESTAMP WITH TIME ZONE,
                    auto_complete_at TIMESTAMP WITH TIME ZONE, completed_at TIMESTAMP WITH TIME ZONE,
                    buyer_confirmed BOOLEAN NOT NULL DEFAULT false, buyer_confirmed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_deals_order_id UNIQUE (order_id)
                )""",
                "CREATE INDEX IF NOT EXISTS ix_deals_buyer_status ON deals(buyer_id, status)",
                "CREATE INDEX IF NOT EXISTS ix_deals_seller_status ON deals(seller_id, status)",
                
                """CREATE TABLE IF NOT EXISTS lot_stock_items (
                    id SERIAL PRIMARY KEY, lot_id INTEGER NOT NULL REFERENCES lots(id) ON DELETE CASCADE,
                    data TEXT NOT NULL, is_sold BOOLEAN NOT NULL DEFAULT false,
                    is_reserved BOOLEAN NOT NULL DEFAULT false, reserved_until TIMESTAMP WITH TIME ZONE,
                    sold_at TIMESTAMP WITH TIME ZONE, deal_id INTEGER REFERENCES deals(id) ON DELETE SET NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_lot_stock_items_lot_status ON lot_stock_items(lot_id, is_sold, is_reserved)",
                
                """CREATE TABLE IF NOT EXISTS deal_messages (
                    id SERIAL PRIMARY KEY, deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
                    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    message_text TEXT, media_id INTEGER REFERENCES media_files(id) ON DELETE SET NULL,
                    is_system BOOLEAN NOT NULL DEFAULT false, is_read BOOLEAN NOT NULL DEFAULT false,
                    read_at TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_deal_messages_deal_created ON deal_messages(deal_id, created_at)",
                
                """CREATE TABLE IF NOT EXISTS deal_disputes (
                    id SERIAL PRIMARY KEY, deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
                    initiator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    reason TEXT NOT NULL, status dispute_status_enum NOT NULL DEFAULT 'open',
                    admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL, resolution TEXT,
                    resolved_at TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_deal_disputes_deal_id UNIQUE (deal_id)
                )""",
                
                """CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    transaction_type transaction_type_enum NOT NULL, amount NUMERIC(12, 2) NOT NULL,
                    currency_code VARCHAR(10) NOT NULL DEFAULT 'RUB',
                    status transaction_status_enum NOT NULL DEFAULT 'pending',
                    balance_before NUMERIC(12, 2) NOT NULL, balance_after NUMERIC(12, 2) NOT NULL,
                    description TEXT, reference_type VARCHAR(50), reference_id INTEGER,
                    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_transactions_user_type_created ON transactions(user_id, transaction_type, created_at)",
                "CREATE INDEX IF NOT EXISTS ix_transactions_status ON transactions(status)",
                
                """CREATE TABLE IF NOT EXISTS seller_withdrawals (
                    id SERIAL PRIMARY KEY, seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
                    amount NUMERIC(12, 2) NOT NULL, currency_code VARCHAR(10) NOT NULL DEFAULT 'RUB',
                    status withdrawal_status_enum NOT NULL DEFAULT 'pending',
                    payment_method VARCHAR(50) NOT NULL, payment_details TEXT NOT NULL,
                    processed_by_admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
                    processed_at TIMESTAMP WITH TIME ZONE, rejection_reason TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_seller_withdrawals_seller_status ON seller_withdrawals(seller_id, status)",
                
                """CREATE TABLE IF NOT EXISTS seller_reviews (
                    id SERIAL PRIMARY KEY, seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
                    deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
                    buyer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5), text TEXT,
                    status review_status_enum NOT NULL DEFAULT 'published',
                    seller_reply TEXT, seller_replied_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_seller_reviews_seller_status ON seller_reviews(seller_id, status)",
                
                """CREATE TABLE IF NOT EXISTS favorites (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    lot_id INTEGER NOT NULL REFERENCES lots(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_favorites_user_lot UNIQUE (user_id, lot_id)
                )""",
                "CREATE INDEX IF NOT EXISTS ix_favorites_user_created ON favorites(user_id, created_at)",
                
                """CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    notification_type notification_type_enum NOT NULL, title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL, is_read BOOLEAN NOT NULL DEFAULT false,
                    read_at TIMESTAMP WITH TIME ZONE, reference_type VARCHAR(50), reference_id INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )""",
                "CREATE INDEX IF NOT EXISTS ix_notifications_user_read_created ON notifications(user_id, is_read, created_at)",
            ]
            
            for table_sql in tables:
                try:
                    await session.execute(text(table_sql))
                except Exception as e:
                    logger.warning(f"Table creation warning: {str(e)[:100]}")
            
            await session.commit()
            logger.info("✅ Migrations applied successfully!")
            
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        # Don't fail startup - let bot try to run anyway


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    
    # Run migrations before starting bot
    await run_migrations()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)

    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(UserContextMiddleware())
    dp.update.middleware(BlockMiddleware())
    dp.update.middleware(RateLimitMiddleware())

    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(orders.router)
    dp.include_router(profile.router)
    dp.include_router(support.router)
    dp.include_router(reviews.router)
    
    # Import and include new routers
    from app.handlers.user import seller, deals
    dp.include_router(seller.router)
    dp.include_router(deals.router)

    dp.include_router(panel.router)
    dp.include_router(admin_catalog.router)
    dp.include_router(admin_orders.router)
    dp.include_router(admin_prices.router)
    dp.include_router(admin_promos.router)
    dp.include_router(admin_broadcasts.router)
    dp.include_router(admin_misc.router)
    dp.include_router(admin_reviews.router)

    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "inline_query", "chosen_inline_result"])


if __name__ == "__main__":
    asyncio.run(main())
