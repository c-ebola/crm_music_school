from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.performance import Performance
from app.schemas.performance import PerformanceCreate, PerformanceUpdate


class PerformanceError(Exception):
    pass


class EventNotFoundError(PerformanceError):
    pass


def _to_read(p: Performance) -> dict:
    teacher_name = None
    if p.teacher is not None:
        teacher_name = " ".join(filter(None, [p.teacher.last_name, p.teacher.first_name])) or None
    return {
        "id": p.id,
        "event_id": p.event_id,
        "teacher_id": p.teacher_id,
        "room_id": p.room_id,
        "notes": p.notes,
        "teacher_name": teacher_name,
        "room_name": p.room.name if p.room else None,
        "event_title": p.event.title if p.event else None,
        "created_at": p.created_at,
    }


async def list_performances(db: AsyncSession, event_id: int | None = None) -> list[dict]:
    query = select(Performance)
    if event_id is not None:
        query = query.where(Performance.event_id == event_id)
    query = query.order_by(Performance.created_at.asc())
    result = await db.execute(query)
    return [_to_read(p) for p in result.scalars().all()]


async def get_performance(db: AsyncSession, perf_id: int) -> dict | None:
    result = await db.execute(select(Performance).where(Performance.id == perf_id))
    p = result.scalar_one_or_none()
    return _to_read(p) if p else None


async def create_performance(db: AsyncSession, data: PerformanceCreate) -> dict:
    event = await db.get(Event, data.event_id)
    if event is None:
        raise EventNotFoundError("Мероприятие не найдено")
    perf = Performance(**data.model_dump())
    db.add(perf)
    await db.commit()
    await db.refresh(perf)
    return _to_read(perf)


async def update_performance(db: AsyncSession, perf_id: int, data: PerformanceUpdate) -> dict | None:
    result = await db.execute(select(Performance).where(Performance.id == perf_id))
    perf = result.scalar_one_or_none()
    if perf is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(perf, field, value)
    await db.commit()
    await db.refresh(perf)
    return _to_read(perf)


async def delete_performance(db: AsyncSession, perf_id: int) -> bool:
    result = await db.execute(select(Performance).where(Performance.id == perf_id))
    perf = result.scalar_one_or_none()
    if perf is None:
        return False
    await db.delete(perf)
    await db.commit()
    return True
