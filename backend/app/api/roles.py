from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.schemas.role import RoleCreate, RoleRead
from app.services import role_service

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=list[RoleRead], dependencies=[Depends(require_roles("admin"))])
async def get_roles(db: AsyncSession = Depends(get_db)):
    """Получить список всех ролей."""
    roles = await role_service.list_roles(db)
    return roles


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def add_role(data: RoleCreate, db: AsyncSession = Depends(get_db)):
    """Создать новую роль."""
    try:
        role = await role_service.create_role(db, data)
    except role_service.RoleAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return role