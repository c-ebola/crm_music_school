"""merge students into leads with is_student flag

Revision ID: 6dd10a96dc1c
Revises: 6877c50422a2
Create Date: 2026-05-30 12:36:31.851949

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dd10a96dc1c'
down_revision: Union[str, Sequence[str], None] = '6877c50422a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # тип student_status уже существует (создан миграцией students) — переиспользуем
    student_status = postgresql.ENUM(
        'active', 'paused', 'finished', 'dropped',
        name='student_status', create_type=False,
    )
    op.add_column('leads', sa.Column('is_student', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('leads', sa.Column('teacher_id', sa.Integer(), nullable=True))
    op.add_column('leads', sa.Column('enrollment_date', sa.Date(), nullable=True))
    op.add_column('leads', sa.Column('student_status', student_status, nullable=True))
    op.create_foreign_key(
        'leads_teacher_id_fkey', 'leads', 'users',
        ['teacher_id'], ['id'], ondelete='SET NULL',
    )
    op.drop_table('students')


def downgrade() -> None:
    op.drop_constraint('leads_teacher_id_fkey', 'leads', type_='foreignkey')
    op.drop_column('leads', 'student_status')
    op.drop_column('leads', 'enrollment_date')
    op.drop_column('leads', 'teacher_id')
    op.drop_column('leads', 'is_student')
    # пересоздание таблицы students в downgrade опущено