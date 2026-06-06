from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.models.room import Room
from app.models.lead import Lead
from app.models.lesson import Lesson
from app.models.session import Session
from app.models.session_student import SessionStudent
from app.models.subscription import Subscription, SubscriptionStatus
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

async def _active_subscription(db: AsyncSession, student_id: int) -> Subscription | None:
    """Действующий абонемент: не отменён, срок не истёк, есть остаток уроков.
    Берём тот, что заканчивается раньше (сначала тратим старый)."""
    today = date.today()
    res = await db.execute(
        select(Subscription).where(
            Subscription.student_id == student_id,
            Subscription.status != SubscriptionStatus.cancelled,
            Subscription.end_date >= today,
            Subscription.lessons_used < Subscription.lessons_total,
        ).order_by(Subscription.end_date.asc())
    )
    return res.scalars().first()

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
        if room is not None and room.branch_id and student.branch_id and room.branch_id != student.branch_id:
            raise BranchMismatchError("Ученик из другого филиала")

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

    fields = data.model_dump(exclude_unset=True)

    # посещаемость: списываем/возвращаем урок с абонемента
    if "attended" in fields and fields["attended"] != ss.attended:
        if fields["attended"]:
            # отметили «пришёл» > списать урок (если ещё не списан)
            if ss.subscription_id is None:
                sub = await _active_subscription(db, ss.student_id)
                if sub is not None:
                    sub.lessons_used += 1
                    ss.subscription_id = sub.id
                # действующего абонемента нет > посещение фиксируем без списания,
                # ученик попадёт в очередь «нужно продлить»
            ss.attended = True
        else:
            # сняли отметку > вернуть урок
            if ss.subscription_id is not None:
                sub = await db.get(Subscription, ss.subscription_id)
                if sub is not None and sub.lessons_used > 0:
                    sub.lessons_used -= 1
                ss.subscription_id = None
            ss.attended = False
        fields.pop("attended", None)

    # прочие поля (например, ручной subscription_id) - как раньше
    for field, value in fields.items():
        setattr(ss, field, value)

    await db.commit()
    await db.refresh(ss)
    return _to_read(ss)


async def unenroll(db: AsyncSession, ss_id: int) -> bool:
    result = await db.execute(select(SessionStudent).where(SessionStudent.id == ss_id))
    ss = result.scalar_one_or_none()
    if ss is None:
        return False
    if ss.attended and ss.subscription_id is not None:
        sub = await db.get(Subscription, ss.subscription_id)
        if sub is not None and sub.lessons_used > 0:
            sub.lessons_used -= 1
    await db.delete(ss)
    await db.commit()
    return True
