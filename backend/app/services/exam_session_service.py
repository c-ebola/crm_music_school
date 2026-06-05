from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import Exam
from app.models.exam_session import ExamSession, ExamStatus
from app.models.exam_session_student import ExamSessionStudent, ExamResult
from app.models.lead import Lead
from app.schemas.exam import ExamSessionStudentUpdate, ExamSessionUpdate


class ExamSessionError(Exception):
    pass


def _fio(u) -> str | None:
    if u is None:
        return None
    return " ".join(filter(None, [u.last_name, u.first_name])) or None


def _student_read(es: ExamSessionStudent) -> dict:
    name = None
    if es.student is not None:
        name = es.student.student_full_name or es.student.contact_full_name
    return {
        "id": es.id,
        "exam_session_id": es.exam_session_id,
        "student_id": es.student_id,
        "student_name": name,
        "result": es.result,
        "result_level": es.result_level,
        "score": es.score,
        "comment": es.comment,
    }


def _session_read(s: ExamSession, students: list[ExamSessionStudent]) -> dict:
    exam = s.exam
    return {
        "id": s.id,
        "exam_id": s.exam_id,
        "room_id": s.room_id,
        "status": s.status,
        "exam_type": exam.exam_type if exam else None,
        "discipline_name": exam.discipline.name if exam and exam.discipline else None,
        "commission_name": exam.commission.name if exam and exam.commission else None,
        "room_name": s.room.name if s.room else None,
        "students": [_student_read(x) for x in students],
    }


async def _students_of(db: AsyncSession, session_id: int) -> list[ExamSessionStudent]:
    res = await db.execute(
        select(ExamSessionStudent)
        .where(ExamSessionStudent.exam_session_id == session_id)
        .order_by(ExamSessionStudent.id.asc())
    )
    return list(res.scalars().all())


async def get_exam_session(db: AsyncSession, session_id: int) -> dict | None:
    res = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    s = res.scalar_one_or_none()
    if s is None:
        return None
    return _session_read(s, await _students_of(db, session_id))


async def list_session_students(db: AsyncSession, session_id: int) -> list[dict]:
    return [_student_read(x) for x in await _students_of(db, session_id)]


async def update_session(db: AsyncSession, session_id: int, data: ExamSessionUpdate) -> dict | None:
    res = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    s = res.scalar_one_or_none()
    if s is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(s, field, value)
    await db.commit()
    return await get_exam_session(db, session_id)


async def add_student(db: AsyncSession, session_id: int, student_id: int) -> dict | None:
    s = await db.get(ExamSession, session_id)
    if s is None:
        return None
    student = await db.get(Lead, student_id)
    if student is None or not student.is_student:
        raise ExamSessionError("Ученик не найден")
    db.add(ExamSessionStudent(exam_session_id=session_id, student_id=student_id))
    await db.commit()
    return await get_exam_session(db, session_id)


async def remove_student(db: AsyncSession, ess_id: int) -> bool:
    res = await db.execute(select(ExamSessionStudent).where(ExamSessionStudent.id == ess_id))
    ess = res.scalar_one_or_none()
    if ess is None:
        return False
    await db.delete(ess)
    await db.commit()
    return True


async def update_student_result(db: AsyncSession, ess_id: int, data: ExamSessionStudentUpdate) -> dict | None:
    res = await db.execute(select(ExamSessionStudent).where(ExamSessionStudent.id == ess_id))
    ess = res.scalar_one_or_none()
    if ess is None:
        return None
    fields = data.model_dump(exclude_unset=True)
    apply_level = fields.pop("apply_level", True)
    for field, value in fields.items():
        setattr(ess, field, value)
    if apply_level and ess.result == ExamResult.passed and ess.result_level is not None:
        lead = await db.get(Lead, ess.student_id)
        if lead is not None:
            lead.level = ess.result_level
    await db.commit()
    await db.refresh(ess)
    return _student_read(ess)
