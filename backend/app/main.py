from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import roles, leads, employees
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

# CORS — на всякий случай оставляем (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры API
app.include_router(roles.router)
app.include_router(leads.router)
app.include_router(employees.router)

@app.get("/")
async def root():
    return {"message": "CRM Music School API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности: пингуем БД."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.scalar()
        return {"status": "ok", "database": "connected", "test_query": row}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}
