from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.session import SessionStatus
from app.schemas.lesson import LessonRead
from app.schemas.room import RoomRead


class SessionBase(BaseModel):
    lesson_id: int
    room_id: int | None = None
    session_date: datetime


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    lesson_id: int | None = None
    room_id: int | None = None
    session_date: datetime | None = None
    status: SessionStatus | None = None


class SessionRead(SessionBase):
    id: int
    status: SessionStatus
    lesson: LessonRead | None
    room: RoomRead | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
