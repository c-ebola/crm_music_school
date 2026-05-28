import enum
from datetime import date, datetime
from sqlalchemy import String, Integer, Text, Date, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Gender(str, enum.Enum):
    """Пол."""
    male = "male"
    female = "female"
    other = "other"


class EmployeeStatus(str, enum.Enum):
    """Статус сотрудника."""
    active = "active"           # работает
    on_leave = "on_leave"       # в отпуске
    suspended = "suspended"     # отстранён
    dismissed = "dismissed"     # уволен


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Личные данные
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100))
    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender, name="gender"))

    # Контакты
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    telegram: Mapped[str | None] = mapped_column(String(100))

    # Должностные данные
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch: Mapped[str | None] = mapped_column(String(100))
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[EmployeeStatus] = mapped_column(
        Enum(EmployeeStatus, name="employee_status"),
        nullable=False,
        default=EmployeeStatus.active,
    )

    # Для преподавателей — список дисциплин через запятую (пока упрощённо)
    disciplines: Mapped[str | None] = mapped_column(String(300))

    # Прочее
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ORM-связь с Role: позволяет получать employee.role как объект
    role: Mapped["Role"] = relationship("Role", lazy="joined")  # noqa: F821

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, name={self.full_name!r})>"