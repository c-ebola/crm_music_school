from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.schemas.lead import LeadCreate


async def list_leads(db: AsyncSession) -> list[Lead]:
    """Получить все лиды, новые сверху."""
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    return list(result.scalars().all())


async def get_lead(db: AsyncSession, lead_id: int) -> Lead | None:
    """Получить лид по ID или None."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()


async def create_lead(db: AsyncSession, data: LeadCreate) -> Lead:
    """Создать нового лида."""
    lead = Lead(**data.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead