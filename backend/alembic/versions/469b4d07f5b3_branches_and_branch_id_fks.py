"""branches and branch_id fks

Revision ID: 469b4d07f5b3
Revises: 0083c973c01a
Create Date: 2026-06-05 21:03:49.548066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '469b4d07f5b3'
down_revision: Union[str, Sequence[str], None] = '0083c973c01a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    branch_kind = postgresql.ENUM('school', 'venue', name='branch_kind')
    branch_kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'branches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=300), nullable=True),
        sa.Column('kind', postgresql.ENUM('school', 'venue', name='branch_kind', create_type=False),
                  nullable=False, server_default='school'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    for table in ('users', 'rooms', 'instruments', 'leads'):
        op.add_column(table, sa.Column('branch_id', sa.Integer(), nullable=True))
        op.create_foreign_key(f'fk_{table}_branch', table, 'branches',
                              ['branch_id'], ['id'], ondelete='SET NULL')


def downgrade():
    for table in ('leads', 'instruments', 'rooms', 'users'):
        op.drop_constraint(f'fk_{table}_branch', table, type_='foreignkey')
        op.drop_column(table, 'branch_id')
    op.drop_table('branches')
    postgresql.ENUM(name='branch_kind').drop(op.get_bind(), checkfirst=True)
