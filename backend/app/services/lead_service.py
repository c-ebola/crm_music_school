from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import ContactType, Lead, LeadStatus, StudentStatus
from app.schemas.lead import ConvertLeadRequest, LeadCreate


class LeadServiceError(Exception):
    pass


class LeadNotFoundError(LeadServiceError):
    pass


class AlreadyConvertedError(LeadServiceError):
    pass


async def list_leads(db: AsyncSession, is_student: bool | None = None) -> list[Lead]:
    """Список записей. is_student=True → ученики, False → активные лиды, None → все."""
    query = select(Lead)
    if is_student is not None:
        query = query.where(Lead.is_student == is_student)
    query = query.order_by(Lead.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_lead(db: AsyncSession, lead_id: int) -> Lead | None:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()


async def create_lead(db: AsyncSession, data: LeadCreate) -> Lead:
    lead = Lead(**data.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


async def convert_lead_to_student(
    db: AsyncSession, lead_id: int, data: ConvertLeadRequest
) -> Lead:
    """Пометить лид учеником (та же запись), заполнить поля ученика."""
    lead = await get_lead(db, lead_id)
    if lead is None:
        raise LeadNotFoundError(f"Лид с id={lead_id} не найден")
    if lead.is_student:
        raise AlreadyConvertedError("Лид уже зачислен как ученик")

    # ФИО УЧЕНИКА (не родителя!)
    if data.full_name:
        lead.student_full_name = data.full_name
    elif lead.student_full_name:
        pass  # уже указано в заявке
    elif lead.contact_type == ContactType.student:
        lead.student_full_name = lead.contact_full_name  # записался сам
    else:
        raise LeadServiceError(
            "В заявке не указано ФИО ученика. Укажите его в форме конверсии."
        )

    if data.branch is not None:
        lead.preferred_branch = data.branch

    lead.teacher_id = data.teacher_id
    lead.enrollment_date = data.enrollment_date
    lead.student_status = StudentStatus.active
    lead.is_student = True
    lead.status = LeadStatus.converted

    await db.commit()
    await db.refresh(lead)
    return lead
