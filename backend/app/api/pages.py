from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pages"])

# В контейнере фронт лежит в /app/frontend
FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"


def _html(filename: str) -> FileResponse:
    return FileResponse(FRONTEND_DIR / filename, media_type="text/html")


@router.get("/login")
async def page_login():
    """Веб-страница входа."""
    return _html("login.html")


@router.get("/users")
async def page_users():
    """Веб-страница управления пользователями."""
    return _html("users.html")


@router.get("/leads")
async def page_leads():
    """Веб-страница создания лида."""
    return _html("lead-new.html")
