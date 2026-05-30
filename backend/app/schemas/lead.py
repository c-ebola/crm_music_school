from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.lead import (
    ContactType, Discipline, LeadChannel, LeadStatus,
    LessonFormat, Level, StudentStatus,
)
from app.schemas.user import UserRead


class LeadBase(BaseModel):
    contact_full_name: str = Field(..., min_length=1, max_length=200)
    contact_type: ContactType = ContactType.parent
    email: EmailStr
    telegram: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    student_full_name: str | None = Field(None, max_length=200)
    student_age: int | None = Field(None, ge=3, le=99)
    discipline: Discipline
    level: Level | None = None
    lesson_format: LessonFormat | None = None
    preferred_branch: str | None = Field(None, max_length=100)
    channel: LeadChannel
    utm_campaign: str | None = Field(None, max_length=200)
    manager_comment: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadRead(LeadBase):
    id: int
    status: LeadStatus
    is_student: bool
    teacher_id: int | None
    enrollment_date: date | None
    student_status: StudentStatus | None
    teacher: UserRead | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConvertLeadRequest(BaseModel):
    """Данные для конверсии лида в ученика."""
    teacher_id: int | None = None
    enrollment_date: date
    full_name: str | None = None   # ФИО ученика; если None — берём из лида
    branch: str | None = None
