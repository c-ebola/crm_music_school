from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PerformanceStudent(Base):
    """Исполнитель выступления (M2M ученики ↔ выступления) + его инструмент."""
    __tablename__ = "performance_students"

    id: Mapped[int] = mapped_column(primary_key=True)

    performance_id: Mapped[int] = mapped_column(
        ForeignKey("performances.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[int | None] = mapped_column(
        ForeignKey("instruments.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("performance_id", "student_id", name="uq_performance_student"),
    )

    student: Mapped["Lead"] = relationship("Lead", lazy="joined")              # noqa: F821
    instrument: Mapped["Instrument | None"] = relationship("Instrument", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PerformanceStudent(id={self.id}, performance_id={self.performance_id}, student_id={self.student_id})>"
