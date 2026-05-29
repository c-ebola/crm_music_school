from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate


class UserError(Exception):
    pass


class EmailAlreadyExistsError(UserError):
    pass


class RoleNotFoundError(UserError):
    pass


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    role = await db.get(Role, data.role_id)
    if role is None:
        raise RoleNotFoundError(f"Роль с id={data.role_id} не найдена")

    payload = data.model_dump()
    raw_password = payload.pop("password")
    user = User(**payload, hashed_password=hash_password(raw_password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise EmailAlreadyExistsError(
            f"Пользователь с email '{data.email}' уже существует"
        )
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    """Проверить email + пароль. None, если не подходит."""
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
