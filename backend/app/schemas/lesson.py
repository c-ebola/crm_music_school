from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.discipline import DisciplineRead
from app.schemas.user import UserRead


class LessonBase(BaseModel):
    discipline_id: int
    teacher_id: int | None = None
    lesson_type: str | None = Field(None, max_length=50)
    max_students: int = Field(1, ge=1)


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    discipline_id: int | None = None
    teacher_id: int | None = None
    lesson_type: str | None = Field(None, max_length=50)
    max_students: int | None = Field(None, ge=1)


class LessonRead(LessonBase):
    id: int
    discipline: DisciplineRead | None
    teacher: UserRead | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
