"""move date from sessions to schedule

Revision ID: 51e96fbc6e95
Revises: e0c1a8eb9538
Create Date: 2026-06-03 01:58:00.127607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51e96fbc6e95'
down_revision: Union[str, Sequence[str], None] = 'e0c1a8eb9538'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. новая колонка в schedule
    op.add_column('schedule', sa.Column('date', sa.Date(), nullable=True))

    # 2. перенос: дата слота = дата сессии
    op.execute("""
        UPDATE schedule SET date = s.session_date::date
        FROM sessions s
        WHERE schedule.entity_type = 'session' AND schedule.entity_id = s.id
    """)
    # подстраховка для возможных «осиротевших» строк
    op.execute("UPDATE schedule SET date = CURRENT_DATE WHERE date IS NULL")

    # 3. NOT NULL и удаление старого поля из sessions
    op.alter_column('schedule', 'date', nullable=False)
    op.drop_column('sessions', 'session_date')


def downgrade() -> None:
    op.add_column('sessions', sa.Column('session_date', sa.DateTime(timezone=True), nullable=True))
    op.execute("""
        UPDATE sessions SET session_date = (sch.date + TIME '09:00')
        FROM schedule sch
        WHERE sch.entity_type = 'session' AND sch.entity_id = sessions.id
    """)
    op.drop_column('schedule', 'date')