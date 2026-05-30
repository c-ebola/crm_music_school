from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.student import (
    ConvertLeadRequest, StudentCreate, StudentRead, StudentUpdate,
)
from app.services import student_service

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=list[StudentRead])
async def get_students(branch: str | None = None, db: AsyncSession = Depends(get_db)):
    return await student_service.list_students(db, branch=branch)


@router.get("/{student_id}", response_model=StudentRead)
async def get_student_by_id(student_id: int, db: AsyncSession = Depends(get_db)):
    student = await student_service.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    return student


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def add_student(data: StudentCreate, db: AsyncSession = Depends(get_db)):
    return await student_service.create_student(db, data)


@router.patch("/{student_id}", response_model=StudentRead)
async def edit_student(student_id: int, data: StudentUpdate, db: AsyncSession = Depends(get_db)):
    student = await student_service.update_student(db, student_id, data)
    if student is None:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    return student
