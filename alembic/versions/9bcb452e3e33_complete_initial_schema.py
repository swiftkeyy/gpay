"""complete_initial_schema

Revision ID: 9bcb452e3e33
Revises: 
Create Date: 2026-04-18 20:09:59.228113

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '9bcb452e3e33'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(64), nullable=True),
        sa.Column('first_name', sa.String(120), nullable=True),
        sa.Column('last_name', sa.String(120), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('block_reason', sa.Text(), nullable=True),
        sa.Column('referred_by_user_id', sa.Integer(), nullable=True),
        sa.Column('personal_discount_percent', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('referral_code', sa.String(32), nullable=True),
        sa.Column('balance', sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['referred_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id', name='uq_users_telegram_id'),
        sa.UniqueConstraint('referral_code')
    )
    op.create_index('ix_users_blocked_created', 'users', ['is_blocked', 'created_at'])
    
    # Create admins table
    op.create_table('admins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_admins_user_id')
    )
    op.execute("ALTER TABLE admins ADD CONSTRAINT ck_admins_role CHECK (role::text = ANY (ARRAY['super_admin'::text, 'moderator'::text, 'support'::text]))")
    
    # Create media_files table (must be before games because games references it)
    op.create_table('media_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_file_id', sa.String(255), nullable=False),
        sa.Column('file_unique_id', sa.String(255), nullable=False),
        sa.Column('media_type', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('alt_text', sa.String(255), nullable=True),
        sa.Column('created_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_unique_id', name='uq_media_files_file_unique_id')
    )
    op.execute("ALTER TABLE media_files ADD CONSTRAINT ck_media_files_media_type CHECK (media_type::text = ANY (ARRAY['photo'::text, 'video'::text, 'document'::text]))")
    op.execute("ALTER TABLE media_files ADD CONSTRAINT ck_media_files_entity_type CHECK (entity_type::text = ANY (ARRAY['game'::text, 'category'::text, 'product'::text, 'broadcast'::text]))")
    
    # Create games table
    op.create_table('games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(['image_id'], ['media_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_games_slug')
    )
    op.create_index('ix_games_active_sort', 'games', ['is_active', 'sort_order'])
    
    # Create categories table
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['image_id'], ['media_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'slug', name='uq_categories_game_slug')
    )
    op.create_index('ix_categories_game_active_sort', 'categories', ['game_id', 'is_active', 'sort_order'])

    
    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_id', sa.Integer(), nullable=True),
        sa.Column('fulfillment_type', sa.String(50), nullable=False, server_default=sa.text("'manual'")),
        sa.Column('requires_player_id', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('requires_nickname', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('requires_region', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('requires_manual_review', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('requires_screenshot', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('extra_fields_schema_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['image_id'], ['media_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'slug', name='uq_products_game_slug')
    )
    op.create_index('ix_products_category_active_sort', 'products', ['category_id', 'is_active', 'sort_order'])
    op.execute("ALTER TABLE products ADD CONSTRAINT ck_products_fulfillment_type CHECK (fulfillment_type::text = ANY (ARRAY['manual'::text, 'auto'::text, 'api'::text]))")
    
    # Create prices table
    op.create_table('prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('base_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('discounted_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('changed_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prices_product_active_period', 'prices', ['product_id', 'is_active', 'starts_at', 'ends_at'])
    
    # Create carts table
    op.create_table('carts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_carts_user_id')
    )
    
    # Create cart_items table
    op.create_table('cart_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cart_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cart_id', 'product_id', name='uq_cart_items_cart_product')
    )
    
    # Create promo_codes table
    op.create_table('promo_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('promo_type', sa.String(50), nullable=False),
        sa.Column('value', sa.Numeric(12, 2), nullable=False),
        sa.Column('max_usages', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('only_new_users', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_promo_codes_code')
    )
    op.create_index('ix_promo_codes_active_dates', 'promo_codes', ['is_active', 'starts_at', 'ends_at'])
    op.execute("ALTER TABLE promo_codes ADD CONSTRAINT ck_promo_codes_promo_type CHECK (promo_type::text = ANY (ARRAY['percentage'::text, 'fixed'::text]))")
    
    # Create promo_code_usages table
    op.create_table('promo_code_usages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('promo_code_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    
    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(32), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'new'")),
        sa.Column('subtotal_amount', sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column('discount_amount', sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('promo_code_id', sa.Integer(), nullable=True),
        sa.Column('payment_provider', sa.String(50), nullable=False, server_default=sa.text("'manual'")),
        sa.Column('payment_external_id', sa.String(255), nullable=True),
        sa.Column('fulfillment_type', sa.String(50), nullable=False, server_default=sa.text("'manual'")),
        sa.Column('customer_data_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('admin_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number', name='uq_orders_order_number')
    )
    op.create_index('ix_orders_user_status_created', 'orders', ['user_id', 'status', 'created_at'])
    op.execute("ALTER TABLE orders ADD CONSTRAINT ck_orders_status CHECK (status::text = ANY (ARRAY['new'::text, 'pending_payment'::text, 'paid'::text, 'processing'::text, 'completed'::text, 'canceled'::text, 'refunded'::text]))")
    op.execute("ALTER TABLE orders ADD CONSTRAINT ck_orders_payment_provider CHECK (payment_provider::text = ANY (ARRAY['manual'::text, 'yukassa'::text, 'tinkoff'::text, 'cryptobot'::text, 'telegram_stars'::text, 'balance'::text]))")
    op.execute("ALTER TABLE orders ADD CONSTRAINT ck_orders_fulfillment_type CHECK (fulfillment_type::text = ANY (ARRAY['manual'::text, 'auto'::text, 'api'::text]))")
    
    # Update promo_code_usages foreign key
    op.create_foreign_key('fk_promo_code_usages_order_id', 'promo_code_usages', 'orders', ['order_id'], ['id'], ondelete='SET NULL')
    
    # Create order_items table
    op.create_table('order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('title_snapshot', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('fulfillment_type', sa.String(50), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute("ALTER TABLE order_items ADD CONSTRAINT ck_order_items_fulfillment_type CHECK (fulfillment_type::text = ANY (ARRAY['manual'::text, 'auto'::text, 'api'::text]))")
    
    # Create order_status_history table
    op.create_table('order_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('old_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('changed_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_order_status_history_order_created', 'order_status_history', ['order_id', 'created_at'])
    op.execute("ALTER TABLE order_status_history ADD CONSTRAINT ck_order_status_history_old_status CHECK (old_status IS NULL OR old_status::text = ANY (ARRAY['new'::text, 'pending_payment'::text, 'paid'::text, 'processing'::text, 'completed'::text, 'canceled'::text, 'refunded'::text]))")
    op.execute("ALTER TABLE order_status_history ADD CONSTRAINT ck_order_status_history_new_status CHECK (new_status::text = ANY (ARRAY['new'::text, 'pending_payment'::text, 'paid'::text, 'processing'::text, 'completed'::text, 'canceled'::text, 'refunded'::text]))")
    
    # Create reviews table
    op.create_table('reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'hidden'")),
        sa.Column('moderated_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['moderated_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_reviews_rating_range')
    )
    op.create_index('ix_reviews_status_created', 'reviews', ['status', 'created_at'])
    op.execute("ALTER TABLE reviews ADD CONSTRAINT ck_reviews_status CHECK (status::text = ANY (ARRAY['hidden'::text, 'published'::text, 'rejected'::text]))")
    
    # Create referrals table
    op.create_table('referrals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('referrer_user_id', sa.Integer(), nullable=False),
        sa.Column('referred_user_id', sa.Integer(), nullable=False),
        sa.Column('referral_code', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['referrer_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['referred_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('referred_user_id', name='uq_referrals_referred_user_id')
    )
    
    # Create referral_rewards table
    op.create_table('referral_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('referral_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('reward_type', sa.String(50), nullable=False),
        sa.Column('reward_value', sa.Numeric(12, 2), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['referral_id'], ['referrals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute("ALTER TABLE referral_rewards ADD CONSTRAINT ck_referral_rewards_reward_type CHECK (reward_type::text = ANY (ARRAY['percentage'::text, 'fixed'::text]))")

    
    # Create bot_settings table
    op.create_table('bot_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(120), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='uq_bot_settings_key')
    )
    
    # Create broadcasts table
    op.create_table('broadcasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('image_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'draft'")),
        sa.Column('target_filter_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('send_hash', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['image_id'], ['media_files.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('send_hash', name='uq_broadcasts_send_hash')
    )
    op.execute("ALTER TABLE broadcasts ADD CONSTRAINT ck_broadcasts_status CHECK (status::text = ANY (ARRAY['draft'::text, 'scheduled'::text, 'sending'::text, 'sent'::text, 'failed'::text]))")
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('old_values_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('new_values_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_entity_created', 'audit_logs', ['entity_type', 'created_at'])
    op.execute("ALTER TABLE audit_logs ADD CONSTRAINT ck_audit_logs_action CHECK (action::text = ANY (ARRAY['create'::text, 'update'::text, 'delete'::text, 'restore'::text]))")
    op.execute("ALTER TABLE audit_logs ADD CONSTRAINT ck_audit_logs_entity_type CHECK (entity_type::text = ANY (ARRAY['game'::text, 'category'::text, 'product'::text, 'broadcast'::text, 'user'::text, 'order'::text, 'promo_code'::text]))")
    
    # Create user_blocks table
    op.create_table('user_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('blocked_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('scope', sa.String(50), nullable=False, server_default=sa.text("'full'")),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['blocked_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_blocks_user_scope', 'user_blocks', ['user_id', 'scope'])
    op.execute("ALTER TABLE user_blocks ADD CONSTRAINT ck_user_blocks_scope CHECK (scope::text = ANY (ARRAY['full'::text, 'orders'::text, 'reviews'::text]))")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_blocks')
    op.drop_table('audit_logs')
    op.drop_table('broadcasts')
    op.drop_table('bot_settings')
    op.drop_table('referral_rewards')
    op.drop_table('referrals')
    op.drop_table('reviews')
    op.drop_table('order_status_history')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('promo_code_usages')
    op.drop_table('promo_codes')
    op.drop_table('cart_items')
    op.drop_table('carts')
    op.drop_table('prices')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('games')
    op.drop_table('media_files')
    op.drop_table('admins')
    op.drop_table('users')
