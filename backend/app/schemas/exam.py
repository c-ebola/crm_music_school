from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.lead import Level
from app.models.exam_session import ExamStatus
from app.models.exam_session_student import ExamResult


# пул экзаменов 
class ExamCreate(BaseModel):
    discipline_id: int
    exam_type: str | None = Field(None, max_length=50)
    max_students: int = Field(1, ge=1)
    level: Level | None = None
    commission_id: int | None = None


class ExamUpdate(BaseModel):
    discipline_id: int | None = None
    exam_type: str | None = None
    max_students: int | None = Field(None, ge=1)
    level: Level | None = None
    commission_id: int | None = None


class ExamRead(BaseModel):
    id: int
    discipline_id: int
    discipline_name: str | None = None
    exam_type: str | None
    max_students: int
    level: Level | None
    commission_id: int | None
    commission_name: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# результат ученика 
class ExamSessionStudentRead(BaseModel):
    id: int
    exam_session_id: int
    student_id: int
    student_name: str | None = None
    result: ExamResult
    result_level: Level | None
    score: int | None
    comment: str | None
    model_config = ConfigDict(from_attributes=True)


class ExamSessionStudentUpdate(BaseModel):
    result: ExamResult | None = None
    result_level: Level | None = None
    score: int | None = None
    comment: str | None = None
    apply_level: bool = True


class ExamStudentAdd(BaseModel):
    student_id: int


# проведение экзамена 
class ExamSessionUpdate(BaseModel):
    room_id: int | None = None
    status: ExamStatus | None = None


class ExamSessionRead(BaseModel):
    id: int
    exam_id: int
    room_id: int | None
    status: ExamStatus
    exam_type: str | None = None
    discipline_name: str | None = None
    commission_name: str | None = None
    room_name: str | None = None
    students: list[ExamSessionStudentRead] = []
    model_config = ConfigDict(from_attributes=True)
