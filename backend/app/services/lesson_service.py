from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discipline import Discipline
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonUpdate


class LessonError(Exception):
    pass


class DisciplineNotFoundError(LessonError):
    pass


async def list_lessons(
    db: AsyncSession,
    discipline_id: int | None = None,
    teacher_id: int | None = None,
) -> list[Lesson]:
    query = select(Lesson)
    if discipline_id is not None:
        query = query.where(Lesson.discipline_id == discipline_id)
    if teacher_id is not None:
        query = query.where(Lesson.teacher_id == teacher_id)
    query = query.order_by(Lesson.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_lesson(db: AsyncSession, lesson_id: int) -> Lesson | None:
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    return result.scalar_one_or_none()


async def create_lesson(db: AsyncSession, data: LessonCreate) -> Lesson:
    discipline = await db.get(Discipline, data.discipline_id)
    if discipline is None:
        raise DisciplineNotFoundError("Дисциплина не найдена")
    lesson = Lesson(**data.model_dump())
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def update_lesson(db: AsyncSession, lesson_id: int, data: LessonUpdate) -> Lesson | None:
    lesson = await get_lesson(db, lesson_id)
    if lesson is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lesson, field, value)
    await db.commit()
    await db.refresh(lesson)
    return lesson
