from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadRead
from app.services import lead_service

from app.schemas.student import ConvertLeadRequest, StudentRead
from app.services import student_service

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

@router.post(
    "/{lead_id}/convert-to-student",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
)
async def convert_lead_to_student(
    lead_id: int, data: ConvertLeadRequest, db: AsyncSession = Depends(get_db)
):
    """Конвертировать лид в ученика."""
    try:
        return await student_service.convert_lead_to_student(db, lead_id, data)
    except student_service.LeadNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except student_service.AlreadyConvertedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except student_service.StudentError as e:
        raise HTTPException(status_code=400, detail=str(e))