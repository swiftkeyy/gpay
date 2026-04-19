"""create all missing enums (lot_status_enum and others)

Revision ID: 20260419_130000
Revises: 66e77a681dd3
Create Date: 2026-04-19 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260419_130000'
down_revision = '66e77a681dd3'
branch_labels = None
depends_on = None


def upgrade():
    # === ЗАЩИТА ОТ ДУБЛИКАТОВ + создание всех enum ===
    op.execute("""
    DO $$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lot_status_enum') THEN
            CREATE TYPE lot_status_enum AS ENUM ('draft', 'active', 'paused', 'out_of_stock', 'deleted');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lot_delivery_type_enum') THEN
            CREATE TYPE lot_delivery_type_enum AS ENUM ('auto', 'manual', 'coordinates');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'deal_status_enum') THEN
            CREATE TYPE deal_status_enum AS ENUM ('created', 'paid', 'in_progress', 'waiting_confirmation', 'completed', 'canceled', 'dispute', 'refunded');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'seller_status_enum') THEN
            CREATE TYPE seller_status_enum AS ENUM ('pending', 'active', 'suspended', 'banned');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'dispute_status_enum') THEN
            CREATE TYPE dispute_status_enum AS ENUM ('open', 'in_review', 'resolved', 'closed');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_type_enum') THEN
            CREATE TYPE transaction_type_enum AS ENUM ('deposit', 'purchase', 'sale', 'refund', 'withdrawal', 'commission', 'bonus', 'penalty');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_status_enum') THEN
            CREATE TYPE transaction_status_enum AS ENUM ('pending', 'completed', 'failed', 'canceled');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'withdrawal_status_enum') THEN
            CREATE TYPE withdrawal_status_enum AS ENUM ('pending', 'processing', 'completed', 'rejected', 'canceled');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_type_enum') THEN
            CREATE TYPE notification_type_enum AS ENUM ('new_message', 'new_order', 'order_status', 'payment', 'review', 'system', 'price_alert');
        END IF;
    END
    $$;
    """)


def downgrade():
    op.execute("DROP TYPE IF EXISTS lot_status_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS lot_delivery_type_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS deal_status_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS seller_status_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS dispute_status_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS transaction_type_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS transaction_status_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS withdrawal_status_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS notification_type_enum CASCADE;")
