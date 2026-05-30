from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.subscription_plan import (
    SubscriptionPlanCreate, SubscriptionPlanRead, SubscriptionPlanUpdate,
)
from app.services import subscription_plan_service

router = APIRouter(prefix="/api/subscription-plans", tags=["subscription-plans"])


@router.get("", response_model=list[SubscriptionPlanRead])
async def get_plans(only_active: bool = False, db: AsyncSession = Depends(get_db)):
    return await subscription_plan_service.list_plans(db, only_active=only_active)


@router.get("/{plan_id}", response_model=SubscriptionPlanRead)
async def get_plan_by_id(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan = await subscription_plan_service.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Абонемент не найден")
    return plan


@router.post("", response_model=SubscriptionPlanRead, status_code=status.HTTP_201_CREATED)
async def add_plan(data: SubscriptionPlanCreate, db: AsyncSession = Depends(get_db)):
    return await subscription_plan_service.create_plan(db, data)


@router.patch("/{plan_id}", response_model=SubscriptionPlanRead)
async def edit_plan(plan_id: int, data: SubscriptionPlanUpdate, db: AsyncSession = Depends(get_db)):
    plan = await subscription_plan_service.update_plan(db, plan_id, data)
    if plan is None:
        raise HTTPException(status_code=404, detail="Абонемент не найден")
    return plan
