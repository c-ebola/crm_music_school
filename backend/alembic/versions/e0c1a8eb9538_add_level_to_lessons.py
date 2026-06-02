"""add level to lessons

Revision ID: e0c1a8eb9538
Revises: 7026d9c8a15c
Create Date: 2026-06-02 16:35:27.029512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e0c1a8eb9538'
down_revision: Union[str, Sequence[str], None] = '7026d9c8a15c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    level_enum = postgresql.ENUM(
        'beginner', 'intermediate', 'advanced',
        name='level', create_type=False,
    )
    op.add_column('lessons', sa.Column('level', level_enum, nullable=True))


def downgrade() -> None:
    op.drop_column('lessons', 'level')