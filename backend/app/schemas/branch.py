from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.branch import BranchKind


class BranchBase(BaseModel):
    name: str
    city: str | None = None
    address: str | None = None
    kind: BranchKind = BranchKind.school
    is_active: bool = True


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    kind: BranchKind | None = None
    is_active: bool | None = None


class BranchRead(BranchBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
