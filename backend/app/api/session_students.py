from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.session_student import (
    SessionStudentCreate, SessionStudentRead, SessionStudentUpdate,
)
from app.services import session_student_service

router = APIRouter(prefix="/api/session-students", tags=["session-students"])


@router.get("", response_model=list[SessionStudentRead])
async def get_session_students(
    session_id: int | None = None,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await session_student_service.list_session_students(
        db, session_id=session_id, student_id=student_id
    )


@router.get("/{ss_id}", response_model=SessionStudentRead)
async def get_session_student_by_id(ss_id: int, db: AsyncSession = Depends(get_db)):
    ss = await session_student_service.get_session_student(db, ss_id)
    if ss is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return ss


@router.post("", response_model=SessionStudentRead, status_code=status.HTTP_201_CREATED)
async def enroll_student(data: SessionStudentCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await session_student_service.enroll(db, data)
    except session_student_service.DisciplineMismatchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except session_student_service.BranchMismatchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except session_student_service.SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except session_student_service.StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except session_student_service.CapacityExceededError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except session_student_service.AlreadyEnrolledError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except session_student_service.SessionStudentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except session_student_service.LevelMismatchError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{ss_id}", response_model=SessionStudentRead)
async def edit_session_student(ss_id: int, data: SessionStudentUpdate, db: AsyncSession = Depends(get_db)):
    ss = await session_student_service.update_session_student(db, ss_id, data)
    if ss is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return ss


@router.delete("/{ss_id}")
async def remove_session_student(ss_id: int, db: AsyncSession = Depends(get_db)):
    ok = await session_student_service.unenroll(db, ss_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"deleted": True}
