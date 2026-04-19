"""alter column types to use enums

Revision ID: 20260419_140000
Revises: 20260419_130000
Create Date: 2026-04-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260419_140000'
down_revision = '20260419_130000'
branch_labels = None
depends_on = None


def upgrade():
    # Alter lots table columns to use ENUM types
    op.execute("""
        ALTER TABLE lots 
        ALTER COLUMN status TYPE lot_status_enum USING status::lot_status_enum,
        ALTER COLUMN delivery_type TYPE lot_delivery_type_enum USING delivery_type::lot_delivery_type_enum;
    """)
    
    # Alter sellers table
    op.execute("""
        ALTER TABLE sellers 
        ALTER COLUMN status TYPE seller_status_enum USING status::seller_status_enum;
    """)
    
    # Alter deals table
    op.execute("""
        ALTER TABLE deals 
        ALTER COLUMN status TYPE deal_status_enum USING status::deal_status_enum;
    """)
    
    # Alter deal_disputes table
    op.execute("""
        ALTER TABLE deal_disputes 
        ALTER COLUMN status TYPE dispute_status_enum USING status::dispute_status_enum;
    """)
    
    # Alter transactions table
    op.execute("""
        ALTER TABLE transactions 
        ALTER COLUMN transaction_type TYPE transaction_type_enum USING transaction_type::transaction_type_enum,
        ALTER COLUMN status TYPE transaction_status_enum USING status::transaction_status_enum;
    """)
    
    # Alter seller_withdrawals table
    op.execute("""
        ALTER TABLE seller_withdrawals 
        ALTER COLUMN status TYPE withdrawal_status_enum USING status::withdrawal_status_enum;
    """)
    
    # Alter notifications table
    op.execute("""
        ALTER TABLE notifications 
        ALTER COLUMN notification_type TYPE notification_type_enum USING notification_type::notification_type_enum;
    """)


def downgrade():
    # Revert to VARCHAR types
    op.execute("ALTER TABLE lots ALTER COLUMN status TYPE VARCHAR(50);")
    op.execute("ALTER TABLE lots ALTER COLUMN delivery_type TYPE VARCHAR(50);")
    op.execute("ALTER TABLE sellers ALTER COLUMN status TYPE VARCHAR(50);")
    op.execute("ALTER TABLE deals ALTER COLUMN status TYPE VARCHAR(50);")
    op.execute("ALTER TABLE deal_disputes ALTER COLUMN status TYPE VARCHAR(50);")
    op.execute("ALTER TABLE transactions ALTER COLUMN transaction_type TYPE VARCHAR(50);")
    op.execute("ALTER TABLE transactions ALTER COLUMN status TYPE VARCHAR(50);")
    op.execute("ALTER TABLE seller_withdrawals ALTER COLUMN status TYPE VARCHAR(50);")
    op.execute("ALTER TABLE notifications ALTER COLUMN notification_type TYPE VARCHAR(50);")
