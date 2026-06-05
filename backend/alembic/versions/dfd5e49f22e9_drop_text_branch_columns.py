"""drop text branch columns

Revision ID: dfd5e49f22e9
Revises: 469b4d07f5b3
Create Date: 2026-06-05 21:18:48.455752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfd5e49f22e9'
down_revision: Union[str, Sequence[str], None] = '469b4d07f5b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_column('rooms', 'branch')
    op.drop_column('instruments', 'branch')
    op.drop_column('leads', 'preferred_branch')


def downgrade():
    op.add_column('leads', sa.Column('preferred_branch', sa.String(length=100), nullable=True))
    op.add_column('instruments', sa.Column('branch', sa.String(length=100), nullable=True))
    op.add_column('rooms', sa.Column('branch', sa.String(length=100), nullable=True))