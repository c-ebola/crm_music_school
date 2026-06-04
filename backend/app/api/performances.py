from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.schemas.performance import PerformanceCreate, PerformanceRead, PerformanceUpdate
from app.services import performance_service

router = APIRouter(prefix="/api/performances", tags=["performances"])


@router.get("", response_model=list[PerformanceRead], dependencies=[Depends(require_roles("methodist","branch_admin","admin"))])
async def get_performances(event_id: int | None = None, db: AsyncSession = Depends(get_db)):
    return await performance_service.list_performances(db, event_id=event_id)


@router.get("/{perf_id}", response_model=PerformanceRead, dependencies=[Depends(require_roles("methodist","branch_admin","admin"))])
async def get_performance_by_id(perf_id: int, db: AsyncSession = Depends(get_db)):
    p = await performance_service.get_performance(db, perf_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Выступление не найдено")
    return p


@router.post("", response_model=PerformanceRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("methodist"))])
async def add_performance(data: PerformanceCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await performance_service.create_performance(db, data)
    except performance_service.EventNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except performance_service.PerformanceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{perf_id}", response_model=PerformanceRead, dependencies=[Depends(require_roles("methodist"))])
async def edit_performance(perf_id: int, data: PerformanceUpdate, db: AsyncSession = Depends(get_db)):
    p = await performance_service.update_performance(db, perf_id, data)
    if p is None:
        raise HTTPException(status_code=404, detail="Выступление не найдено")
    return p


@router.delete("/{perf_id}", dependencies=[Depends(require_roles("methodist"))])
async def remove_performance(perf_id: int, db: AsyncSession = Depends(get_db)):
    ok = await performance_service.delete_performance(db, perf_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Выступление не найдено")
    return {"deleted": True}
