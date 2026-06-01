from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pages"])

FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"


def _html(rel_path: str) -> FileResponse:
    return FileResponse(FRONTEND_DIR / rel_path, media_type="text/html")


@router.get("/login", summary="Вход")
async def page_login():
    return _html("pages/login/login.html")


@router.get("/users", summary="Пользователи")
async def page_users():
    return _html("pages/users/users.html")


@router.get("/leads", summary="Новый лид")
async def page_leads():
    return _html("pages/lead-new/lead-new.html")


@router.get("/convert", summary="Конверсия лида в ученика")
async def page_convert():
    return _html("pages/convert/convert.html")


@router.get("/plans", summary="Каталог абонементов")
async def page_plans():
    return _html("pages/plans/plans.html")


@router.get("/subscription-new", summary="Оформление абонемента")
async def page_subscription_new():
    return _html("pages/subscription-new/subscription-new.html")


@router.get("/payment-new", summary="Фиксация оплаты")
async def page_payment_new():
    return _html("pages/payment-new/payment-new.html")


@router.get("/student-finance", summary="Абонементы и оплаты ученика")
async def page_student_finance():
    return _html("pages/student-finance/student-finance.html")


@router.get("/confirm-payments", summary="Подтверждение оплат")
async def page_confirm_payments():
    return _html("pages/confirm-payments/confirm-payments.html")
