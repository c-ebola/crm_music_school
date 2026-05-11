from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """Базовые поля роли — общие для создания и чтения."""
    code: str = Field(..., min_length=1, max_length=50, description="Код роли (латиница)")
    name: str = Field(..., min_length=1, max_length=100, description="Название роли")


class RoleCreate(RoleBase):
    """Схема для создания роли (то, что приходит от клиента)."""
    pass


class RoleRead(RoleBase):
    """Схема для отдачи роли клиенту (с id из БД)."""
    id: int

    # Позволяет Pydantic читать данные напрямую из ORM-объектов
    model_config = ConfigDict(from_attributes=True)