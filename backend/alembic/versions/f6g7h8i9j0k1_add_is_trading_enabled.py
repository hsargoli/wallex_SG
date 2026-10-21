"""add is_trading_enabled to users

Revision ID: f6g7h8i9j0k1
Revises: d4e5f6g7h8i9
Create Date: 2026-10-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'f6g7h8i9j0k1'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('is_trading_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False))

def downgrade():
    op.drop_column('users', 'is_trading_enabled')
