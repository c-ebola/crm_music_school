"""seed default roles

Revision ID: 8feee964af21
Revises: 50daeb87c09b
Create Date: 2026-05-28 00:43:39.351809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8feee964af21'
down_revision: Union[str, Sequence[str], None] = '50daeb87c09b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавить начальный набор ролей."""
    op.execute("""
        INSERT INTO roles (code, name) VALUES
            ('admin', 'Администратор'),
            ('manager', 'Менеджер по продажам'),
            ('teacher', 'Преподаватель'),
            ('methodist', 'Методист')
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade() -> None:
    """Удалить начальный набор ролей."""
    op.execute("""
        DELETE FROM roles
        WHERE code IN ('admin', 'manager', 'teacher', 'methodist');
    """)