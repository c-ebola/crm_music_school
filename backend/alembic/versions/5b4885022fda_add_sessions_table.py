"""add sessions table

Revision ID: 5b4885022fda
Revises: b2e3654e11f1
Create Date: 2026-06-02 01:35:02.694326

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b4885022fda'
down_revision: Union[str, Sequence[str], None] = 'b2e3654e11f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # новый enum-тип создаём явно, в create_table — с create_type=False (чтобы не было дубля)
    session_status = postgresql.ENUM(
        'scheduled', 'completed', 'cancelled',
        name='session_status', create_type=False,
    )
    session_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True),
        sa.Column('session_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', session_status, nullable=False, server_default='scheduled'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id']),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('sessions')
    postgresql.ENUM(name='session_status').drop(op.get_bind(), checkfirst=True)