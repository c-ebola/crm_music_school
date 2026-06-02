from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api import (auth, leads, 
pages, roles, users, subscription_plans, subscriptions, 
payments, disciplines
)
from app.core.config import settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[startup] {settings.app_name} запускается")
    yield
    print(f"[shutdown] {settings.app_name} останавливается")
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API-маршруты ---
app.include_router(roles.router)
app.include_router(leads.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subscription_plans.router)
app.include_router(subscriptions.router)
app.include_router(payments.router)
app.include_router(disciplines.router)

@app.get("/health", tags=["system"])
async def health_check():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.scalar()
        return {"status": "ok", "database": "connected", "test_query": row}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}


# --- Веб-маршруты (чистые URL без .html) ---
# Регистрируются ДО монтирования статики, чтобы имели приоритет
app.include_router(pages.router)

# --- Статика фронта (CSS, JS, .html файлы) ---
# Монтируется ПОСЛЕДНЕЙ как catch-all
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="frontend",
    )
