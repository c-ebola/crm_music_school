from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.models.lead import Lead
from app.models.lesson import Lesson
from app.models.session import Session
from app.models.session_student import SessionStudent
from app.models.subscription import Subscription
from app.schemas.session_student import SessionStudentCreate, SessionStudentUpdate


class SessionStudentError(Exception):
    pass


class SessionNotFoundError(SessionStudentError):
    pass


class StudentNotFoundError(SessionStudentError):
    pass


class CapacityExceededError(SessionStudentError):
    pass


class AlreadyEnrolledError(SessionStudentError):
    pass


class DisciplineMismatchError(SessionStudentError):
    pass


class BranchMismatchError(SessionStudentError):
    pass

class LevelMismatchError(SessionStudentError):
    pass

def _to_read(ss: SessionStudent) -> dict:
    student_name = None
    if ss.student is not None:
        student_name = ss.student.student_full_name or ss.student.contact_full_name
    return {
        "id": ss.id,
        "session_id": ss.session_id,
        "student_id": ss.student_id,
        "subscription_id": ss.subscription_id,
        "attended": ss.attended,
        "student_name": student_name,
        "created_at": ss.created_at,
    }


async def list_session_students(
    db: AsyncSession,
    session_id: int | None = None,
    student_id: int | None = None,
) -> list[dict]:
    query = select(SessionStudent)
    if session_id is not None:
        query = query.where(SessionStudent.session_id == session_id)
    if student_id is not None:
        query = query.where(SessionStudent.student_id == student_id)
    query = query.order_by(SessionStudent.created_at.asc())
    result = await db.execute(query)
    return [_to_read(ss) for ss in result.scalars().all()]


async def get_session_student(db: AsyncSession, ss_id: int) -> dict | None:
    result = await db.execute(select(SessionStudent).where(SessionStudent.id == ss_id))
    ss = result.scalar_one_or_none()
    return _to_read(ss) if ss else None


async def enroll(db: AsyncSession, data: SessionStudentCreate) -> dict:
    session = await db.get(Session, data.session_id)
    if session is None:
        raise SessionNotFoundError("Занятие (session) не найдено")

    student = await db.get(Lead, data.student_id)
    if student is None or not student.is_student:
        raise StudentNotFoundError("Ученик не найден (или это ещё не ученик)")

    lesson = await db.get(Lesson, session.lesson_id)

    # дисциплина ученика должна совпадать с дисциплиной занятия
    if lesson is not None and student.discipline_id != lesson.discipline_id:
        raise DisciplineMismatchError("Дисциплина ученика не совпадает с дисциплиной занятия")

    if lesson is not None and lesson.level is not None and student.level != lesson.level:
        raise LevelMismatchError("Уровень ученика не совпадает с уровнем занятия")
    
    # филиал: если у кабинета задан филиал — ученик должен быть из того же
    if session.room_id is not None:
        room = await db.get(Room, session.room_id)
        if room is not None and room.branch and student.preferred_branch and room.branch != student.preferred_branch:
            raise BranchMismatchError(f"Ученик из другого филиала (занятие в филиале «{room.branch}»)")

    # вместимость по типу занятия
    if lesson is not None and lesson.max_students is not None:
        count = await db.execute(
            select(func.count()).select_from(SessionStudent).where(
                SessionStudent.session_id == data.session_id
            )
        )
        if (count.scalar() or 0) >= lesson.max_students:
            raise CapacityExceededError(
                f"Превышена вместимость занятия (максимум {lesson.max_students})"
            )

    # запрет дубля
    dup = await db.execute(
        select(SessionStudent).where(
            SessionStudent.session_id == data.session_id,
            SessionStudent.student_id == data.student_id,
        )
    )
    if dup.scalar_one_or_none() is not None:
        raise AlreadyEnrolledError("Ученик уже записан на это занятие")

    # абонемент (если указан) — принадлежит этому ученику
    if data.subscription_id is not None:
        sub = await db.get(Subscription, data.subscription_id)
        if sub is None:
            raise SessionStudentError("Абонемент не найден")
        if sub.student_id != data.student_id:
            raise SessionStudentError("Абонемент принадлежит другому ученику")

    ss = SessionStudent(
        session_id=data.session_id,
        student_id=data.student_id,
        subscription_id=data.subscription_id,
    )
    db.add(ss)
    await db.commit()
    await db.refresh(ss)
    return _to_read(ss)

async def update_session_student(db: AsyncSession, ss_id: int, data: SessionStudentUpdate) -> dict | None:
    result = await db.execute(select(SessionStudent).where(SessionStudent.id == ss_id))
    ss = result.scalar_one_or_none()
    if ss is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ss, field, value)
    await db.commit()
    await db.refresh(ss)
    return _to_read(ss)


async def unenroll(db: AsyncSession, ss_id: int) -> bool:
    result = await db.execute(select(SessionStudent).where(SessionStudent.id == ss_id))
    ss = result.scalar_one_or_none()
    if ss is None:
        return False
    await db.delete(ss)
    await db.commit()
    return True
