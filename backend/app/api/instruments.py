from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.instrument import InstrumentCreate, InstrumentRead, InstrumentUpdate
from app.services import instrument_service

router = APIRouter(prefix="/api/instruments", tags=["instruments"])


@router.get("", response_model=list[InstrumentRead])
async def get_instruments(only_active: bool = False, branch: str | None = None, db: AsyncSession = Depends(get_db)):
    return await instrument_service.list_instruments(db, only_active=only_active, branch=branch)


@router.get("/{instrument_id}", response_model=InstrumentRead)
async def get_instrument_by_id(instrument_id: int, db: AsyncSession = Depends(get_db)):
    instr = await instrument_service.get_instrument(db, instrument_id)
    if instr is None:
        raise HTTPException(status_code=404, detail="Инструмент не найден")
    return instr


@router.post("", response_model=InstrumentRead, status_code=status.HTTP_201_CREATED)
async def add_instrument(data: InstrumentCreate, db: AsyncSession = Depends(get_db)):
    return await instrument_service.create_instrument(db, data)


@router.patch("/{instrument_id}", response_model=InstrumentRead)
async def edit_instrument(instrument_id: int, data: InstrumentUpdate, db: AsyncSession = Depends(get_db)):
    instr = await instrument_service.update_instrument(db, instrument_id, data)
    if instr is None:
        raise HTTPException(status_code=404, detail="Инструмент не найден")
    return instr
