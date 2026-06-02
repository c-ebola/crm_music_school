import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SessionStatus(str, enum.Enum):
    scheduled = "scheduled"    # запланировано
    completed = "completed"    # проведено
    cancelled = "cancelled"    # отменено


class Session(Base):
    """Конкретное проведение занятия (строка расписания)."""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id"), nullable=False
    )
    room_id: Mapped[int | None] = mapped_column(
        ForeignKey("rooms.id", ondelete="SET NULL")
    )
    session_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        nullable=False, default=SessionStatus.scheduled,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    lesson: Mapped["Lesson"] = relationship("Lesson", lazy="joined")  # noqa: F821
    room: Mapped["Room | None"] = relationship("Room", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, lesson_id={self.lesson_id}, date={self.session_date})>"
