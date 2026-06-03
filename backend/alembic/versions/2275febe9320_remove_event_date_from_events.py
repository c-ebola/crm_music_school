"""remove event_date from events

Revision ID: 2275febe9320
Revises: 24f4975a1400
Create Date: 2026-06-03 02:30:43.969101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2275febe9320'
down_revision: Union[str, Sequence[str], None] = '24f4975a1400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('events', 'event_date')


def downgrade() -> None:
    op.add_column('events', sa.Column('event_date', sa.DateTime(timezone=True), nullable=True))