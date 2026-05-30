from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import ContactType, Lead, LeadStatus
from app.models.student import Student
from app.models.user import User
from app.schemas.student import ConvertLeadRequest, StudentCreate, StudentUpdate


class StudentError(Exception):
    pass


class LeadNotFoundError(StudentError):
    pass


class AlreadyConvertedError(StudentError):
    pass


async def list_students(db: AsyncSession, branch: str | None = None) -> list[Student]:
    query = select(Student)
    if branch:
        query = query.where(Student.branch == branch)
    query = query.order_by(Student.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_student(db: AsyncSession, student_id: int) -> Student | None:
    result = await db.execute(select(Student).where(Student.id == student_id))
    return result.scalar_one_or_none()


async def create_student(db: AsyncSession, data: StudentCreate) -> Student:
    student = Student(**data.model_dump())
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


async def update_student(db: AsyncSession, student_id: int, data: StudentUpdate) -> Student | None:
    student = await get_student(db, student_id)
    if student is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    await db.commit()
    await db.refresh(student)
    return student


async def convert_lead_to_student(db: AsyncSession, lead_id: int, data: ConvertLeadRequest) -> Student:
    """Создать ученика на основе лида и пометить лид сконвертированным."""
    lead = await db.get(Lead, lead_id)
    if lead is None:
        raise LeadNotFoundError(f"Лид с id={lead_id} не найден")
    if lead.status == LeadStatus.converted:
        raise AlreadyConvertedError("Лид уже сконвертирован")

    # ФИО УЧЕНИКА 
    if data.full_name:
        # явно передано в форме конверсии
        full_name = data.full_name
    elif lead.student_full_name:
        # в заявке указано ФИО ученика — берём его
        full_name = lead.student_full_name
    elif lead.contact_type == ContactType.student:
        # контакт сам является учеником (лид записался сам)
        full_name = lead.contact_full_name
    else:
        # родитель оставил заявку, ФИО ребёнка не указано — требуем ввод
        raise StudentError(
            "В заявке не указано ФИО ученика. Укажите ФИО ученика "
            "в форме конверсии (поле full_name)."
        )

    branch = data.branch if data.branch is not None else lead.preferred_branch

    student = Student(
        full_name=full_name,
        discipline=lead.discipline,
        branch=branch,
        enrollment_date=data.enrollment_date,
        teacher_id=data.teacher_id,
        lead_id=lead.id,
    )
    db.add(student)
    lead.status = LeadStatus.converted

    await db.commit()
    await db.refresh(student)
    return student