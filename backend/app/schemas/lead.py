from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.lead import (
    ContactType, Discipline, Level, LessonFormat, LeadChannel, LeadStatus,
)


class LeadBase(BaseModel):
    """Общие поля лида."""
    # Контакт
    contact_full_name: str = Field(..., min_length=1, max_length=200)
    contact_type: ContactType = ContactType.parent
    email: EmailStr
    telegram: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)

    # Об ученике
    student_full_name: str | None = Field(None, max_length=200)
    student_age: int | None = Field(None, ge=3, le=99)
    discipline: Discipline
    level: Level | None = None
    lesson_format: LessonFormat | None = None
    preferred_branch: str | None = Field(None, max_length=100)

    # Источник
    channel: LeadChannel
    utm_campaign: str | None = Field(None, max_length=200)

    # Прочее
    manager_comment: str | None = None


class LeadCreate(LeadBase):
    """Что принимаем от клиента."""
    pass


class LeadRead(LeadBase):
    """Что отдаём клиенту."""
    id: int
    status: LeadStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)