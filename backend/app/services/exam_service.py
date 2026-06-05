from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import Exam
from app.schemas.exam import ExamCreate, ExamUpdate


def _to_read(e: Exam) -> dict:
    return {
        "id": e.id,
        "discipline_id": e.discipline_id,
        "discipline_name": e.discipline.name if e.discipline else None,
        "exam_type": e.exam_type,
        "max_students": e.max_students,
        "level": e.level,
        "commission_id": e.commission_id,
        "commission_name": e.commission.name if e.commission else None,
        "created_at": e.created_at,
    }


async def list_exams(db: AsyncSession) -> list[dict]:
    res = await db.execute(select(Exam).order_by(Exam.id.desc()))
    return [_to_read(e) for e in res.scalars().all()]


async def get_exam(db: AsyncSession, exam_id: int) -> dict | None:
    res = await db.execute(select(Exam).where(Exam.id == exam_id))
    e = res.scalar_one_or_none()
    return _to_read(e) if e else None


async def create_exam(db: AsyncSession, data: ExamCreate) -> dict:
    exam = Exam(**data.model_dump())
    db.add(exam)
    await db.commit()
    return await get_exam(db, exam.id)


async def update_exam(db: AsyncSession, exam_id: int, data: ExamUpdate) -> dict | None:
    res = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = res.scalar_one_or_none()
    if exam is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    await db.commit()
    return await get_exam(db, exam_id)


async def delete_exam(db: AsyncSession, exam_id: int) -> bool:
    res = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = res.scalar_one_or_none()
    if exam is None:
        return False
    await db.delete(exam)
    await db.commit()
    return True
