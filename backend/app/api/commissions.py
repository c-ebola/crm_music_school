from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.schemas.commission import (
    CommissionCreate, CommissionRead, CommissionUpdate, CommissionMemberCreate,
)
from app.services import commission_service

router = APIRouter(prefix="/api/commissions", tags=["commissions"])

READ = require_roles("methodist", "branch_admin", "teacher", "admin")
WRITE = require_roles("methodist", "branch_admin")


@router.get("", response_model=list[CommissionRead], dependencies=[Depends(READ)])
async def list_commissions(db: AsyncSession = Depends(get_db)):
    return await commission_service.list_commissions(db)


@router.get("/{commission_id}", response_model=CommissionRead, dependencies=[Depends(READ)])
async def get_commission(commission_id: int, db: AsyncSession = Depends(get_db)):
    c = await commission_service.get_commission(db, commission_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Комиссия не найдена")
    return c


@router.post("", response_model=CommissionRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(WRITE)])
async def create_commission(data: CommissionCreate, db: AsyncSession = Depends(get_db)):
    return await commission_service.create_commission(db, data)


@router.patch("/{commission_id}", response_model=CommissionRead, dependencies=[Depends(WRITE)])
async def update_commission(commission_id: int, data: CommissionUpdate, db: AsyncSession = Depends(get_db)):
    c = await commission_service.update_commission(db, commission_id, data)
    if c is None:
        raise HTTPException(status_code=404, detail="Комиссия не найдена")
    return c


@router.delete("/{commission_id}", dependencies=[Depends(WRITE)])
async def delete_commission(commission_id: int, db: AsyncSession = Depends(get_db)):
    ok = await commission_service.delete_commission(db, commission_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Комиссия не найдена")
    return {"deleted": True}


@router.post("/{commission_id}/members", response_model=CommissionRead, dependencies=[Depends(WRITE)])
async def add_member(commission_id: int, data: CommissionMemberCreate, db: AsyncSession = Depends(get_db)):
    c = await commission_service.add_member(db, commission_id, data)
    if c is None:
        raise HTTPException(status_code=404, detail="Комиссия не найдена")
    return c


@router.delete("/{commission_id}/members/{member_id}", response_model=CommissionRead, dependencies=[Depends(WRITE)])
async def remove_member(commission_id: int, member_id: int, db: AsyncSession = Depends(get_db)):
    c = await commission_service.remove_member(db, commission_id, member_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Не найдено")
    return c
