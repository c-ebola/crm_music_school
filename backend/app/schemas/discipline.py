from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DisciplineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True


class DisciplineCreate(DisciplineBase):
    pass


class DisciplineUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None


class DisciplineRead(DisciplineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
