import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CommissionRole(str, enum.Enum):
    chairman = "chairman"   # председатель комиссии
    member = "member"       # член комиссии


class CommissionMember(Base):
    """Член комиссии (админ/методист/учитель)."""
    __tablename__ = "commission_members"

    id: Mapped[int] = mapped_column(primary_key=True)

    commission_id: Mapped[int] = mapped_column(
        ForeignKey("commissions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[CommissionRole] = mapped_column(
        Enum(CommissionRole, name="commission_role"),
        nullable=False, default=CommissionRole.member,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("commission_id", "user_id", name="uq_commission_member"),
    )

    commission: Mapped["Commission"] = relationship("Commission", back_populates="members")  # noqa: F821
    user: Mapped["User"] = relationship("User", lazy="joined")                                # noqa: F821

    def __repr__(self) -> str:
        return f"<CommissionMember(commission_id={self.commission_id}, user_id={self.user_id}, role={self.role})>"
