from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.schemas.role import RoleCreate


class RoleAlreadyExistsError(Exception):
    """Роль с таким кодом уже существует."""
    pass


async def list_roles(db: AsyncSession) -> list[Role]:
    """Получить все роли, отсортированные по id."""
    result = await db.execute(select(Role).order_by(Role.id))
    return list(result.scalars().all())


async def create_role(db: AsyncSession, data: RoleCreate) -> Role:
    """Создать новую роль. Бросает RoleAlreadyExistsError при дубликате кода."""
    role = Role(code=data.code, name=data.name)
    db.add(role)
    try:
        await db.commit()
    except IntegrityError:
        # UNIQUE constraint на code сработал
        await db.rollback()
        raise RoleAlreadyExistsError(f"Роль с кодом '{data.code}' уже существует")
    await db.refresh(role)
    return role