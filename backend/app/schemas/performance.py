from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PerformanceCreate(BaseModel):
    event_id: int
    teacher_id: int | None = None
    room_id: int | None = None
    notes: str | None = None


class PerformanceUpdate(BaseModel):
    teacher_id: int | None = None
    room_id: int | None = None
    notes: str | None = None


class PerformanceRead(BaseModel):
    id: int
    event_id: int
    teacher_id: int | None
    room_id: int | None
    notes: str | None
    teacher_name: str | None
    room_name: str | None
    event_title: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
