import enum
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.discipline import Discipline

from app.db.base import Base


class ContactType(str, enum.Enum):
    """Кто обращается."""
    parent = "parent"           # родитель
    student = "student"         # сам ученик 
    other = "other"             # другое



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


class StudentStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    finished = "finished"
    dropped = "dropped"


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
    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("disciplines.id"), nullable=False
    )
    level: Mapped[Level | None] = mapped_column(Enum(Level, name="level"))
    lesson_format: Mapped[LessonFormat | None] = mapped_column(
        Enum(LessonFormat, name="lesson_format")
    )
    branch_id: Mapped[int | None] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL")
    )

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

    is_student: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    enrollment_date: Mapped[date | None] = mapped_column(Date)
    student_status: Mapped[StudentStatus | None] = mapped_column(
        Enum(StudentStatus, name="student_status")
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
    
    teacher: Mapped["User | None"] = relationship("User", lazy="joined")  # noqa: F821
    discipline: Mapped["Discipline"] = relationship("Discipline", lazy="joined")
    branch: Mapped["Branch | None"] = relationship("Branch", lazy="joined")  # noqa: F821
