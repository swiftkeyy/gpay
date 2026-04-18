"""add bot_settings table

Revision ID: 20260418_154000
Revises: 20260418_000001
Create Date: 2026-04-18 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260418_154000'
down_revision = '20260418_000001'
branch_labels = None
depends_on = None


def upgrade():
    # === BOT_SETTINGS ===
    op.create_table(
        'bot_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='uq_bot_settings_key')
    )
    op.create_index('ix_bot_settings_key', 'bot_settings', ['key'], unique=True)


def downgrade():
    op.drop_index('ix_bot_settings_key', table_name='bot_settings')
    op.drop_table('bot_settings')
