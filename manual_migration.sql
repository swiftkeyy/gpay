-- Manual migration for marketplace features
-- Execute this SQL in your PostgreSQL database

-- 1. Add balance column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00;

-- 2. Create new enum types
DO $$ BEGIN
    CREATE TYPE seller_status_enum AS ENUM ('pending', 'active', 'suspended', 'banned');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE lot_status_enum AS ENUM ('draft', 'active', 'paused', 'out_of_stock', 'deleted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE lot_delivery_type_enum AS ENUM ('auto', 'manual', 'coordinates');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE deal_status_enum AS ENUM ('created', 'paid', 'in_progress', 'waiting_confirmation', 'completed', 'canceled', 'dispute', 'refunded');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE transaction_type_enum AS ENUM ('deposit', 'purchase', 'sale', 'refund', 'withdrawal', 'commission', 'bonus', 'penalty');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE transaction_status_enum AS ENUM ('pending', 'completed', 'failed', 'canceled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE withdrawal_status_enum AS ENUM ('pending', 'processing', 'completed', 'rejected', 'canceled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE dispute_status_enum AS ENUM ('open', 'in_review', 'resolved', 'closed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_type_enum AS ENUM ('new_message', 'new_order', 'order_status', 'payment', 'review', 'system', 'price_alert');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. Create sellers table
CREATE TABLE IF NOT EXISTS sellers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status seller_status_enum NOT NULL DEFAULT 'pending',
    shop_name VARCHAR(120) NOT NULL,
    description TEXT,
    rating NUMERIC(3, 2) NOT NULL DEFAULT 0.00,
    total_sales INTEGER NOT NULL DEFAULT 0,
    total_reviews INTEGER NOT NULL DEFAULT 0,
    balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    commission_percent NUMERIC(5, 2) NOT NULL DEFAULT 10.00,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_sellers_user_id UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS ix_sellers_status_rating ON sellers(status, rating);

-- 4. Create lots table
CREATE TABLE IF NOT EXISTS lots (
    id SERIAL PRIMARY KEY,
    seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(12, 2) NOT NULL,
    currency_code VARCHAR(10) NOT NULL DEFAULT 'RUB',
    delivery_type lot_delivery_type_enum NOT NULL DEFAULT 'manual',
    stock_count INTEGER NOT NULL DEFAULT 0,
    reserved_count INTEGER NOT NULL DEFAULT 0,
    sold_count INTEGER NOT NULL DEFAULT 0,
    status lot_status_enum NOT NULL DEFAULT 'draft',
    auto_delivery_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    delivery_time_minutes INTEGER,
    is_featured BOOLEAN NOT NULL DEFAULT false,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_lots_product_seller_status ON lots(product_id, seller_id, status);
CREATE INDEX IF NOT EXISTS ix_lots_status_price ON lots(status, price);

-- 5. Create deals table
CREATE TABLE IF NOT EXISTS deals (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    buyer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    lot_id INTEGER NOT NULL REFERENCES lots(id) ON DELETE CASCADE,
    status deal_status_enum NOT NULL DEFAULT 'created',
    amount NUMERIC(12, 2) NOT NULL,
    commission_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    seller_amount NUMERIC(12, 2) NOT NULL,
    escrow_released BOOLEAN NOT NULL DEFAULT false,
    escrow_released_at TIMESTAMP WITH TIME ZONE,
    auto_complete_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    buyer_confirmed BOOLEAN NOT NULL DEFAULT false,
    buyer_confirmed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_deals_order_id UNIQUE (order_id)
);

CREATE INDEX IF NOT EXISTS ix_deals_buyer_status ON deals(buyer_id, status);
CREATE INDEX IF NOT EXISTS ix_deals_seller_status ON deals(seller_id, status);

-- 6. Create lot_stock_items table
CREATE TABLE IF NOT EXISTS lot_stock_items (
    id SERIAL PRIMARY KEY,
    lot_id INTEGER NOT NULL REFERENCES lots(id) ON DELETE CASCADE,
    data TEXT NOT NULL,
    is_sold BOOLEAN NOT NULL DEFAULT false,
    is_reserved BOOLEAN NOT NULL DEFAULT false,
    reserved_until TIMESTAMP WITH TIME ZONE,
    sold_at TIMESTAMP WITH TIME ZONE,
    deal_id INTEGER REFERENCES deals(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_lot_stock_items_lot_status ON lot_stock_items(lot_id, is_sold, is_reserved);

-- 7. Create deal_messages table
CREATE TABLE IF NOT EXISTS deal_messages (
    id SERIAL PRIMARY KEY,
    deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_text TEXT,
    media_id INTEGER REFERENCES media_files(id) ON DELETE SET NULL,
    is_system BOOLEAN NOT NULL DEFAULT false,
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_deal_messages_deal_created ON deal_messages(deal_id, created_at);

-- 8. Create deal_disputes table
CREATE TABLE IF NOT EXISTS deal_disputes (
    id SERIAL PRIMARY KEY,
    deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    initiator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    status dispute_status_enum NOT NULL DEFAULT 'open',
    admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    resolution TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_deal_disputes_deal_id UNIQUE (deal_id)
);

-- 9. Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_type transaction_type_enum NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency_code VARCHAR(10) NOT NULL DEFAULT 'RUB',
    status transaction_status_enum NOT NULL DEFAULT 'pending',
    balance_before NUMERIC(12, 2) NOT NULL,
    balance_after NUMERIC(12, 2) NOT NULL,
    description TEXT,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_transactions_user_type_created ON transactions(user_id, transaction_type, created_at);
CREATE INDEX IF NOT EXISTS ix_transactions_status ON transactions(status);

-- 10. Create seller_withdrawals table
CREATE TABLE IF NOT EXISTS seller_withdrawals (
    id SERIAL PRIMARY KEY,
    seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    currency_code VARCHAR(10) NOT NULL DEFAULT 'RUB',
    status withdrawal_status_enum NOT NULL DEFAULT 'pending',
    payment_method VARCHAR(50) NOT NULL,
    payment_details TEXT NOT NULL,
    processed_by_admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_seller_withdrawals_seller_status ON seller_withdrawals(seller_id, status);

-- 11. Create seller_reviews table
CREATE TABLE IF NOT EXISTS seller_reviews (
    id SERIAL PRIMARY KEY,
    seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    buyer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    text TEXT,
    status review_status_enum NOT NULL DEFAULT 'published',
    seller_reply TEXT,
    seller_replied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_seller_reviews_seller_status ON seller_reviews(seller_id, status);

-- 12. Create favorites table
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lot_id INTEGER NOT NULL REFERENCES lots(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_favorites_user_lot UNIQUE (user_id, lot_id)
);

CREATE INDEX IF NOT EXISTS ix_favorites_user_created ON favorites(user_id, created_at);

-- 13. Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type notification_type_enum NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_notifications_user_read_created ON notifications(user_id, is_read, created_at);

-- 14. Update alembic version
INSERT INTO alembic_version (version_num) VALUES ('20260414_000001')
ON CONFLICT (version_num) DO NOTHING;

-- Done!
SELECT 'Migration completed successfully!' as status;
