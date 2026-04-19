"""add_payment_model_and_enums

Revision ID: d7750e4969b9
Revises: 4fa7210713d6
Create Date: 2026-04-20 02:33:23.746680

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7750e4969b9'
down_revision = '4fa7210713d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment_status enum
    op.execute("""
        CREATE TYPE payment_status_enum AS ENUM (
            'pending',
            'success',
            'failed',
            'canceled'
        )
    """)
    
    # Create payment_provider enum
    op.execute("""
        CREATE TYPE payment_provider_enum AS ENUM (
            'yookassa',
            'tinkoff',
            'cloudpayments',
            'cryptobot',
            'telegram_stars'
        )
    """)
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('payment_provider', sa.String(length=50), nullable=False),
        sa.Column('external_payment_id', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='RUB'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('payment_url', sa.Text(), nullable=True),
        sa.Column('provider_data', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_payments_order_id', 'payments', ['order_id'])
    op.create_index('ix_payments_external_payment_id', 'payments', ['external_payment_id'])
    op.create_index('ix_payments_status', 'payments', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_external_payment_id', table_name='payments')
    op.drop_index('ix_payments_order_id', table_name='payments')
    
    # Drop table
    op.drop_table('payments')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS payment_provider_enum')
    op.execute('DROP TYPE IF EXISTS payment_status_enum')
