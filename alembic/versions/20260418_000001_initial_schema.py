"""initial schema

Revision ID: 20260418_000001
Revises: None
Create Date: 2026-04-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260418_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop all existing enum types if they exist (cleanup from failed migrations)
    op.execute("DROP TYPE IF EXISTS seller_review_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS notification_type_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS dispute_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS withdrawal_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS transaction_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS transaction_type_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS deal_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS lot_delivery_type_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS lot_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS seller_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS payment_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS payment_provider_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS order_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS product_type_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS game_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS admin_role_enum CASCADE")
    
    # Create enums
    op.execute("CREATE TYPE admin_role_enum AS ENUM ('super_admin', 'moderator', 'support')")
    op.execute("CREATE TYPE game_enum AS ENUM ('brawl_stars', 'clash_royale', 'clash_of_clans', 'squad_busters')")
    op.execute("CREATE TYPE product_type_enum AS ENUM ('gems', 'gold', 'account', 'pass', 'other')")
    op.execute("CREATE TYPE order_status_enum AS ENUM ('pending', 'paid', 'processing', 'completed', 'canceled', 'refunded')")
    op.execute("CREATE TYPE payment_provider_enum AS ENUM ('yukassa', 'tinkoff', 'cloudpayments', 'cryptobot', 'telegram_stars', 'balance')")
    op.execute("CREATE TYPE payment_status_enum AS ENUM ('pending', 'processing', 'succeeded', 'failed', 'canceled', 'refunded')")
    op.execute("CREATE TYPE seller_status_enum AS ENUM ('pending', 'active', 'suspended', 'banned')")
    op.execute("CREATE TYPE lot_status_enum AS ENUM ('draft', 'active', 'paused', 'out_of_stock', 'deleted')")
    op.execute("CREATE TYPE lot_delivery_type_enum AS ENUM ('auto', 'manual', 'coordinates')")
    op.execute("CREATE TYPE deal_status_enum AS ENUM ('created', 'paid', 'in_progress', 'waiting_confirmation', 'completed', 'canceled', 'dispute', 'refunded')")
    op.execute("CREATE TYPE transaction_type_enum AS ENUM ('deposit', 'purchase', 'sale', 'refund', 'withdrawal', 'commission', 'bonus', 'penalty')")
    op.execute("CREATE TYPE transaction_status_enum AS ENUM ('pending', 'completed', 'failed', 'canceled')")
    op.execute("CREATE TYPE withdrawal_status_enum AS ENUM ('pending', 'processing', 'completed', 'rejected', 'canceled')")
    op.execute("CREATE TYPE dispute_status_enum AS ENUM ('open', 'in_review', 'resolved', 'closed')")
    op.execute("CREATE TYPE notification_type_enum AS ENUM ('new_message', 'new_order', 'order_status', 'payment', 'review', 'system', 'price_alert')")
    op.execute("CREATE TYPE seller_review_status_enum AS ENUM ('hidden', 'published', 'rejected')")
    
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
        sa.Column('role', sa.Enum('super_admin', 'moderator', 'support', name='admin_role_enum', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_admins_user_id')
    )
    
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

    
    # Create games table
    op.create_table('games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Enum('brawl_stars', 'clash_royale', 'clash_of_clans', 'squad_busters', name='game_enum', create_type=False), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_games_name')
    )
    
    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('product_type', sa.Enum('gems', 'gold', 'account', 'pass', 'other', name='product_type_enum', create_type=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_game_type_active', 'products', ['game_id', 'product_type', 'is_active'])
    
    # Create media_files table
    op.create_table('media_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_file_id', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('uploaded_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_file_id', name='uq_media_files_telegram_file_id')
    )
    
    # Create cart_items table
    op.create_table('cart_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cart_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column('price_at_add', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cart_id', 'product_id', name='uq_cart_items_cart_product')
    )
    
    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'paid', 'processing', 'completed', 'canceled', 'refunded', name='order_status_enum', create_type=False), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column('final_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('promo_code_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_orders_user_status_created', 'orders', ['user_id', 'status', 'created_at'])
    
    # Create order_items table
    op.create_table('order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price_per_unit', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.Enum('yukassa', 'tinkoff', 'cloudpayments', 'cryptobot', 'telegram_stars', 'balance', name='payment_provider_enum', create_type=False), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'succeeded', 'failed', 'canceled', 'refunded', name='payment_status_enum', create_type=False), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('provider_payment_id', sa.String(255), nullable=True),
        sa.Column('provider_response', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('payment_url', sa.String(1000), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payments_order_status', 'payments', ['order_id', 'status'])
    op.create_index('ix_payments_provider_payment_id', 'payments', ['provider_payment_id'])

    
    # Create sellers table
    op.create_table('sellers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'active', 'suspended', 'banned', name='seller_status_enum', create_type=False), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('shop_name', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rating', sa.Numeric(3, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column('total_sales', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('total_reviews', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('balance', sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column('commission_percent', sa.Numeric(5, 2), nullable=False, server_default=sa.text("10.00")),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_sellers_user_id')
    )
    op.create_index('ix_sellers_status_rating', 'sellers', ['status', 'rating'])
    
    # Create lots table
    op.create_table('lots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('delivery_type', sa.Enum('auto', 'manual', 'coordinates', name='lot_delivery_type_enum', create_type=False), nullable=False, server_default=sa.text("'manual'")),
        sa.Column('stock_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('reserved_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('sold_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('status', sa.Enum('draft', 'active', 'paused', 'out_of_stock', 'deleted', name='lot_status_enum', create_type=False), nullable=False, server_default=sa.text("'draft'")),
        sa.Column('auto_delivery_data', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('delivery_time_minutes', sa.Integer(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['seller_id'], ['sellers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lots_product_seller_status', 'lots', ['product_id', 'seller_id', 'status'])
    op.create_index('ix_lots_status_price', 'lots', ['status', 'price'])
    
    # Create deals table
    op.create_table('deals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('created', 'paid', 'in_progress', 'waiting_confirmation', 'completed', 'canceled', 'dispute', 'refunded', name='deal_status_enum', create_type=False), nullable=False, server_default=sa.text("'created'")),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('commission_amount', sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column('seller_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('escrow_released', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('escrow_released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_complete_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('buyer_confirmed', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('buyer_confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['seller_id'], ['sellers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lot_id'], ['lots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', name='uq_deals_order_id')
    )
    op.create_index('ix_deals_buyer_status', 'deals', ['buyer_id', 'status'])
    op.create_index('ix_deals_seller_status', 'deals', ['seller_id', 'status'])
    
    # Create lot_stock_items table
    op.create_table('lot_stock_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Text(), nullable=False),
        sa.Column('is_sold', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('is_reserved', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('reserved_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sold_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deal_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lot_id'], ['lots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lot_stock_items_lot_status', 'lot_stock_items', ['lot_id', 'is_sold', 'is_reserved'])
    
    # Create deal_messages table
    op.create_table('deal_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=True),
        sa.Column('media_id', sa.Integer(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['media_id'], ['media_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_deal_messages_deal_created', 'deal_messages', ['deal_id', 'created_at'])
    
    # Create deal_disputes table
    op.create_table('deal_disputes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('initiator_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('open', 'in_review', 'resolved', 'closed', name='dispute_status_enum', create_type=False), nullable=False, server_default=sa.text("'open'")),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['initiator_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('deal_id', name='uq_deal_disputes_deal_id')
    )

    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.Enum('deposit', 'purchase', 'sale', 'refund', 'withdrawal', 'commission', 'bonus', 'penalty', name='transaction_type_enum', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'canceled', name='transaction_status_enum', create_type=False), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('balance_before', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_after', sa.Numeric(12, 2), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_user_type_created', 'transactions', ['user_id', 'transaction_type', 'created_at'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])
    
    # Create seller_withdrawals table
    op.create_table('seller_withdrawals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'rejected', 'canceled', name='withdrawal_status_enum', create_type=False), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('payment_details', sa.Text(), nullable=False),
        sa.Column('processed_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['seller_id'], ['sellers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['processed_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seller_withdrawals_seller_status', 'seller_withdrawals', ['seller_id', 'status'])
    
    # Create seller_reviews table
    op.create_table('seller_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('hidden', 'published', 'rejected', name='seller_review_status_enum', create_type=False), nullable=False, server_default=sa.text("'published'")),
        sa.Column('seller_reply', sa.Text(), nullable=True),
        sa.Column('seller_replied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['seller_id'], ['sellers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_seller_reviews_rating_range')
    )
    op.create_index('ix_seller_reviews_seller_status', 'seller_reviews', ['seller_id', 'status'])
    
    # Create favorites table
    op.create_table('favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lot_id'], ['lots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'lot_id', name='uq_favorites_user_lot')
    )
    op.create_index('ix_favorites_user_created', 'favorites', ['user_id', 'created_at'])
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.Enum('new_message', 'new_order', 'order_status', 'payment', 'review', 'system', 'price_alert', name='notification_type_enum', create_type=False), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_user_read_created', 'notifications', ['user_id', 'is_read', 'created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('notifications')
    op.drop_table('favorites')
    op.drop_table('seller_reviews')
    op.drop_table('seller_withdrawals')
    op.drop_table('transactions')
    op.drop_table('deal_disputes')
    op.drop_table('deal_messages')
    op.drop_table('lot_stock_items')
    op.drop_table('deals')
    op.drop_table('lots')
    op.drop_table('sellers')
    op.drop_table('payments')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cart_items')
    op.drop_table('media_files')
    op.drop_table('products')
    op.drop_table('games')
    op.drop_table('carts')
    op.drop_table('admins')
    op.drop_table('users')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS seller_review_status_enum")
    op.execute("DROP TYPE IF EXISTS notification_type_enum")
    op.execute("DROP TYPE IF EXISTS dispute_status_enum")
    op.execute("DROP TYPE IF EXISTS withdrawal_status_enum")
    op.execute("DROP TYPE IF EXISTS transaction_status_enum")
    op.execute("DROP TYPE IF EXISTS transaction_type_enum")
    op.execute("DROP TYPE IF EXISTS deal_status_enum")
    op.execute("DROP TYPE IF EXISTS lot_delivery_type_enum")
    op.execute("DROP TYPE IF EXISTS lot_status_enum")
    op.execute("DROP TYPE IF EXISTS seller_status_enum")
    op.execute("DROP TYPE IF EXISTS payment_status_enum")
    op.execute("DROP TYPE IF EXISTS payment_provider_enum")
    op.execute("DROP TYPE IF EXISTS order_status_enum")
    op.execute("DROP TYPE IF EXISTS product_type_enum")
    op.execute("DROP TYPE IF EXISTS game_enum")
    op.execute("DROP TYPE IF EXISTS admin_role_enum")

