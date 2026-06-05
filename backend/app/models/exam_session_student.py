import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.lead import Level
from app.db.base import Base


class ExamResult(str, enum.Enum):
    pending = "pending"    # ещё не оценён
    passed = "passed"      # сдал
    failed = "failed"      # не сдал


class ExamSessionStudent(Base):
    """Результат ученика на экзамене (аналог session_students, но со статусом сдачи и уровнем)."""
    __tablename__ = "exam_session_students"

    id: Mapped[int] = mapped_column(primary_key=True)

    exam_session_id: Mapped[int] = mapped_column(
        ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    result: Mapped[ExamResult] = mapped_column(
        Enum(ExamResult, name="exam_result"),
        nullable=False, default=ExamResult.pending,
    )
    result_level: Mapped[Level | None] = mapped_column(Enum(Level, name="level"))
    score: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("exam_session_id", "student_id", name="uq_exam_session_student"),
    )

    student: Mapped["Lead"] = relationship("Lead", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ExamSessionStudent(exam_session_id={self.exam_session_id}, student_id={self.student_id}, result={self.result})>"
