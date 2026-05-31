from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.services import payment_service
from app.core.deps import require_admin
from app.models.payment import PaymentStatus

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("", response_model=list[PaymentRead])
async def get_payments(
    subscription_id: int | None = None,
    student_id: int | None = None,
    status: PaymentStatus | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.list_payments(
        db, subscription_id=subscription_id, student_id=student_id, status=status
    )


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment_by_id(payment_id: int, db: AsyncSession = Depends(get_db)):
    payment = await payment_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Оплата не найдена")
    return payment


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def add_payment(data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await payment_service.create_payment(db, data)
    except payment_service.SubscriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except payment_service.PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{payment_id}", response_model=PaymentRead)
async def edit_payment(payment_id: int, data: PaymentUpdate, db: AsyncSession = Depends(get_db)):
    payment = await payment_service.update_payment(db, payment_id, data)
    if payment is None:
        raise HTTPException(status_code=404, detail="Оплата не найдена")
    return payment


@router.post("/{payment_id}/confirm", response_model=PaymentRead)
async def confirm_payment(payment_id: int, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    payment = await payment_service.confirm_payment(db, payment_id, admin.id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Оплата не найдена")
    return payment


@router.post("/{payment_id}/reject", response_model=PaymentRead)
async def reject_payment(payment_id: int, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    payment = await payment_service.reject_payment(db, payment_id, admin.id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Оплата не найдена")
    return payment