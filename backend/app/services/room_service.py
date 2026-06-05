from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate


async def list_rooms(db: AsyncSession, only_active: bool = False, branch_id: int | None = None) -> list[Room]:
    query = select(Room)
    if only_active:
        query = query.where(Room.is_active.is_(True))
    if branch_id is not None:
        query = query.where(Room.branch_id == branch_id)
    query = query.order_by(Room.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_room(db: AsyncSession, room_id: int) -> Room | None:
    result = await db.execute(select(Room).where(Room.id == room_id))
    return result.scalar_one_or_none()


async def create_room(db: AsyncSession, data: RoomCreate) -> Room:
    room = Room(**data.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def update_room(db: AsyncSession, room_id: int, data: RoomUpdate) -> Room | None:
    room = await get_room(db, room_id)
    if room is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    await db.commit()
    await db.refresh(room)
    return room
