"""add exams, commission, exam_sessions, exam_session_students

Revision ID: 0083c973c01a
Revises: 2a38f7e826f9
Create Date: 2026-06-05 04:04:36.838643

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0083c973c01a'
down_revision: Union[str, Sequence[str], None] = '2a38f7e826f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    level = postgresql.ENUM('beginner', 'intermediate', 'advanced', name='level', create_type=False)

    op.create_table(
        'commissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'commission_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('commission_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('chairman', 'member', name='commission_role'), server_default='member', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['commission_id'], ['commissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('commission_id', 'user_id', name='uq_commission_member'),
    )
    op.create_table(
        'exams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('discipline_id', sa.Integer(), nullable=False),
        sa.Column('exam_type', sa.String(length=50), nullable=True),
        sa.Column('max_students', sa.Integer(), server_default='1', nullable=False),
        sa.Column('level', level, nullable=True),
        sa.Column('commission_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['discipline_id'], ['disciplines.id']),
        sa.ForeignKeyConstraint(['commission_id'], ['commissions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'exam_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('scheduled', 'completed', 'cancelled', name='exam_status'), server_default='scheduled', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id']),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'exam_session_students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_session_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('result', sa.Enum('pending', 'passed', 'failed', name='exam_result'), server_default='pending', nullable=False),
        sa.Column('result_level', level, nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['exam_session_id'], ['exam_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('exam_session_id', 'student_id', name='uq_exam_session_student'),
    )

    op.drop_constraint('schedule_entity_type_check', 'schedule', type_='check')
    op.create_check_constraint('schedule_entity_type_check', 'schedule',
                               "entity_type IN ('session','event','exam')")


def downgrade() -> None:
    op.drop_constraint('schedule_entity_type_check', 'schedule', type_='check')
    op.create_check_constraint('schedule_entity_type_check', 'schedule',
                               "entity_type IN ('session','event')")
    op.drop_table('exam_session_students')
    op.drop_table('exam_sessions')
    op.drop_table('exams')
    op.drop_table('commission_members')
    op.drop_table('commissions')
    op.execute("DROP TYPE IF EXISTS exam_result")
    op.execute("DROP TYPE IF EXISTS exam_status")
    op.execute("DROP TYPE IF EXISTS commission_role")
