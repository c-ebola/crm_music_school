from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    """Фиксация оплаты по абонементу."""
    subscription_id: int
    amount: float = Field(..., gt=0)
    payment_date: date | None = None  # если не указана — сегодня
    method: PaymentMethod = PaymentMethod.cash
    comment: str | None = None


class PaymentUpdate(BaseModel):
    amount: float | None = Field(None, gt=0)
    payment_date: date | None = None
    method: PaymentMethod | None = None
    status: PaymentStatus | None = None
    comment: str | None = None


class PaymentRead(BaseModel):
    id: int
    subscription_id: int
    amount: float
    payment_date: date
    method: PaymentMethod
    status: PaymentStatus
    comment: str | None
    confirmed_by: int | None
    confirmed_at: datetime | None
    student_name: str | None     # ФИО ученика (через абонемент) — для удобства
    plan_name: str | None        # название тарифа
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
