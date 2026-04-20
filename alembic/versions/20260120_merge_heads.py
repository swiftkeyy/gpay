"""Merge dispute and review reply migrations

Revision ID: 20260120_merge_heads
Revises: 20260120_add_dispute_fields, 20260120_add_review_reply_fields
Create Date: 2026-01-20 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260120_merge_heads'
down_revision = ('20260120_add_dispute_fields', '20260120_add_review_reply_fields')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no changes needed
    pass


def downgrade():
    # This is a merge migration - no changes needed
    pass
