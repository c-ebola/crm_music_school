from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.session import SessionStatus
from app.schemas.session import SessionCreate, SessionRead, SessionUpdate
from app.services import session_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionRead])
async def get_sessions(
    lesson_id: int | None = None,
    status: SessionStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await session_service.list_sessions(
        db, lesson_id=lesson_id, status=status, date_from=date_from, date_to=date_to
    )


@router.get("/{session_id}", response_model=SessionRead)
async def get_session_by_id(session_id: int, db: AsyncSession = Depends(get_db)):
    s = await session_service.get_session(db, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return s


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def add_session(data: SessionCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await session_service.create_session(db, data)
    except session_service.LessonNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except session_service.SessionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{session_id}", response_model=SessionRead)
async def edit_session(session_id: int, data: SessionUpdate, db: AsyncSession = Depends(get_db)):
    s = await session_service.update_session(db, session_id, data)
    if s is None:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return s
