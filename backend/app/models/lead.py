import enum
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContactType(str, enum.Enum):
    """Кто обращается."""
    parent = "parent"           # родитель
    student = "student"         # сам ученик 
    other = "other"             # другое


class Discipline(str, enum.Enum):
    """Музыкальная дисциплина."""
    piano = "piano"
    guitar = "guitar"
    vocals = "vocals"
    violin = "violin"
    drums = "drums"
    other = "other"


class Level(str, enum.Enum):
    """Уровень подготовки ученика."""
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class LessonFormat(str, enum.Enum):
    """Формат занятий."""
    individual = "individual"   # индивидуальные
    group = "group"             # групповые
    online = "online"           # онлайн


class LeadChannel(str, enum.Enum):
    """Канал обращения."""
    website = "website"         # сайт
    phone = "phone"             # звонок
    social = "social"           # соцсети
    referral = "referral"       # сарафан
    advertising = "advertising" # реклама
    other = "other"


class LeadStatus(str, enum.Enum):
    """Статус лида в воронке продаж."""
    new = "new"                       # новый
    in_progress = "in_progress"       # в работе
    trial_scheduled = "trial_scheduled"   # назначен пробный
    converted = "converted"           # стал учеником
    rejected = "rejected"             # отказ


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Контакт
    contact_full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_type: Mapped[ContactType] = mapped_column(
        Enum(ContactType, name="contact_type"),
        nullable=False,
        default=ContactType.parent,
    )
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    telegram: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(50))

    # Об ученике
    student_full_name: Mapped[str | None] = mapped_column(String(200))
    student_age: Mapped[int | None] = mapped_column(Integer)
    discipline: Mapped[Discipline] = mapped_column(
        Enum(Discipline, name="discipline"),
        nullable=False,
    )
    level: Mapped[Level | None] = mapped_column(Enum(Level, name="level"))
    lesson_format: Mapped[LessonFormat | None] = mapped_column(
        Enum(LessonFormat, name="lesson_format")
    )
    preferred_branch: Mapped[str | None] = mapped_column(String(100))

    # Источник
    channel: Mapped[LeadChannel] = mapped_column(
        Enum(LeadChannel, name="lead_channel"),
        nullable=False,
    )
    utm_campaign: Mapped[str | None] = mapped_column(String(200))

    # Прочее
    manager_comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status"),
        nullable=False,
        default=LeadStatus.new,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, name={self.contact_full_name!r})>"