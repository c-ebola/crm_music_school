from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import EventStatus
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services import event_service

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventRead])
async def get_events(status: EventStatus | None = None, db: AsyncSession = Depends(get_db)):
    return await event_service.list_events(db, status=status)


@router.get("/{event_id}", response_model=EventRead)
async def get_event_by_id(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await event_service.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def add_event(data: EventCreate, db: AsyncSession = Depends(get_db)):
    return await event_service.create_event(db, data)


@router.patch("/{event_id}", response_model=EventRead)
async def edit_event(event_id: int, data: EventUpdate, db: AsyncSession = Depends(get_db)):
    event = await event_service.update_event(db, event_id, data)
    if event is None:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event
