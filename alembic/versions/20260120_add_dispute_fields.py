"""Add dispute fields and notification types

Revision ID: 20260120_add_dispute_fields
Revises: bed2a74f0bcb
Create Date: 2026-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260120_add_dispute_fields'
down_revision = 'bed2a74f0bcb'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to deal_disputes table
    op.add_column('deal_disputes', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('deal_disputes', sa.Column('admin_comment', sa.Text(), nullable=True))
    op.add_column('deal_disputes', sa.Column('resolved_by_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint for resolved_by_id
    op.create_foreign_key(
        'fk_deal_disputes_resolved_by_id_admins',
        'deal_disputes', 'admins',
        ['resolved_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add new notification types to enum
    op.execute("""
        ALTER TYPE notification_type_enum ADD VALUE IF NOT EXISTS 'dispute_opened';
        ALTER TYPE notification_type_enum ADD VALUE IF NOT EXISTS 'dispute_resolved';
    """)


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_deal_disputes_resolved_by_id_admins', 'deal_disputes', type_='foreignkey')
    
    # Remove columns from deal_disputes table
    op.drop_column('deal_disputes', 'resolved_by_id')
    op.drop_column('deal_disputes', 'admin_comment')
    op.drop_column('deal_disputes', 'description')
    
    # Note: Cannot remove enum values in PostgreSQL without recreating the enum
    # This would require more complex migration logic
