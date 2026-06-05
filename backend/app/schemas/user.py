from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.role import RoleRead
from app.schemas.branch import BranchRead


class UserBase(BaseModel):
    email: EmailStr
    last_name: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    role_id: int
    is_active: bool = True
    is_superuser: bool = False
    branch_id: int | None = None


class UserCreate(UserBase):
    """Создание пользователя — с паролем."""
    password: str = Field(..., min_length=8, max_length=72)


class UserRead(UserBase):
    """Чтение — без пароля, с вложенной ролью."""
    id: int
    full_name: str
    role: RoleRead
    branch: BranchRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Ответ при успешном логине."""
    access_token: str
    token_type: str = "bearer"
    user: UserRead
