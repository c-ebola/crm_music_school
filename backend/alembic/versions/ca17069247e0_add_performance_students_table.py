"""add performance_students table

Revision ID: ca17069247e0
Revises: fbeb2f3e5c01
Create Date: 2026-06-03 04:22:36.794067

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca17069247e0'
down_revision: Union[str, Sequence[str], None] = 'fbeb2f3e5c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'performance_students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('performance_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['performance_id'], ['performances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('performance_id', 'student_id', name='uq_performance_student'),
        sa.PrimaryKeyConstraint('id'),
    )

def downgrade() -> None:
    op.drop_table('performance_students')