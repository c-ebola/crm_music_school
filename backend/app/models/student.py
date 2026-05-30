import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.lead import Discipline


class StudentStatus(str, enum.Enum):
    """Статус ученика."""
    active = "active"           # учится
    paused = "paused"           # пауза
    finished = "finished"       # завершил
    dropped = "dropped"         # бросил


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    discipline: Mapped[Discipline] = mapped_column(
        Enum(Discipline, name="discipline"), nullable=False
    )
    branch: Mapped[str | None] = mapped_column(String(100))
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus, name="student_status"),
        nullable=False,
        default=StudentStatus.active,
    )

    # Преподаватель (FK на users)
    teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    # Связь с исходным лидом
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    teacher: Mapped["User | None"] = relationship("User", lazy="joined")  # noqa: F821
    lead: Mapped["Lead | None"] = relationship("Lead", lazy="joined")     # noqa: F821

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, name={self.full_name!r})>"
