from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import SubscriptionStatus


class SubscriptionCreate(BaseModel):
    """Оформление абонемента ученику."""
    student_id: int
    plan_id: int
    start_date: date | None = None  # если не указана — сегодня


class SubscriptionUpdate(BaseModel):
    lessons_used: int | None = Field(None, ge=0)
    status: SubscriptionStatus | None = None
    end_date: date | None = None


class SubscriptionRead(BaseModel):
    id: int
    student_id: int
    plan_id: int | None
    lessons_total: int
    lessons_used: int
    lessons_remaining: int          # вычисляемое
    price_paid: float
    start_date: date
    end_date: date
    status: SubscriptionStatus
    student_name: str | None        # ФИО ученика для удобства
    plan_name: str | None           # название тарифа
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
