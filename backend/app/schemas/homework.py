from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HomeworkCreate(BaseModel):
    teacher_id: int
    student_id: int
    description: str = Field(..., min_length=1)


class HomeworkUpdate(BaseModel):
    description: str | None = None
    comment: str | None = None
    is_completed: bool | None = None


class HomeworkRead(BaseModel):
    id: int
    teacher_id: int
    student_id: int
    description: str
    comment: str | None
    is_completed: bool
    teacher_name: str | None
    student_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
