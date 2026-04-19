"""add_p2p_marketplace_tables

Revision ID: 66e77a681dd3
Revises: 9bcb452e3e33
Create Date: 2026-04-19 12:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '66e77a681dd3'
down_revision = '9bcb452e3e33'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sellers table
    op.create_table('sellers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'pending'")),
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
    op.execute("ALTER TABLE sellers ADD CONSTRAINT ck_sellers_status CHECK (status::text = ANY (ARRAY['pending'::text, 'active'::text, 'suspended'::text, 'banned'::text]))")
    
    # Create lots table
    op.create_table('lots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('delivery_type', sa.String(50), nullable=False, server_default=sa.text("'manual'")),
        sa.Column('stock_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('reserved_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('sold_count', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'draft'")),
        sa.Column('auto_delivery_data', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('delivery_time_minutes', sa.Integer(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(['seller_id'], ['sellers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lots_product_seller_status', 'lots', ['product_id', 'seller_id', 'status'])
    op.create_index('ix_lots_status_price', 'lots', ['status', 'price'])
    op.execute("ALTER TABLE lots ADD CONSTRAINT ck_lots_delivery_type CHECK (delivery_type::text = ANY (ARRAY['manual'::text, 'auto'::text, 'instant'::text]))")
    op.execute("ALTER TABLE lots ADD CONSTRAINT ck_lots_status CHECK (status::text = ANY (ARRAY['draft'::text, 'active'::text, 'out_of_stock'::text, 'suspended'::text, 'deleted'::text]))")
    
    # Create deals table
    op.create_table('deals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'created'")),
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
    op.execute("ALTER TABLE deals ADD CONSTRAINT ck_deals_status CHECK (status::text = ANY (ARRAY['created'::text, 'paid'::text, 'in_progress'::text, 'waiting_confirmation'::text, 'completed'::text, 'disputed'::text, 'canceled'::text, 'refunded'::text]))")
    
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
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'open'")),
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
    op.execute("ALTER TABLE deal_disputes ADD CONSTRAINT ck_deal_disputes_status CHECK (status::text = ANY (ARRAY['open'::text, 'investigating'::text, 'resolved'::text, 'closed'::text]))")
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'pending'")),
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
    op.execute("ALTER TABLE transactions ADD CONSTRAINT ck_transactions_transaction_type CHECK (transaction_type::text = ANY (ARRAY['deposit'::text, 'withdrawal'::text, 'purchase'::text, 'refund'::text, 'commission'::text, 'payout'::text, 'bonus'::text, 'penalty'::text]))")
    op.execute("ALTER TABLE transactions ADD CONSTRAINT ck_transactions_status CHECK (status::text = ANY (ARRAY['pending'::text, 'completed'::text, 'failed'::text, 'canceled'::text]))")
    
    # Create seller_withdrawals table
    op.create_table('seller_withdrawals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency_code', sa.String(10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'pending'")),
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
    op.execute("ALTER TABLE seller_withdrawals ADD CONSTRAINT ck_seller_withdrawals_status CHECK (status::text = ANY (ARRAY['pending'::text, 'processing'::text, 'completed'::text, 'failed'::text, 'canceled'::text]))")
    
    # Create seller_reviews table
    op.create_table('seller_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'published'")),
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
    op.execute("ALTER TABLE seller_reviews ADD CONSTRAINT ck_seller_reviews_status CHECK (status::text = ANY (ARRAY['hidden'::text, 'published'::text, 'rejected'::text]))")
    
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
        sa.Column('notification_type', sa.String(50), nullable=False),
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
    op.execute("ALTER TABLE notifications ADD CONSTRAINT ck_notifications_notification_type CHECK (notification_type::text = ANY (ARRAY['order'::text, 'deal'::text, 'payment'::text, 'review'::text, 'system'::text, 'promo'::text]))")


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
