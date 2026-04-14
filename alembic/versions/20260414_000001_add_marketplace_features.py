"""add marketplace features

Revision ID: 20260414_000001
Revises: 20260411_000001
Create Date: 2026-04-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260414_000001'
down_revision: Union[str, None] = '20260411_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add balance to users
    op.add_column('users', sa.Column('balance', sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")))
    
    # Create new enums
    op.execute("CREATE TYPE seller_status_enum AS ENUM ('pending', 'active', 'suspended', 'banned')")
    op.execute("CREATE TYPE lot_status_enum AS ENUM ('draft', 'active', 'paused', 'out_of_stock', 'deleted')")
    op.execute("CREATE TYPE lot_delivery_type_enum AS ENUM ('auto', 'manual', 'coordinates')")
    op.execute("CREATE TYPE deal_status_enum AS ENUM ('created', 'paid', 'in_progress', 'waiting_confirmation', 'completed', 'canceled', 'dispute', 'refunded')")
    op.execute("CREATE TYPE transaction_type_enum AS ENUM ('deposit', 'purchase', 'sale', 'refund', 'withdrawal', 'commission', 'bonus', 'penalty')")
    op.execute("CREATE TYPE transaction_status_enum AS ENUM ('pending', 'completed', 'failed', 'canceled')")
    op.execute("CREATE TYPE withdrawal_status_enum AS ENUM ('pending', 'processing', 'completed', 'rejected', 'canceled')")
    op.execute("CREATE TYPE dispute_status_enum AS ENUM ('open', 'in_review', 'resolved', 'closed')")
    op.execute("CREATE TYPE notification_type_enum AS ENUM ('new_message', 'new_order', 'order_status', 'payment', 'review', 'system', 'price_alert')")
    
    # Create sellers table
    op.create_table('sellers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'active', 'suspended', 'banned', name='seller_status_enum'), nullable=False, server_default=sa.text("'pending'")),
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
        sa.Column('delivery_type', sa.Enum('auto', 'manual', 'coordinates', name='lot_delivery_type_enum'), nullable=False, server_default=sa.text("'manual'")),
        sa.Column('stock_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('reserved_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('sold_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('status', sa.Enum('draft', 'active', 'paused', 'out_of_stock', 'deleted', name='lot_status_enum'), nullable=False, server_default=sa.text("'draft'")),
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
        sa.Column('status', sa.Enum('created', 'paid', 'in_progress', 'waiting_confirmation', 'completed', 'canceled', 'dispute', 'refunded', name='deal_status_enum'), nullable=False, server_default=sa.text("'created'")),
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
        sa.Column('status', sa.Enum('open', 'in_review', 'resolved', 'closed', name='dispute_status_enum'), nullable=False, server_default=sa.text("'open'")),
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
        sa.Column('transaction_type', sa.Enum('deposit', 'purchase', 'sale', 'refund', 'withdrawal', 'commission', 'bonus', 'penalty', name='transaction_type_enum'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'canceled', name='transaction_status_enum'), nullable=False, server_default=sa.text("'pending'")),
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
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'rejected', 'canceled', name='withdrawal_status_enum'), nullable=False, server_default=sa.text("'pending'")),
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
        sa.Column('status', sa.Enum('hidden', 'published', 'rejected', name='seller_review_status_enum'), nullable=False, server_default=sa.text("'published'")),
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
        sa.Column('notification_type', sa.Enum('new_message', 'new_order', 'order_status', 'payment', 'review', 'system', 'price_alert', name='notification_type_enum'), nullable=False),
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
    # Drop tables
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
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS notification_type_enum")
    op.execute("DROP TYPE IF EXISTS dispute_status_enum")
    op.execute("DROP TYPE IF EXISTS withdrawal_status_enum")
    op.execute("DROP TYPE IF EXISTS transaction_status_enum")
    op.execute("DROP TYPE IF EXISTS transaction_type_enum")
    op.execute("DROP TYPE IF EXISTS deal_status_enum")
    op.execute("DROP TYPE IF EXISTS lot_delivery_type_enum")
    op.execute("DROP TYPE IF EXISTS lot_status_enum")
    op.execute("DROP TYPE IF EXISTS seller_status_enum")
    
    # Remove balance from users
    op.drop_column('users', 'balance')
