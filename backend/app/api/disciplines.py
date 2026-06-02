from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.discipline import DisciplineCreate, DisciplineRead, DisciplineUpdate
from app.services import discipline_service

router = APIRouter(prefix="/api/disciplines", tags=["disciplines"])


@router.get("", response_model=list[DisciplineRead])
async def get_disciplines(only_active: bool = False, db: AsyncSession = Depends(get_db)):
    return await discipline_service.list_disciplines(db, only_active=only_active)


@router.get("/{discipline_id}", response_model=DisciplineRead)
async def get_discipline_by_id(discipline_id: int, db: AsyncSession = Depends(get_db)):
    d = await discipline_service.get_discipline(db, discipline_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    return d


@router.post("", response_model=DisciplineRead, status_code=status.HTTP_201_CREATED)
async def add_discipline(data: DisciplineCreate, db: AsyncSession = Depends(get_db)):
    return await discipline_service.create_discipline(db, data)


@router.patch("/{discipline_id}", response_model=DisciplineRead)
async def edit_discipline(discipline_id: int, data: DisciplineUpdate, db: AsyncSession = Depends(get_db)):
    d = await discipline_service.update_discipline(db, discipline_id, data)
    if d is None:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    return d
