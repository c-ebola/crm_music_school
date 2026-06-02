from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lesson(Base):
    """Шаблон/тип занятия (дисциплина + преподаватель + формат)."""
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)

    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("disciplines.id"), nullable=False
    )
    teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    lesson_type: Mapped[str | None] = mapped_column(String(50))  # individual / group / online
    max_students: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    discipline: Mapped["Discipline"] = relationship("Discipline", lazy="joined")  # noqa: F821
    teacher: Mapped["User | None"] = relationship("User", lazy="joined")          # noqa: F821

    def __repr__(self) -> str:
        return f"<Lesson(id={self.id}, discipline_id={self.discipline_id})>"
