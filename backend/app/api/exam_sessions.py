from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.schemas.exam import (
    ExamSessionRead, ExamSessionUpdate,
    ExamSessionStudentRead, ExamSessionStudentUpdate, ExamStudentAdd,
)
from app.services import exam_session_service

router = APIRouter(prefix="/api/exam-sessions", tags=["exam-sessions"])
students_router = APIRouter(prefix="/api/exam-session-students", tags=["exam-session-students"])

READ = require_roles("methodist", "branch_admin", "teacher", "admin")
MANAGE = require_roles("methodist", "branch_admin")
CONDUCT = require_roles("teacher", "methodist", "branch_admin")


@router.get("/{session_id}", response_model=ExamSessionRead, dependencies=[Depends(READ)])
async def get_exam_session(session_id: int, db: AsyncSession = Depends(get_db)):
    s = await exam_session_service.get_exam_session(db, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Проведение экзамена не найдено")
    return s


@router.get("/{session_id}/students", response_model=list[ExamSessionStudentRead], dependencies=[Depends(READ)])
async def list_students(session_id: int, db: AsyncSession = Depends(get_db)):
    return await exam_session_service.list_session_students(db, session_id)


@router.patch("/{session_id}", response_model=ExamSessionRead, dependencies=[Depends(MANAGE)])
async def update_exam_session(session_id: int, data: ExamSessionUpdate, db: AsyncSession = Depends(get_db)):
    s = await exam_session_service.update_session(db, session_id, data)
    if s is None:
        raise HTTPException(status_code=404, detail="Проведение экзамена не найдено")
    return s


@router.post("/{session_id}/students", response_model=ExamSessionRead, dependencies=[Depends(MANAGE)])
async def add_student(session_id: int, data: ExamStudentAdd, db: AsyncSession = Depends(get_db)):
    try:
        s = await exam_session_service.add_student(db, session_id, data.student_id)
    except exam_session_service.ExamSessionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if s is None:
        raise HTTPException(status_code=404, detail="Проведение экзамена не найдено")
    return s


@students_router.patch("/{ess_id}", response_model=ExamSessionStudentRead, dependencies=[Depends(CONDUCT)])
async def update_student_result(ess_id: int, data: ExamSessionStudentUpdate, db: AsyncSession = Depends(get_db)):
    r = await exam_session_service.update_student_result(db, ess_id, data)
    if r is None:
        raise HTTPException(status_code=404, detail="Запись ученика не найдена")
    return r


@students_router.delete("/{ess_id}", dependencies=[Depends(MANAGE)])
async def remove_student(ess_id: int, db: AsyncSession = Depends(get_db)):
    ok = await exam_session_service.remove_student(db, ess_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Запись ученика не найдена")
    return {"deleted": True}
