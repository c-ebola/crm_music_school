from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.schemas.homework import HomeworkCreate, HomeworkRead, HomeworkUpdate
from app.services import homework_service

router = APIRouter(prefix="/api/homeworks", tags=["homeworks"])


@router.get("", response_model=list[HomeworkRead], dependencies=[Depends(require_roles("teacher","admin"))])
async def get_homeworks(
    teacher_id: int | None = None,
    student_id: int | None = None,
    is_completed: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await homework_service.list_homeworks(
        db, teacher_id=teacher_id, student_id=student_id, is_completed=is_completed
    )


@router.get("/{hw_id}", response_model=HomeworkRead, dependencies=[Depends(require_roles("teacher","admin"))])
async def get_homework_by_id(hw_id: int, db: AsyncSession = Depends(get_db)):
    h = await homework_service.get_homework(db, hw_id)
    if h is None:
        raise HTTPException(status_code=404, detail="Домашнее задание не найдено")
    return h


@router.post("", response_model=HomeworkRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("teacher"))])
async def add_homework(data: HomeworkCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await homework_service.create_homework(db, data)
    except homework_service.TeacherNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except homework_service.StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except homework_service.HomeworkError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{hw_id}", response_model=HomeworkRead, dependencies=[Depends(require_roles("teacher"))])
async def edit_homework(hw_id: int, data: HomeworkUpdate, db: AsyncSession = Depends(get_db)):
    h = await homework_service.update_homework(db, hw_id, data)
    if h is None:
        raise HTTPException(status_code=404, detail="Домашнее задание не найдено")
    return h


@router.delete("/{hw_id}", dependencies=[Depends(require_roles("teacher"))])
async def remove_homework(hw_id: int, db: AsyncSession = Depends(get_db)):
    ok = await homework_service.delete_homework(db, hw_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Домашнее задание не найдено")
    return {"deleted": True}
