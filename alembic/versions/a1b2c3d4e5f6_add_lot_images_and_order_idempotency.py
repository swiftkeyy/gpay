"""add_lot_images_and_order_idempotency

Revision ID: a1b2c3d4e5f6
Revises: 20260419_140000
Create Date: 2026-04-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '20260419_140000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lot_images table
    op.create_table('lot_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lot_id'], ['lots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['media_id'], ['media_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lot_images_lot_sort', 'lot_images', ['lot_id', 'sort_order'])
    
    # Add idempotency_key column to orders table
    op.add_column('orders', sa.Column('idempotency_key', sa.String(255), nullable=True))
    op.create_index('ix_orders_idempotency_key', 'orders', ['idempotency_key'], unique=True)


def downgrade() -> None:
    # Drop idempotency_key column from orders table
    op.drop_index('ix_orders_idempotency_key', table_name='orders')
    op.drop_column('orders', 'idempotency_key')
    
    # Drop lot_images table
    op.drop_index('ix_lot_images_lot_sort', table_name='lot_images')
    op.drop_table('lot_images')
