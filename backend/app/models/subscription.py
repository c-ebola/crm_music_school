import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SubscriptionStatus(str, enum.Enum):
    active = "active"        # действует
    expired = "expired"      # истёк срок
    used_up = "used_up"      # занятия закончились
    cancelled = "cancelled"  # отменён


class Subscription(Base):
    """Абонемент конкретного ученика (покупка тарифа из каталога)."""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ученик (запись leads с is_student=true)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    # тариф из каталога
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscription_plans.id", ondelete="SET NULL")
    )

    # снимок условий на момент покупки
    lessons_total: Mapped[int] = mapped_column(Integer, nullable=False)
    lessons_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # срок действия
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        nullable=False, default=SubscriptionStatus.active,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped["Lead"] = relationship("Lead", lazy="joined")          # noqa: F821
    plan: Mapped["SubscriptionPlan | None"] = relationship("SubscriptionPlan", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, student_id={self.student_id})>"
