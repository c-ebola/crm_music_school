from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles, get_branch_filter
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate
from app.services import room_service

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomRead], dependencies=[Depends(require_roles("methodist","branch_admin","admin"))])
async def get_rooms(
    only_active: bool = False,
    branch_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    branch_filter: int | None = Depends(get_branch_filter),
):
    effective = branch_filter if branch_filter is not None else branch_id
    return await room_service.list_rooms(db, only_active=only_active, branch_id=effective)


@router.get("/{room_id}", response_model=RoomRead, dependencies=[Depends(require_roles("methodist","branch_admin","admin"))])
async def get_room_by_id(room_id: int, db: AsyncSession = Depends(get_db)):
    room = await room_service.get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    return room


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
async def add_room(data: RoomCreate, db: AsyncSession = Depends(get_db)):
    return await room_service.create_room(db, data)


@router.patch("/{room_id}", response_model=RoomRead)
async def edit_room(room_id: int, data: RoomUpdate, db: AsyncSession = Depends(get_db)):
    room = await room_service.update_room(db, room_id, data)
    if room is None:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    return room
