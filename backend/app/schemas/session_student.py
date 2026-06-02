from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionStudentCreate(BaseModel):
    session_id: int
    student_id: int
    subscription_id: int | None = None


class SessionStudentUpdate(BaseModel):
    attended: bool | None = None
    subscription_id: int | None = None


class SessionStudentRead(BaseModel):
    id: int
    session_id: int
    student_id: int
    subscription_id: int | None
    attended: bool
    student_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
