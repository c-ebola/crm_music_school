import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExamStatus(str, enum.Enum):
    scheduled = "scheduled"    # назначен
    completed = "completed"    # проведён
    cancelled = "cancelled"    # отменён


class ExamSession(Base):
    """Конкретное проведение экзамена (строка расписания, entity_type='exam')."""
    __tablename__ = "exam_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"))
    status: Mapped[ExamStatus] = mapped_column(
        Enum(ExamStatus, name="exam_status"),
        nullable=False, default=ExamStatus.scheduled,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    exam: Mapped["Exam"] = relationship("Exam", lazy="joined")         # noqa: F821
    room: Mapped["Room | None"] = relationship("Room", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ExamSession(id={self.id}, exam_id={self.exam_id})>"
