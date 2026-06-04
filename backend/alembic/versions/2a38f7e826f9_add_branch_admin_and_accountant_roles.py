"""add branch_admin and accountant roles

Revision ID: 2a38f7e826f9
Revises: ef8824cf6bfd
Create Date: 2026-06-04 09:41:34.021270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a38f7e826f9'
down_revision: Union[str, Sequence[str], None] = 'ef8824cf6bfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO roles (code, name) VALUES
            ('branch_admin', 'Администратор филиала'),
            ('accountant', 'Бухгалтер')
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM roles
        WHERE code IN ('branch_admin', 'accountant');
    """)