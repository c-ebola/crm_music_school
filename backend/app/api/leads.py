from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadRead
from app.services import lead_service

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("", response_model=list[LeadRead])
async def get_leads(db: AsyncSession = Depends(get_db)):
    """Получить список всех лидов."""
    return await lead_service.list_leads(db)


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead_by_id(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Получить лид по ID."""
    lead = await lead_service.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Лид не найден")
    return lead


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def add_lead(data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Создать нового лида."""
    return await lead_service.create_lead(db, data)