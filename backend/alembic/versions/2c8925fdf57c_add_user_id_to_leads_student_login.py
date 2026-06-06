"""add user_id to leads (student login)

Revision ID: 2c8925fdf57c
Revises: cf50ed3becd7
Create Date: 2026-06-06 04:03:14.510003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c8925fdf57c'
down_revision: Union[str, Sequence[str], None] = 'cf50ed3becd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('leads', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('leads_user_id_fkey', 'leads', 'users',
                          ['user_id'], ['id'], ondelete='SET NULL')

def downgrade() -> None:
    op.drop_constraint('leads_user_id_fkey', 'leads', type_='foreignkey')
    op.drop_column('leads', 'user_id')