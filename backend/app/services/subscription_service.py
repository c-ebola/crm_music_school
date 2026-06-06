from datetime import date, timedelta
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, StudentStatus
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


class SubscriptionError(Exception):
    pass


class StudentNotFoundError(SubscriptionError):
    pass


class PlanNotFoundError(SubscriptionError):
    pass


def _to_read_dict(sub: Subscription) -> dict:
    """Готовим данные для SubscriptionRead с вычисляемыми полями."""
    return {
        "id": sub.id,
        "student_id": sub.student_id,
        "plan_id": sub.plan_id,
        "lessons_total": sub.lessons_total,
        "lessons_used": sub.lessons_used,
        "lessons_remaining": sub.lessons_total - sub.lessons_used,
        "price_paid": float(sub.price_paid),
        "start_date": sub.start_date,
        "end_date": sub.end_date,
        "status": sub.status,
        "student_name": (sub.student.student_full_name or sub.student.contact_full_name) if sub.student else None,
        "plan_name": sub.plan.name if sub.plan else None,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
    }


async def list_subscriptions(db: AsyncSession, student_id: int | None = None) -> list[dict]:
    query = select(Subscription)
    if student_id is not None:
        query = query.where(Subscription.student_id == student_id)
    query = query.order_by(Subscription.created_at.desc())
    result = await db.execute(query)
    return [_to_read_dict(s) for s in result.scalars().all()]


async def get_subscription(db: AsyncSession, sub_id: int) -> dict | None:
    result = await db.execute(select(Subscription).where(Subscription.id == sub_id))
    sub = result.scalar_one_or_none()
    return _to_read_dict(sub) if sub else None


async def create_subscription(db: AsyncSession, data: SubscriptionCreate) -> dict:
    # ученик
    student = await db.get(Lead, data.student_id)
    if student is None or not student.is_student:
        raise StudentNotFoundError("Ученик не найден (или это ещё не ученик)")

    # тариф
    plan = await db.get(SubscriptionPlan, data.plan_id)
    if plan is None:
        raise PlanNotFoundError("Тариф не найден")
    if not plan.is_active:
        raise SubscriptionError("Тариф неактивен, оформление невозможно")

    start = data.start_date or date.today()
    end = start + timedelta(days=plan.duration_days)

    sub = Subscription(
        student_id=student.id,
        plan_id=plan.id,
        lessons_total=plan.lessons_count,   # снимок
        lessons_used=0,
        price_paid=plan.price,              # снимок цены
        start_date=start,
        end_date=end,
        status=SubscriptionStatus.active,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return _to_read_dict(sub)


def _effective_status(sub) -> SubscriptionStatus:
    if sub.status == SubscriptionStatus.cancelled:
        return SubscriptionStatus.cancelled
    if sub.lessons_used >= sub.lessons_total:
        return SubscriptionStatus.used_up
    if sub.end_date < date.today():
        return SubscriptionStatus.expired
    return SubscriptionStatus.active

async def update_subscription(db: AsyncSession, sub_id: int, data: SubscriptionUpdate) -> dict | None:
    result = await db.execute(select(Subscription).where(Subscription.id == sub_id))
    sub = result.scalar_one_or_none()
    if sub is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sub, field, value)
    await db.commit()
    await db.refresh(sub)
    return _to_read_dict(sub)


async def students_needing_renewal(db: AsyncSession) -> list[dict]:
    """Активные ученики без действующего абонемента — очередь на продление."""
    today = date.today()
    students = (await db.execute(
        select(Lead).where(Lead.is_student.is_(True))
    )).scalars().all()
    active = [s for s in students
              if s.student_status not in (StudentStatus.finished, StudentStatus.dropped)]

    subs = (await db.execute(select(Subscription))).scalars().all()
    by_student: dict[int, list] = defaultdict(list)
    for sub in subs:
        by_student[sub.student_id].append(sub)

    out = []
    for s in active:
        subs_s = by_student.get(s.id, [])
        valid = [
            x for x in subs_s
            if x.status != SubscriptionStatus.cancelled
            and x.end_date >= today
            and x.lessons_used < x.lessons_total
        ]
        if valid:
            continue
        if not subs_s:
            reason = "Нет абонемента"
        else:
            last = max(subs_s, key=lambda x: x.end_date)
            if last.lessons_used >= last.lessons_total:
                reason = "Занятия закончились"
            elif last.end_date < today:
                reason = "Истёк срок"
            else:
                reason = "Нет действующего"
        out.append({
            "student_id": s.id,
            "student_name": s.student_full_name or s.contact_full_name,
            "discipline_name": s.discipline.name if s.discipline else None,
            "reason": reason,
        })
    return out