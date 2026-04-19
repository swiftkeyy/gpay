"""add_boosted_until_to_lots

Revision ID: 4fa7210713d6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-20 02:12:35.662463

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4fa7210713d6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add boosted_until column to lots table
    op.add_column('lots', sa.Column('boosted_until', sa.DateTime(timezone=True), nullable=True))
    
    # Create index on boosted_until for efficient querying of boosted lots
    op.create_index('ix_lots_boosted_until', 'lots', ['boosted_until'], unique=False)
    
    # Add BOOST transaction type to transaction_type_enum
    op.execute("ALTER TYPE transaction_type_enum ADD VALUE IF NOT EXISTS 'boost'")


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_lots_boosted_until', table_name='lots')
    
    # Drop column
    op.drop_column('lots', 'boosted_until')
    
    # Note: Cannot remove enum value in PostgreSQL without recreating the enum type
    # This would require more complex migration logic to preserve existing data

