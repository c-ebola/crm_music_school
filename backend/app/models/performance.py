from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Performance(Base):
    """Выступление на мероприятии (исполнители — через performance_students)."""
    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(primary_key=True)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    room_id: Mapped[int | None] = mapped_column(
        ForeignKey("rooms.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    event: Mapped["Event"] = relationship("Event", lazy="joined")        # noqa: F821
    teacher: Mapped["User | None"] = relationship("User", lazy="joined")  # noqa: F821
    room: Mapped["Room | None"] = relationship("Room", lazy="joined")     # noqa: F821

    def __repr__(self) -> str:
        return f"<Performance(id={self.id}, event_id={self.event_id})>"
