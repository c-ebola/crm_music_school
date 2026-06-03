from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PerformanceStudentCreate(BaseModel):
    performance_id: int
    student_id: int
    instrument_id: int | None = None


class PerformanceStudentUpdate(BaseModel):
    instrument_id: int | None = None


class PerformanceStudentRead(BaseModel):
    id: int
    performance_id: int
    student_id: int
    instrument_id: int | None
    student_name: str | None
    instrument_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
