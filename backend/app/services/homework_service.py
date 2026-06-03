from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import Homework
from app.models.lead import Lead
from app.models.role import Role
from app.models.user import User
from app.schemas.homework import HomeworkCreate, HomeworkUpdate


class HomeworkError(Exception):
    pass


class TeacherNotFoundError(HomeworkError):
    pass


class StudentNotFoundError(HomeworkError):
    pass


def _to_read(h: Homework) -> dict:
    teacher_name = None
    if h.teacher is not None:
        teacher_name = " ".join(filter(None, [h.teacher.last_name, h.teacher.first_name])) or None
    student_name = None
    if h.student is not None:
        student_name = h.student.student_full_name or h.student.contact_full_name
    return {
        "id": h.id,
        "teacher_id": h.teacher_id,
        "student_id": h.student_id,
        "description": h.description,
        "comment": h.comment,
        "is_completed": h.is_completed,
        "teacher_name": teacher_name,
        "student_name": student_name,
        "created_at": h.created_at,
    }


async def list_homeworks(
    db: AsyncSession,
    teacher_id: int | None = None,
    student_id: int | None = None,
    is_completed: bool | None = None,
) -> list[dict]:
    query = select(Homework)
    if teacher_id is not None:
        query = query.where(Homework.teacher_id == teacher_id)
    if student_id is not None:
        query = query.where(Homework.student_id == student_id)
    if is_completed is not None:
        query = query.where(Homework.is_completed == is_completed)
    query = query.order_by(Homework.created_at.desc())
    result = await db.execute(query)
    return [_to_read(h) for h in result.scalars().all()]


async def get_homework(db: AsyncSession, hw_id: int) -> dict | None:
    result = await db.execute(select(Homework).where(Homework.id == hw_id))
    h = result.scalar_one_or_none()
    return _to_read(h) if h else None


async def create_homework(db: AsyncSession, data: HomeworkCreate) -> dict:
    res = await db.execute(
        select(User).join(Role).where(User.id == data.teacher_id, Role.code == "teacher")
    )
    if res.scalar_one_or_none() is None:
        raise TeacherNotFoundError("Нужен пользователь с ролью 'teacher'")
    student = await db.get(Lead, data.student_id)
    if student is None or not student.is_student:
        raise StudentNotFoundError("Ученик не найден")

    hw = Homework(**data.model_dump())
    db.add(hw)
    await db.commit()
    await db.refresh(hw)
    return _to_read(hw)


async def update_homework(db: AsyncSession, hw_id: int, data: HomeworkUpdate) -> dict | None:
    result = await db.execute(select(Homework).where(Homework.id == hw_id))
    hw = result.scalar_one_or_none()
    if hw is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(hw, field, value)
    await db.commit()
    await db.refresh(hw)
    return _to_read(hw)


async def delete_homework(db: AsyncSession, hw_id: int) -> bool:
    result = await db.execute(select(Homework).where(Homework.id == hw_id))
    hw = result.scalar_one_or_none()
    if hw is None:
        return False
    await db.delete(hw)
    await db.commit()
    return True
