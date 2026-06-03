from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Homework(Base):
    """Домашнее задание: преподаватель (users) -> ученик (leads)."""
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True)

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    teacher: Mapped["User"] = relationship("User", lazy="joined")   # noqa: F821
    student: Mapped["Lead"] = relationship("Lead", lazy="joined")   # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Homework(id={self.id}, teacher_id={self.teacher_id}, "
            f"student_id={self.student_id}, done={self.is_completed})>"
        )
