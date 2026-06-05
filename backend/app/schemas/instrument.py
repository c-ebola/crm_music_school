from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.branch import BranchRead


class InstrumentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    type: str | None = Field(None, max_length=50)
    branch_id: int | None = None
    is_active: bool = True


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    type: str | None = Field(None, max_length=50)
    branch_id: int | None = None
    is_active: bool | None = None


class InstrumentRead(InstrumentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    branch: BranchRead | None = None

    model_config = ConfigDict(from_attributes=True)
