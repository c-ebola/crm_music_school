from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.event import EventStatus


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    status: EventStatus | None = None
    description: str | None = None


class EventRead(EventBase):
    id: int
    status: EventStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
