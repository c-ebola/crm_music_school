"""leads discipline enum to FK

Revision ID: 469bd6c90af3
Revises: a6d8e0bc71e6
Create Date: 2026-06-02 00:48:39.784688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '469bd6c90af3'
down_revision: Union[str, Sequence[str], None] = 'a6d8e0bc71e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1 новая колонка (пока nullable)
    op.add_column('leads', sa.Column('discipline_id', sa.Integer(), nullable=True))

    # 2 перенос данных: enum-код -> id дисциплины по названию
    op.execute("""
        UPDATE leads SET discipline_id = d.id
        FROM disciplines d
        WHERE d.name = CASE leads.discipline::text
            WHEN 'piano'  THEN 'Фортепиано'
            WHEN 'guitar' THEN 'Гитара'
            WHEN 'vocals' THEN 'Вокал'
            WHEN 'violin' THEN 'Скрипка'
            WHEN 'drums'  THEN 'Барабаны'
            WHEN 'other'  THEN 'Другое'
        END
    """)

    # 3 теперь делаем NOT NULL и вешаем FK
    op.alter_column('leads', 'discipline_id', nullable=False)
    op.create_foreign_key('leads_discipline_id_fkey', 'leads', 'disciplines', ['discipline_id'], ['id'])

    # 4 убираем старую enum-колонку и неиспользуемый тип
    op.drop_column('leads', 'discipline')
    op.execute("DROP TYPE IF EXISTS discipline")


def downgrade() -> None:
    discipline_enum = sa.Enum('piano', 'guitar', 'vocals', 'violin', 'drums', 'other', name='discipline')
    discipline_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('leads', sa.Column('discipline', discipline_enum, nullable=True))
    op.drop_constraint('leads_discipline_id_fkey', 'leads', type_='foreignkey')
    op.drop_column('leads', 'discipline')