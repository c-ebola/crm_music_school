from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instrument import Instrument
from app.schemas.instrument import InstrumentCreate, InstrumentUpdate


async def list_instruments(db: AsyncSession, only_active: bool = False, branch_id: int | None = None) -> list[Instrument]:
    query = select(Instrument)
    if only_active:
        query = query.where(Instrument.is_active.is_(True))
    if branch_id is not None:
        query = query.where(Instrument.branch_id == branch_id)
    query = query.order_by(Instrument.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_instrument(db: AsyncSession, instrument_id: int) -> Instrument | None:
    result = await db.execute(select(Instrument).where(Instrument.id == instrument_id))
    return result.scalar_one_or_none()


async def create_instrument(db: AsyncSession, data: InstrumentCreate) -> Instrument:
    instr = Instrument(**data.model_dump())
    db.add(instr)
    await db.commit()
    await db.refresh(instr)
    return instr


async def update_instrument(db: AsyncSession, instrument_id: int, data: InstrumentUpdate) -> Instrument | None:
    instr = await get_instrument(db, instrument_id)
    if instr is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(instr, field, value)
    await db.commit()
    await db.refresh(instr)
    return instr
