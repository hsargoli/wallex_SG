"""add user_bot_configs table (phase A) - clean manual

Revision ID: fa01_add_user_bot_configs
Revises: f6g7h8i9j0k1
Create Date: 2026-10-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'fa01_add_user_bot_configs'
down_revision = 'f6g7h8i9j0k1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_bot_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bot_slug', sa.String(length=50), nullable=False),
        sa.Column('mode', sa.String(length=20), server_default=sa.text("'paper'"), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('capital_allocated', sa.Numeric(precision=20, scale=2), server_default=sa.text('0.00'), nullable=False),
        sa.Column('live_stage', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('daily_loss_limit_pct', sa.Numeric(precision=5, scale=2), server_default=sa.text('3.00'), nullable=False),
        sa.Column('kill_switch_auto', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('kill_switch_manual', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='user_bot_configs_user_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'bot_slug', name='uix_user_bot')
    )
    op.create_index(op.f('ix_user_bot_configs_user_id'), 'user_bot_configs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_bot_configs_user_id'), table_name='user_bot_configs')
    op.drop_table('user_bot_configs')
