from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.lead import Level
from app.db.base import Base


class Exam(Base):
    """Пул экзаменов: дисциплина + тип (сольфеджо/выступление) + комиссия."""
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)

    discipline_id: Mapped[int] = mapped_column(ForeignKey("disciplines.id"), nullable=False)
    exam_type: Mapped[str | None] = mapped_column(String(50))   # сольфеджо, выступление, ...
    max_students: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    level: Mapped[Level | None] = mapped_column(Enum(Level, name="level"))
    commission_id: Mapped[int | None] = mapped_column(
        ForeignKey("commissions.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    discipline: Mapped["Discipline"] = relationship("Discipline", lazy="joined")    # noqa: F821
    commission: Mapped["Commission | None"] = relationship("Commission", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Exam(id={self.id}, type={self.exam_type!r})>"
