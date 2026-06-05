from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.branch import BranchRead


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    capacity: int | None = Field(None, ge=1)
    is_active: bool = True
    branch_id: int | None = None
    type: str | None = Field(None, max_length=50)


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    capacity: int | None = Field(None, ge=1)
    is_active: bool | None = None
    branch_id: int | None = None
    type: str | None = Field(None, max_length=50)


class RoomRead(RoomBase):
    id: int
    created_at: datetime
    updated_at: datetime
    branch: BranchRead | None = None

    model_config = ConfigDict(from_attributes=True)
