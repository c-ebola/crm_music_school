from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.session import Session, SessionStatus
from app.schemas.session import SessionCreate, SessionUpdate


class SessionError(Exception):
    pass


class LessonNotFoundError(SessionError):
    pass


async def list_sessions(
    db: AsyncSession,
    lesson_id: int | None = None,
    status: SessionStatus | None = None,
) -> list[Session]:
    query = select(Session)
    if lesson_id is not None:
        query = query.where(Session.lesson_id == lesson_id)
    if status is not None:
        query = query.where(Session.status == status)
    query = query.order_by(Session.id.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_session(db: AsyncSession, session_id: int) -> Session | None:
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def create_session(db: AsyncSession, data: SessionCreate) -> Session:
    lesson = await db.get(Lesson, data.lesson_id)
    if lesson is None:
        raise LessonNotFoundError("Занятие (тип) не найдено")
    session = Session(**data.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def update_session(db: AsyncSession, session_id: int, data: SessionUpdate) -> Session | None:
    session = await get_session(db, session_id)
    if session is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    await db.commit()
    await db.refresh(session)
    return session
