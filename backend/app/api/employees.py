from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.employee import EmployeeCreate, EmployeeRead
from app.services import employee_service

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeRead])
async def get_employees(db: AsyncSession = Depends(get_db)):
    """Список всех сотрудников."""
    return await employee_service.list_employees(db)


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee_by_id(employee_id: int, db: AsyncSession = Depends(get_db)):
    """Получить сотрудника по ID."""
    emp = await employee_service.get_employee(db, employee_id)
    if emp is None:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return emp


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def add_employee(data: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    """Создать нового сотрудника."""
    try:
        return await employee_service.create_employee(db, data)
    except employee_service.RoleNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except employee_service.EmailAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))