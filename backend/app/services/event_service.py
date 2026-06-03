from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventStatus
from app.schemas.event import EventCreate, EventUpdate


async def list_events(db: AsyncSession, status: EventStatus | None = None) -> list[Event]:
    query = select(Event)
    if status is not None:
        query = query.where(Event.status == status)
    query = query.order_by(Event.id.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_event(db: AsyncSession, event_id: int) -> Event | None:
    result = await db.execute(select(Event).where(Event.id == event_id))
    return result.scalar_one_or_none()


async def create_event(db: AsyncSession, data: EventCreate) -> Event:
    event = Event(**data.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def update_event(db: AsyncSession, event_id: int, data: EventUpdate) -> Event | None:
    event = await get_event(db, event_id)
    if event is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    await db.commit()
    await db.refresh(event)
    return event
