from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventStatus
from app.models.lesson import Lesson
from app.models.schedule import Schedule
from app.models.session import Session, SessionStatus
from app.schemas.schedule import (
    ScheduleAddSession, ScheduleAddEvent, ScheduleCreate, ScheduleUpdate,
)
from app.services import session_service, event_service

ALLOWED_TYPES = ("session", "event")


class ScheduleError(Exception):
    pass


class EntityNotFoundError(ScheduleError):
    pass


class UnsupportedEntityError(ScheduleError):
    pass


async def _resolve(db: AsyncSession, sch: Schedule) -> dict:
    session_obj = None
    event_obj = None
    if sch.entity_type == "session":
        session_obj = await session_service.get_session(db, sch.entity_id)
    elif sch.entity_type == "event":
        event_obj = await event_service.get_event(db, sch.entity_id)
    return {
        "id": sch.id,
        "entity_type": sch.entity_type,
        "entity_id": sch.entity_id,
        "date": sch.date,
        "quant": sch.quant,
        "session": session_obj,
        "event": event_obj,
        "created_at": sch.created_at,
        "updated_at": sch.updated_at,
    }

async def list_week_schedule(
    db: AsyncSession,
    week_start: date,
    teacher_id: int | None = None,
) -> list[dict]:
    end = week_start + timedelta(days=7)

    query = select(Schedule).where(
        Schedule.entity_type == "session",
        Schedule.date >= week_start,
        Schedule.date < end,
    )
    if teacher_id is not None:
        sess_ids = (
            select(Session.id)
            .join(Lesson, Session.lesson_id == Lesson.id)
            .where(Lesson.teacher_id == teacher_id)
        )
        query = query.where(Schedule.entity_id.in_(sess_ids))

    query = query.order_by(Schedule.date.asc(), Schedule.quant.asc())
    result = await db.execute(query)
    return [await _resolve(db, r) for r in result.scalars().all()]


async def list_schedule(
    db: AsyncSession,
    quant: int | None = None,
    entity_type: str | None = None,
    day: date | None = None,
) -> list[dict]:
    query = select(Schedule)
    if quant is not None:
        query = query.where(Schedule.quant == quant)
    if entity_type is not None:
        query = query.where(Schedule.entity_type == entity_type)
    if day is not None:
        query = query.where(Schedule.date == day)
    query = query.order_by(Schedule.date.asc(), Schedule.quant.asc())
    result = await db.execute(query)
    return [await _resolve(db, r) for r in result.scalars().all()]


async def get_schedule(db: AsyncSession, schedule_id: int) -> dict | None:
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sch = result.scalar_one_or_none()
    return await _resolve(db, sch) if sch else None


async def create_schedule(db: AsyncSession, data: ScheduleCreate) -> dict:
    await _validate_entity(db, data.entity_type, data.entity_id)
    sch = Schedule(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        date=data.date,
        quant=data.quant,
    )
    db.add(sch)
    await db.commit()
    await db.refresh(sch)
    return await _resolve(db, sch)


async def add_session_to_schedule(db: AsyncSession, data: ScheduleAddSession) -> dict:
    """Создать сессию и поставить её в расписание на день/квант."""
    lesson = await db.get(Lesson, data.lesson_id)
    if lesson is None:
        raise EntityNotFoundError("Занятие (тип) не найдено")

    session = Session(
        lesson_id=data.lesson_id,
        room_id=data.room_id,
        status=SessionStatus.scheduled,
    )
    db.add(session)
    await db.flush()  # получаем session.id

    sch = Schedule(
        entity_type="session",
        entity_id=session.id,
        date=data.day,
        quant=data.quant,
    )
    db.add(sch)
    await db.commit()
    await db.refresh(sch)
    return await _resolve(db, sch)

async def add_event_to_schedule(db: AsyncSession, data: ScheduleAddEvent) -> dict:
    """Создать концерт и поставить его в расписание на день/квант."""
    event = Event(
        title=data.title,
        description=data.description,
        status=EventStatus.planned,
    )
    db.add(event)
    await db.flush()  # получаем event.id

    sch = Schedule(
        entity_type="event",
        entity_id=event.id,
        date=data.day,
        quant=data.quant,
    )
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
