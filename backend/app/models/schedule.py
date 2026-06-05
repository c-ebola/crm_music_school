from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Schedule(Base):
    """Полиморфный слот расписания: ссылается на session или event."""
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'session' | 'event'
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)              # день слота
    quant: Mapped[int] = mapped_column(Integer, nullable=False)          # тайм-слот

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("entity_type IN ('session','event','exam')", name="schedule_entity_type_check"),
    )

    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, type={self.entity_type}, entity_id={self.entity_id}, date={self.date}, quant={self.quant})>"
