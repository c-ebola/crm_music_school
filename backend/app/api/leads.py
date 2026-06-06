from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles, get_current_active_user, get_branch_filter
from app.schemas.lead import ConvertLeadRequest, LeadCreate, LeadRead, LeadStatusUpdate
from app.services import lead_service
from app.models.lead import Level

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("", response_model=list[LeadRead], dependencies=[Depends(get_current_active_user)])
async def get_leads(
    is_student: bool | None = None,
    discipline_id: int | None = None,
    branch_id: int | None = None,
    level: Level | None = None,
    db: AsyncSession = Depends(get_db),
    branch_filter: int | None = Depends(get_branch_filter),
):
    effective_branch = branch_filter if branch_filter is not None else branch_id
    return await lead_service.list_leads(
        db, is_student=is_student, discipline_id=discipline_id, branch_id=effective_branch, level=level
    )


@router.get("/{lead_id}", response_model=LeadRead, dependencies=[Depends(get_current_active_user)])
async def get_lead_by_id(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await lead_service.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Лид не найден")
    return lead


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_roles("manager", "branch_admin"))])
async def add_lead(data: LeadCreate, db: AsyncSession = Depends(get_db)):
    return await lead_service.create_lead(db, data)


@router.post("/{lead_id}/convert-to-student", response_model=LeadRead,
             dependencies=[Depends(require_roles("manager", "branch_admin"))])
async def convert_lead_to_student(
    lead_id: int, data: ConvertLeadRequest, db: AsyncSession = Depends(get_db)
):
    """Конвертировать лид в ученика (та же запись, is_student=true)."""
    try:
        return await lead_service.convert_lead_to_student(db, lead_id, data)
    except lead_service.LeadNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except lead_service.AlreadyConvertedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except lead_service.LeadServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{lead_id}/status", response_model=LeadRead,
              dependencies=[Depends(require_roles("manager", "branch_admin", "admin"))])
async def update_lead_status(lead_id: int, data: LeadStatusUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await lead_service.set_status(db, lead_id, data.status)
    except lead_service.LeadNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except lead_service.LeadServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
