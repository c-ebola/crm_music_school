from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.session import SessionRead


class ScheduleCreate(BaseModel):
    entity_type: str = Field(..., pattern="^(session|event)$")
    entity_id: int
    quant: int = Field(..., ge=1)


class ScheduleUpdate(BaseModel):
    entity_type: str | None = Field(None, pattern="^(session|event)$")
    entity_id: int | None = None
    quant: int | None = Field(None, ge=1)


class ScheduleRead(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    quant: int
    session: SessionRead | None = None   # заполнено, если entity_type == 'session'
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScheduleAddSession(BaseModel):
    """Добавить занятие в квант расписания (создаёт сессию + запись)."""
    day: date
    quant: int = Field(..., ge=1)
    lesson_id: int
    room_id: int | None = None