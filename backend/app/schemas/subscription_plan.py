from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    lessons_count: int = Field(..., ge=1)
    price: float = Field(..., ge=0)
    duration_days: int = Field(30, ge=1)
    is_active: bool = True
    description: str | None = None


class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass


class SubscriptionPlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    lessons_count: int | None = Field(None, ge=1)
    price: float | None = Field(None, ge=0)
    duration_days: int | None = Field(None, ge=1)
    is_active: bool | None = None
    description: str | None = None


class SubscriptionPlanRead(SubscriptionPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
