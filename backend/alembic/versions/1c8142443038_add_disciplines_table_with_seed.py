"""add disciplines table with seed

Revision ID: 1c8142443038
Revises: f43bb36e69b0
Create Date: 2026-06-02 00:17:00.938602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c8142443038'
down_revision: Union[str, Sequence[str], None] = 'f43bb36e69b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'disciplines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.bulk_insert(
        sa.table(
            'disciplines',
            sa.column('name', sa.String),
            sa.column('is_active', sa.Boolean),
        ),
        [
            {'name': 'Фортепиано', 'is_active': True},
            {'name': 'Гитара', 'is_active': True},
            {'name': 'Вокал', 'is_active': True},
            {'name': 'Скрипка', 'is_active': True},
            {'name': 'Барабаны', 'is_active': True},
            {'name': 'Другое', 'is_active': True},
        ],
    )


def downgrade() -> None:
    op.drop_table('disciplines')