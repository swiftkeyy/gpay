"""Add delivered_at field to deals table

Revision ID: bed2a74f0bcb
Revises: d7750e4969b9
Create Date: 2026-04-20 03:09:25.926740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bed2a74f0bcb'
down_revision = 'd7750e4969b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add delivered_at column to deals table
    op.add_column('deals', sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove delivered_at column from deals table
    op.drop_column('deals', 'delivered_at')
