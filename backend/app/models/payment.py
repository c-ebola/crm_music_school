import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentMethod(str, enum.Enum):
    cash = "cash"          # наличные
    card = "card"          # карта
    transfer = "transfer"  # перевод


class PaymentStatus(str, enum.Enum):
    pending = "pending"      # ожидает подтверждения
    confirmed = "confirmed"  # подтверждён
    rejected = "rejected"    # отклонён


class Payment(Base):
    """Оплата по абонементу."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"), nullable=False, default=PaymentMethod.cash
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.pending
    )
    comment: Mapped[str | None] = mapped_column(Text)

    # Подтверждение (используется на следующем шаге)
    confirmed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    subscription: Mapped["Subscription"] = relationship("Subscription", lazy="joined")  # noqa: F821
    confirmer: Mapped["User | None"] = relationship("User", lazy="joined")              # noqa: F821

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status})>"
