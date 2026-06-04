from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date


from app.db.session import get_db
from app.core.deps import require_roles
from app.schemas.schedule import ScheduleCreate, ScheduleRead, ScheduleUpdate, ScheduleAddSession
from app.services import schedule_service

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.get("", response_model=list[ScheduleRead], dependencies=[Depends(require_roles("methodist","branch_admin","teacher","admin"))])
async def get_schedule(
    quant: int | None = None,
    entity_type: str | None = None,
    day: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await schedule_service.list_schedule(db, quant=quant, entity_type=entity_type, day=day)


@router.get("/week", response_model=list[ScheduleRead], dependencies=[Depends(require_roles("methodist","branch_admin","teacher","admin"))])
async def get_week_schedule(
    week_start: date,
    teacher_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await schedule_service.list_week_schedule(
        db, week_start=week_start, teacher_id=teacher_id
    )


@router.get("/{schedule_id}", response_model=ScheduleRead, dependencies=[Depends(require_roles("methodist","branch_admin","teacher","admin"))])
async def get_schedule_by_id(schedule_id: int, db: AsyncSession = Depends(get_db)):
    s = await schedule_service.get_schedule(db, schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Запись расписания не найдена")
    return s


@router.post("", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("methodist","branch_admin"))])
async def add_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await schedule_service.create_schedule(db, data)
    except schedule_service.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except schedule_service.ScheduleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/add-session", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("methodist","branch_admin"))])
async def add_session_to_schedule(data: ScheduleAddSession, db: AsyncSession = Depends(get_db)):
    try:
        return await schedule_service.add_session_to_schedule(db, data)
    except schedule_service.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except schedule_service.ScheduleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{schedule_id}", response_model=ScheduleRead, dependencies=[Depends(require_roles("methodist","branch_admin"))])
async def edit_schedule(schedule_id: int, data: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    try:
        s = await schedule_service.update_schedule(db, schedule_id, data)
    except schedule_service.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except schedule_service.ScheduleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if s is None:
        raise HTTPException(status_code=404, detail="Запись расписания не найдена")
    return s


@router.delete("/{schedule_id}", dependencies=[Depends(require_roles("methodist","branch_admin"))])
async def remove_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    ok = await schedule_service.delete_schedule(db, schedule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Запись расписания не найдена")
    return {"deleted": True}

