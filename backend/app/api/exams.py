from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.schemas.exam import ExamCreate, ExamRead, ExamUpdate
from app.services import exam_service

router = APIRouter(prefix="/api/exams", tags=["exams"])

READ = require_roles("methodist", "branch_admin", "teacher", "admin")
WRITE = require_roles("methodist", "branch_admin")


@router.get("", response_model=list[ExamRead], dependencies=[Depends(READ)])
async def list_exams(db: AsyncSession = Depends(get_db)):
    return await exam_service.list_exams(db)


@router.get("/{exam_id}", response_model=ExamRead, dependencies=[Depends(READ)])
async def get_exam(exam_id: int, db: AsyncSession = Depends(get_db)):
    e = await exam_service.get_exam(db, exam_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Экзамен не найден")
    return e


@router.post("", response_model=ExamRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(WRITE)])
async def create_exam(data: ExamCreate, db: AsyncSession = Depends(get_db)):
    return await exam_service.create_exam(db, data)


@router.patch("/{exam_id}", response_model=ExamRead, dependencies=[Depends(WRITE)])
async def update_exam(exam_id: int, data: ExamUpdate, db: AsyncSession = Depends(get_db)):
    e = await exam_service.update_exam(db, exam_id, data)
    if e is None:
        raise HTTPException(status_code=404, detail="Экзамен не найден")
    return e


@router.delete("/{exam_id}", dependencies=[Depends(WRITE)])
async def delete_exam(exam_id: int, db: AsyncSession = Depends(get_db)):
    ok = await exam_service.delete_exam(db, exam_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Экзамен не найден")
    return {"deleted": True}
