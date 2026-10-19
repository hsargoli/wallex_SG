"""add wallex_trade_token to users

Revision ID: b2c3d4e5f6g7
Revises: 0e32c0249e19
Create Date: 2026-10-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = '0e32c0249e19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('wallex_trade_token_encrypted', sa.LargeBinary(), nullable=True))
    op.add_column('users', sa.Column('wallex_trade_connected_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'wallex_trade_connected_at')
    op.drop_column('users', 'wallex_trade_token_encrypted')
