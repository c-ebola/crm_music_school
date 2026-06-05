from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Commission(Base):
    """Экзаменационная комиссия (панель экзаменаторов). Переиспользуется разными экзаменами."""
    __tablename__ = "commissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    members: Mapped[list["CommissionMember"]] = relationship(   # noqa: F821
        "CommissionMember", back_populates="commission",
        cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Commission(id={self.id}, name={self.name!r})>"
