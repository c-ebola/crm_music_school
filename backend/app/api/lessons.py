from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.lesson import LessonCreate, LessonRead, LessonUpdate
from app.services import lesson_service

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonRead])
async def get_lessons(
    discipline_id: int | None = None,
    teacher_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await lesson_service.list_lessons(db, discipline_id=discipline_id, teacher_id=teacher_id)


@router.get("/{lesson_id}", response_model=LessonRead)
async def get_lesson_by_id(lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    return lesson


@router.post("", response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def add_lesson(data: LessonCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await lesson_service.create_lesson(db, data)
    except lesson_service.DisciplineNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except lesson_service.NotATeacherError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except lesson_service.LessonError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{lesson_id}", response_model=LessonRead)
async def edit_lesson(lesson_id: int, data: LessonUpdate, db: AsyncSession = Depends(get_db)):
    try:
        lesson = await lesson_service.update_lesson(db, lesson_id, data)
    except lesson_service.NotATeacherError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if lesson is None:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    return lesson

@router.delete("/{lesson_id}")
async def remove_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    try:
        ok = await lesson_service.delete_lesson(db, lesson_id)
    except lesson_service.LessonInUseError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    return {"deleted": True}
