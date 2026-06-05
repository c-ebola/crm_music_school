from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.commission_member import CommissionRole


class CommissionMemberCreate(BaseModel):
    user_id: int
    role: CommissionRole = CommissionRole.member


class CommissionMemberRead(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    role: CommissionRole
    model_config = ConfigDict(from_attributes=True)


class CommissionCreate(BaseModel):
    name: str = Field(..., max_length=200)
    members: list[CommissionMemberCreate] = []


class CommissionUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)


class CommissionRead(BaseModel):
    id: int
    name: str
    members: list[CommissionMemberRead] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
