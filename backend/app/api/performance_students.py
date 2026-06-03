from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.performance_student import (
    PerformanceStudentCreate, PerformanceStudentRead, PerformanceStudentUpdate,
)
from app.services import performance_student_service

router = APIRouter(prefix="/api/performance-students", tags=["performance-students"])


@router.get("", response_model=list[PerformanceStudentRead])
async def get_performance_students(
    performance_id: int | None = None,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await performance_student_service.list_performance_students(
        db, performance_id=performance_id, student_id=student_id
    )


@router.get("/{ps_id}", response_model=PerformanceStudentRead)
async def get_performance_student_by_id(ps_id: int, db: AsyncSession = Depends(get_db)):
    ps = await performance_student_service.get_performance_student(db, ps_id)
    if ps is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return ps


@router.post("", response_model=PerformanceStudentRead, status_code=status.HTTP_201_CREATED)
async def enroll_performer(data: PerformanceStudentCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await performance_student_service.enroll(db, data)
    except performance_student_service.PerformanceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except performance_student_service.StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except performance_student_service.AlreadyEnrolledError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except performance_student_service.PerformanceStudentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{ps_id}", response_model=PerformanceStudentRead)
async def edit_performance_student(ps_id: int, data: PerformanceStudentUpdate, db: AsyncSession = Depends(get_db)):
    ps = await performance_student_service.update_performance_student(db, ps_id, data)
    if ps is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return ps


@router.delete("/{ps_id}")
async def remove_performance_student(ps_id: int, db: AsyncSession = Depends(get_db)):
    ok = await performance_student_service.unenroll(db, ps_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"deleted": True}
