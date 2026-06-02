"""add lessons table

Revision ID: b2e3654e11f1
Revises: 469bd6c90af3
Create Date: 2026-06-02 01:21:40.869148

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e3654e11f1'
down_revision: Union[str, Sequence[str], None] = '469bd6c90af3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('discipline_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('lesson_type', sa.String(length=50), nullable=True),
        sa.Column('max_students', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['discipline_id'], ['disciplines.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('lessons')