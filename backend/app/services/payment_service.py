from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus
from app.models.subscription import Subscription
from app.schemas.payment import PaymentCreate, PaymentUpdate


class PaymentError(Exception):
    pass


class SubscriptionNotFoundError(PaymentError):
    pass


def _to_read_dict(p: Payment) -> dict:
    student_name = None
    plan_name = None
    if p.subscription is not None:
        sub = p.subscription
        if sub.student is not None:
            student_name = sub.student.student_full_name or sub.student.contact_full_name
        if sub.plan is not None:
            plan_name = sub.plan.name
    return {
        "id": p.id,
        "subscription_id": p.subscription_id,
        "amount": float(p.amount),
        "payment_date": p.payment_date,
        "method": p.method,
        "status": p.status,
        "comment": p.comment,
        "confirmed_by": p.confirmed_by,
        "confirmed_at": p.confirmed_at,
        "student_name": student_name,
        "plan_name": plan_name,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


async def list_payments(
    db: AsyncSession,
    subscription_id: int | None = None,
    student_id: int | None = None,
    status: PaymentStatus | None = None,
) -> list[dict]:
    query = select(Payment)
    if subscription_id is not None:
        query = query.where(Payment.subscription_id == subscription_id)
    if student_id is not None:
        sub_ids = select(Subscription.id).where(Subscription.student_id == student_id)
        query = query.where(Payment.subscription_id.in_(sub_ids))
    if status is not None:
        query = query.where(Payment.status == status)
    query = query.order_by(Payment.created_at.desc())
    result = await db.execute(query)
    return [_to_read_dict(p) for p in result.scalars().all()]


async def get_payment(db: AsyncSession, payment_id: int) -> dict | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    p = result.scalar_one_or_none()
    return _to_read_dict(p) if p else None


async def create_payment(db: AsyncSession, data: PaymentCreate) -> dict:
    sub = await db.get(Subscription, data.subscription_id)
    if sub is None:
        raise SubscriptionNotFoundError("Абонемент не найден")

    payment = Payment(
        subscription_id=sub.id,
        amount=data.amount,
        payment_date=data.payment_date or date.today(),
        method=data.method,
        comment=data.comment,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return _to_read_dict(payment)


async def update_payment(db: AsyncSession, payment_id: int, data: PaymentUpdate) -> dict | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    await db.commit()
    await db.refresh(payment)
    return _to_read_dict(payment)


async def confirm_payment(db: AsyncSession, payment_id: int, admin_id: int) -> dict | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        return None
    payment.status = PaymentStatus.confirmed
    payment.confirmed_by = admin_id
    payment.confirmed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(payment)
    return _to_read_dict(payment)


async def reject_payment(db: AsyncSession, payment_id: int, admin_id: int) -> dict | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        return None
    payment.status = PaymentStatus.rejected
    payment.confirmed_by = admin_id
    payment.confirmed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(payment)
    return _to_read_dict(payment)