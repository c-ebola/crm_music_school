from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.performance import Performance
from app.models.performance_student import PerformanceStudent
from app.schemas.performance_student import PerformanceStudentCreate, PerformanceStudentUpdate


class PerformanceStudentError(Exception):
    pass


class PerformanceNotFoundError(PerformanceStudentError):
    pass


class StudentNotFoundError(PerformanceStudentError):
    pass


class AlreadyEnrolledError(PerformanceStudentError):
    pass


def _to_read(ps: PerformanceStudent) -> dict:
    return {
        "id": ps.id,
        "performance_id": ps.performance_id,
        "student_id": ps.student_id,
        "instrument_id": ps.instrument_id,
        "student_name": (ps.student.student_full_name or ps.student.contact_full_name) if ps.student else None,
        "instrument_name": ps.instrument.name if ps.instrument else None,
        "created_at": ps.created_at,
    }


async def list_performance_students(
    db: AsyncSession,
    performance_id: int | None = None,
    student_id: int | None = None,
) -> list[dict]:
    query = select(PerformanceStudent)
    if performance_id is not None:
        query = query.where(PerformanceStudent.performance_id == performance_id)
    if student_id is not None:
        query = query.where(PerformanceStudent.student_id == student_id)
    query = query.order_by(PerformanceStudent.created_at.asc())
    result = await db.execute(query)
    return [_to_read(ps) for ps in result.scalars().all()]


async def get_performance_student(db: AsyncSession, ps_id: int) -> dict | None:
    result = await db.execute(select(PerformanceStudent).where(PerformanceStudent.id == ps_id))
    ps = result.scalar_one_or_none()
    return _to_read(ps) if ps else None


async def enroll(db: AsyncSession, data: PerformanceStudentCreate) -> dict:
    perf = await db.get(Performance, data.performance_id)
    if perf is None:
        raise PerformanceNotFoundError("Выступление не найдено")

    student = await db.get(Lead, data.student_id)
    if student is None or not student.is_student:
        raise StudentNotFoundError("Ученик не найден (или это ещё не ученик)")

    dup = await db.execute(
        select(PerformanceStudent).where(
            PerformanceStudent.performance_id == data.performance_id,
            PerformanceStudent.student_id == data.student_id,
        )
    )
    if dup.scalar_one_or_none() is not None:
        raise AlreadyEnrolledError("Ученик уже добавлен в это выступление")

    ps = PerformanceStudent(
        performance_id=data.performance_id,
        student_id=data.student_id,
        instrument_id=data.instrument_id,
    )
    db.add(ps)
    await db.commit()
    await db.refresh(ps)
    return _to_read(ps)


async def update_performance_student(db: AsyncSession, ps_id: int, data: PerformanceStudentUpdate) -> dict | None:
    result = await db.execute(select(PerformanceStudent).where(PerformanceStudent.id == ps_id))
    ps = result.scalar_one_or_none()
    if ps is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ps, field, value)
    await db.commit()
    await db.refresh(ps)
    return _to_read(ps)


async def unenroll(db: AsyncSession, ps_id: int) -> bool:
    result = await db.execute(select(PerformanceStudent).where(PerformanceStudent.id == ps_id))
    ps = result.scalar_one_or_none()
    if ps is None:
        return False
    await db.delete(ps)
    await db.commit()
    return True
