from datetime import datetime
import enum

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BranchKind(str, enum.Enum):
    """Тип точки: учебный филиал или концертная площадка."""
    school = "school"
    venue = "venue"


class Branch(Base):
    """Единый справочник филиалов и концертных площадок."""
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(300))
    kind: Mapped[BranchKind] = mapped_column(
        Enum(BranchKind, name="branch_kind"),
        nullable=False, default=BranchKind.school,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Branch(id={self.id}, name={self.name!r}, kind={self.kind})>"
