from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.role import Role
from app.schemas.employee import EmployeeCreate


class EmployeeError(Exception):
    """Базовая ошибка работы с сотрудниками."""


class EmailAlreadyExistsError(EmployeeError):
    """Сотрудник с таким email уже зарегистрирован."""


class RoleNotFoundError(EmployeeError):
    """Указанная роль не найдена."""


async def list_employees(db: AsyncSession) -> list[Employee]:
    """Список сотрудников, последние сверху."""
    result = await db.execute(
        select(Employee).order_by(Employee.created_at.desc())
    )
    return list(result.scalars().all())


async def get_employee(db: AsyncSession, employee_id: int) -> Employee | None:
    """Получить сотрудника по ID."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    return result.scalar_one_or_none()


async def create_employee(db: AsyncSession, data: EmployeeCreate) -> Employee:
    """Создать сотрудника. Проверяет существование роли и уникальность email."""
    # Проверяем, что роль с таким id существует
    role = await db.get(Role, data.role_id)
    if role is None:
        raise RoleNotFoundError(f"Роль с id={data.role_id} не найдена")

    employee = Employee(**data.model_dump())
    db.add(employee)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise EmailAlreadyExistsError(
            f"Сотрудник с email '{data.email}' уже существует"
        )
    await db.refresh(employee)
    return employee