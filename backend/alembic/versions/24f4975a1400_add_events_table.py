"""add events table

Revision ID: 24f4975a1400
Revises: 51e96fbc6e95
Create Date: 2026-06-03 02:23:43.592932

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '24f4975a1400'
down_revision: Union[str, Sequence[str], None] = '51e96fbc6e95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    event_status = postgresql.ENUM(
        'planned', 'completed', 'cancelled',
        name='event_status', create_type=False,
    )
    event_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', event_status, nullable=False, server_default='planned'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('events')
    postgresql.ENUM(name='event_status').drop(op.get_bind(), checkfirst=True)
