from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: int
    actor_user_id: int | None = None
    actor_name: str | None = None
    actor_role: str | None = None
    actor_branch: str | None = None
    branch_id: int | None = None
    method: str
    path: str
    action: str | None = None
    status_code: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)