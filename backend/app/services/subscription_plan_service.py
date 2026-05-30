from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription_plan import SubscriptionPlan
from app.schemas.subscription_plan import SubscriptionPlanCreate, SubscriptionPlanUpdate


async def list_plans(db: AsyncSession, only_active: bool = False) -> list[SubscriptionPlan]:
    query = select(SubscriptionPlan)
    if only_active:
        query = query.where(SubscriptionPlan.is_active.is_(True))
    query = query.order_by(SubscriptionPlan.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_plan(db: AsyncSession, plan_id: int) -> SubscriptionPlan | None:
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def create_plan(db: AsyncSession, data: SubscriptionPlanCreate) -> SubscriptionPlan:
    plan = SubscriptionPlan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def update_plan(
    db: AsyncSession, plan_id: int, data: SubscriptionPlanUpdate
) -> SubscriptionPlan | None:
    plan = await get_plan(db, plan_id)
    if plan is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.commit()
    await db.refresh(plan)
    return plan
