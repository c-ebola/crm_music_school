from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services import session_service

ALLOWED_TYPES = ("session", "event")


class ScheduleError(Exception):
    pass


class EntityNotFoundError(ScheduleError):
    pass


class UnsupportedEntityError(ScheduleError):
    pass


async def _resolve(db: AsyncSession, sch: Schedule) -> dict:
    """Полиморфное разрешение связи: подтягиваем сущность по entity_type."""
    session_obj = None
    if sch.entity_type == "session":
        session_obj = await session_service.get_session(db, sch.entity_id)
    # event — добавим, когда появится таблица events
    return {
        "id": sch.id,
        "entity_type": sch.entity_type,
        "entity_id": sch.entity_id,
        "quant": sch.quant,
        "session": session_obj,
        "created_at": sch.created_at,
        "updated_at": sch.updated_at,
    }


async def _validate_entity(db: AsyncSession, entity_type: str, entity_id: int) -> None:
    if entity_type not in ALLOWED_TYPES:
        raise ScheduleError("entity_type должен быть 'session' или 'event'")
    if entity_type == "session":
        if await session_service.get_session(db, entity_id) is None:
            raise EntityNotFoundError("Занятие (session) не найдено")
    elif entity_type == "event":
        raise UnsupportedEntityError("Мероприятия (events) ещё не реализованы")


async def list_schedule(db: AsyncSession, quant: int | None = None, entity_type: str | None = None) -> list[dict]:
    query = select(Schedule)
    if quant is not None:
        query = query.where(Schedule.quant == quant)
    if entity_type is not None:
        query = query.where(Schedule.entity_type == entity_type)
    query = query.order_by(Schedule.quant.asc())
    result = await db.execute(query)
    return [await _resolve(db, r) for r in result.scalars().all()]


async def get_schedule(db: AsyncSession, schedule_id: int) -> dict | None:
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sch = result.scalar_one_or_none()
    return await _resolve(db, sch) if sch else None


async def create_schedule(db: AsyncSession, data: ScheduleCreate) -> dict:
    await _validate_entity(db, data.entity_type, data.entity_id)
    sch = Schedule(entity_type=data.entity_type, entity_id=data.entity_id, quant=data.quant)
    db.add(sch)
    await db.commit()
    await db.refresh(sch)
    return await _resolve(db, sch)


async def update_schedule(db: AsyncSession, schedule_id: int, data: ScheduleUpdate) -> dict | None:
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sch = result.scalar_one_or_none()
    if sch is None:
        return None
    update = data.model_dump(exclude_unset=True)
    if "entity_type" in update or "entity_id" in update:
        await _validate_entity(
            db,
            update.get("entity_type", sch.entity_type),
            update.get("entity_id", sch.entity_id),
        )
    for field, value in update.items():
        setattr(sch, field, value)
    await db.commit()
    await db.refresh(sch)
    return await _resolve(db, sch)


async def delete_schedule(db: AsyncSession, schedule_id: int) -> bool:
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sch = result.scalar_one_or_none()
    if sch is None:
        return False
    await db.delete(sch)
    await db.commit()
    return True
