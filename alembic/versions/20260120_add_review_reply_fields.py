"""add review reply and moderation fields

Revision ID: 20260120_add_review_reply_fields
Revises: bed2a74f0bcb
Create Date: 2026-01-20 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260120_add_review_reply_fields'
down_revision = 'bed2a74f0bcb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add photos field to reviews table
    op.add_column('reviews', sa.Column('photos', postgresql.ARRAY(sa.Integer()), nullable=True))
    
    # Add reply fields to reviews table
    op.add_column('reviews', sa.Column('reply_text', sa.Text(), nullable=True))
    op.add_column('reviews', sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add rejection_reason field to reviews table
    op.add_column('reviews', sa.Column('rejection_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove fields from reviews table
    op.drop_column('reviews', 'rejection_reason')
    op.drop_column('reviews', 'replied_at')
    op.drop_column('reviews', 'reply_text')
    op.drop_column('reviews', 'photos')
