from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pages"])

# В контейнере фронт лежит в /app/frontend
FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"


def _html(filename: str) -> FileResponse:
    return FileResponse(FRONTEND_DIR / filename, media_type="text/html")


@router.get("/", summary="Главная страница")
async def page_index():
    return _html("index.html")


@router.get("/login", summary="Страница входа")
async def page_login():
    return _html("login.html")


@router.get("/users", summary="Управление пользователями")
async def page_users():
    return _html("users.html")


@router.get("/leads", summary="Создание лида")
async def page_leads():
    return _html("lead-new.html")


@router.get("/convert", summary="Конверсия лида в ученика")
async def page_convert():
    return _html("convert.html")


@router.get("/plans", summary="Каталог абонементов")
async def page_plans():
    return _html("plans.html")