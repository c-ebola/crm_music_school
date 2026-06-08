from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date



from app.db.session import get_db
from app.core.deps import require_roles, get_current_active_user, get_branch_filter
from app.models.user import User
from app.models.room import Room
from app.schemas.schedule import ScheduleCreate, ScheduleRead, ScheduleUpdate, ScheduleAddSession, ScheduleAddExam
from app.services import schedule_service
from app.schemas.schedule import (
    ScheduleCreate, ScheduleRead, ScheduleUpdate, ScheduleAddSession, ScheduleAddEvent, ScheduleAddEventRef 
)

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.get("", response_model=list[ScheduleRead], dependencies=[Depends(require_roles("methodist","branch_admin","teacher","admin"))])
async def get_schedule(
    quant: int | None = None,
    entity_type: str | None = None,
    day: date | None = None,
    db: AsyncSession = Depends(get_db),
    branch_filter: int | None = Depends(get_branch_filter),
):
    return await schedule_service.list_schedule(db, quant=quant, entity_type=entity_type, day=day,
                                                 branch_filter=branch_filter)


@router.get("/week", response_model=list[ScheduleRead], dependencies=[Depends(require_roles("methodist","branch_admin","teacher","admin"))])
async def get_week_schedule(
    week_start: date,
    teacher_id: int | None = None,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await schedule_service.list_week_schedule(
        db, week_start=week_start, teacher_id=teacher_id, student_id=student_id
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


@router.post("/add-session", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
async def add_session_to_schedule(
    data: ScheduleAddSession, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("methodist","branch_admin","admin")),
):
    if current_user.branch_id and data.room_id:
        room = await db.get(Room, data.room_id)
        if room and room.branch_id and room.branch_id != current_user.branch_id:
            raise HTTPException(403, "Кабинет не принадлежит вашему филиалу")
    try:
        return await schedule_service.add_session_to_schedule(db, data)
    except schedule_service.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except schedule_service.ScheduleError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/place-event", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_roles("methodist", "branch_admin", "admin"))])
async def place_event(data: ScheduleAddEventRef, db: AsyncSession = Depends(get_db)):
    try:
        return await schedule_service.place_event_in_schedule(db, data.event_id, data.day, data.quant)
    except schedule_service.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except schedule_service.ScheduleError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add-event", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_roles("methodist", "branch_admin", "admin"))])
async def add_event_to_schedule(data: ScheduleAddEvent, db: AsyncSession = Depends(get_db)):
    try:
        return await schedule_service.add_event_to_schedule(db, data)
    except schedule_service.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except schedule_service.ScheduleError as e:
        raise HTTPException(status_code=400, detail=str(e)) 

@router.post("/add-exam", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
async def add_exam_to_schedule(
    data: ScheduleAddExam, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("methodist","branch_admin","admin")),
):
    if current_user.branch_id and data.room_id:
        room = await db.get(Room, data.room_id)
        if room and room.branch_id and room.branch_id != current_user.branch_id:
            raise HTTPException(403, "Кабинет не принадлежит вашему филиалу")
    try:
        return await schedule_service.add_exam_to_schedule(db, data)
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


@router.delete("/{schedule_id}", dependencies=[Depends(require_roles("methodist", "branch_admin", "admin"))])
async def remove_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    ok = await schedule_service.delete_schedule(db, schedule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Запись расписания не найдена")
    return {"deleted": True}

