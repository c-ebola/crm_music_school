from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discipline import Discipline
from app.schemas.discipline import DisciplineCreate, DisciplineUpdate


async def list_disciplines(db: AsyncSession, only_active: bool = False) -> list[Discipline]:
    query = select(Discipline)
    if only_active:
        query = query.where(Discipline.is_active.is_(True))
    query = query.order_by(Discipline.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_discipline(db: AsyncSession, discipline_id: int) -> Discipline | None:
    result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    return result.scalar_one_or_none()


async def create_discipline(db: AsyncSession, data: DisciplineCreate) -> Discipline:
    discipline = Discipline(**data.model_dump())
    db.add(discipline)
    await db.commit()
    await db.refresh(discipline)
    return discipline


async def update_discipline(db: AsyncSession, discipline_id: int, data: DisciplineUpdate) -> Discipline | None:
    discipline = await get_discipline(db, discipline_id)
    if discipline is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(discipline, field, value)
    await db.commit()
    await db.refresh(discipline)
    return discipline
