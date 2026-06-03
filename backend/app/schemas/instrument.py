from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InstrumentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    type: str | None = Field(None, max_length=50)
    branch: str | None = Field(None, max_length=100)
    is_active: bool = True


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    type: str | None = Field(None, max_length=50)
    branch: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class InstrumentRead(InstrumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
