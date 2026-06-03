from datetime import date as date_, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.session import SessionRead


class ScheduleCreate(BaseModel):
    entity_type: str = Field(..., pattern="^(session|event)$")
    entity_id: int
    date: date_
    quant: int = Field(..., ge=1)


class ScheduleUpdate(BaseModel):
    entity_type: str | None = Field(None, pattern="^(session|event)$")
    entity_id: int | None = None
    date: date_ | None = None
    quant: int | None = Field(None, ge=1)


class ScheduleRead(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    date: date_
    quant: int
    session: SessionRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduleAddSession(BaseModel):
    day: date_
    quant: int = Field(..., ge=1)
    lesson_id: int
    room_id: int | None = None
