from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """Журнал действий. Снимок исполнителя хранится строкой,
    чтобы запись оставалась читаемой даже после изменения/удаления пользователя."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    actor_user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    actor_name: Mapped[str | None] = mapped_column(String(200))
    actor_role: Mapped[str | None] = mapped_column(String(80))
    actor_branch: Mapped[str | None] = mapped_column(String(120))
    branch_id: Mapped[int | None] = mapped_column(Integer, index=True)

    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(300), nullable=False)
    action: Mapped[str | None] = mapped_column(String(160))
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )