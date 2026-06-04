from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin, get_current_active_user
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserRead], dependencies=[Depends(require_admin)])
async def get_users(db: AsyncSession = Depends(get_db)):
    """Список пользователей (только админ)."""
    return await user_service.list_users(db)


@router.post(
    "", response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создать пользователя (только админ)."""
    try:
        return await user_service.create_user(db, data)
    except user_service.RoleNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except user_service.EmailAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/teachers", response_model=list[UserRead], dependencies=[Depends(get_current_active_user)])
async def get_teachers(db: AsyncSession = Depends(get_db)):
    """Список преподавателей для выпадающих списков."""
    from sqlalchemy import select
    from app.models.user import User
    from app.models.role import Role
    result = await db.execute(
        select(User).join(Role).where(Role.code == "teacher")
    )
    return list(result.scalars().all())