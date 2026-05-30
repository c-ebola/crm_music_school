from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.lead import Discipline
from app.models.student import StudentStatus
from app.schemas.user import UserRead


class StudentBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    discipline: Discipline
    branch: str | None = Field(None, max_length=100)
    enrollment_date: date
    teacher_id: int | None = None


class StudentCreate(StudentBase):
    lead_id: int | None = None


class StudentUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=200)
    discipline: Discipline | None = None
    branch: str | None = Field(None, max_length=100)
    enrollment_date: date | None = None
    teacher_id: int | None = None
    status: StudentStatus | None = None


class StudentRead(StudentBase):
    id: int
    status: StudentStatus
    lead_id: int | None
    teacher: UserRead | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConvertLeadRequest(BaseModel):
    """Данные для конверсии лида в ученика (преподаватель + дата + опц. правки)."""
    teacher_id: int | None = None
    enrollment_date: date
    full_name: str | None = None   # если None — возьмём из лида
    branch: str | None = None
