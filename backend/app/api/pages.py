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

@router.get("/schedule", summary="Расписание")
async def page_schedule():
    return _html("pages/schedule/schedule.html")

@router.get("/my-schedule", summary="Моё расписание (неделя)")
async def page_my_schedule():
    return _html("pages/my-schedule/my-schedule.html")

@router.get("/lessons", summary="Уроки: каталог и создание")
async def page_lessons():
    return _html("pages/lessons/lessons.html")

@router.get("/homeworks", summary="Домашние задания")
async def page_homeworks():
    return _html("pages/homeworks/homeworks.html")


@router.get("/student-schedule", summary="Расписание ученика")
async def page_student_schedule():
    return _html("pages/student-schedule/student-schedule.html")

@router.get("/events", summary="Концерты")
async def page_events():
    return _html("pages/events/events.html")

@router.get("/exams", summary="Экзамены: пул")
async def page_exams():
    return _html("pages/exams/exams.html")


@router.get("/commissions", summary="Экзаменационные комиссии")
async def page_commissions():
    return _html("pages/commissions/commissions.html")
