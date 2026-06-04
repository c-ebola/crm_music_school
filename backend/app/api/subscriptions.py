from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionRead, SubscriptionUpdate,
)
from app.services import subscription_service

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("", response_model=list[SubscriptionRead], dependencies=[Depends(require_roles("accountant","admin"))])
async def get_subscriptions(student_id: int | None = None, db: AsyncSession = Depends(get_db)):
    return await subscription_service.list_subscriptions(db, student_id=student_id)


@router.get("/{sub_id}", response_model=SubscriptionRead, dependencies=[Depends(require_roles("accountant","admin"))])
async def get_subscription_by_id(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await subscription_service.get_subscription(db, sub_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Абонемент не найден")
    return sub


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("accountant"))])
async def add_subscription(data: SubscriptionCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await subscription_service.create_subscription(db, data)
    except subscription_service.StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except subscription_service.PlanNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except subscription_service.SubscriptionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{sub_id}", response_model=SubscriptionRead, dependencies=[Depends(require_roles("accountant"))])
async def edit_subscription(sub_id: int, data: SubscriptionUpdate, db: AsyncSession = Depends(get_db)):
    sub = await subscription_service.update_subscription(db, sub_id, data)
    if sub is None:
        raise HTTPException(status_code=404, detail="Абонемент не найден")
    return sub
