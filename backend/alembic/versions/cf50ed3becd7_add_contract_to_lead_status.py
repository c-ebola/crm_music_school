"""add contract to lead_status

Revision ID: cf50ed3becd7
Revises: dfd5e49f22e9
Create Date: 2026-06-06 02:08:50.225917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf50ed3becd7'
down_revision: Union[str, Sequence[str], None] = 'dfd5e49f22e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE lead_status ADD VALUE IF NOT EXISTS 'contract' BEFORE 'converted'")

def downgrade() -> None:
    pass
