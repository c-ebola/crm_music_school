from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.employee import Gender, EmployeeStatus
from app.schemas.role import RoleRead


class EmployeeBase(BaseModel):
    """Общие поля сотрудника."""
    # Личные
    last_name: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    birth_date: date | None = None
    gender: Gender | None = None

    # Контакты
    email: EmailStr
    phone: str | None = Field(None, max_length=50)
    telegram: str | None = Field(None, max_length=100)

    # Должностные
    role_id: int
    branch: str | None = Field(None, max_length=100)
    hire_date: date
    disciplines: str | None = Field(None, max_length=300)

    notes: str | None = None


class EmployeeCreate(EmployeeBase):
    """Что принимаем при создании сотрудника."""
    pass


class EmployeeRead(EmployeeBase):
    """Что отдаём клиенту."""
    id: int
    status: EmployeeStatus
    full_name: str
    role: RoleRead   # вложенная схема — клиент сразу видит имя роли, а не только id
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)