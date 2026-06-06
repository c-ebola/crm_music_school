from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api import exams, exam_sessions, commissions
from app.api import branches
from app.api import (auth, leads, 
pages, roles, users, subscription_plans, subscriptions, 
payments, disciplines, rooms, lessons, sessions, schedule,
session_students, events,instruments, performances, performance_students,
homeworks, stats, portal

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

# API-маршруты 
app.include_router(roles.router)
app.include_router(leads.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subscription_plans.router)
app.include_router(subscriptions.router)
app.include_router(payments.router)
app.include_router(disciplines.router)
app.include_router(rooms.router)
app.include_router(pages.router)
app.include_router(lessons.router)
app.include_router(sessions.router)
app.include_router(schedule.router)
app.include_router(session_students.router)
app.include_router(events.router)
app.include_router(instruments.router)
app.include_router(performances.router)
app.include_router(performance_students.router)
app.include_router(homeworks.router)
app.include_router(commissions.router)
app.include_router(exams.router)
app.include_router(exam_sessions.router)
app.include_router(exam_sessions.students_router)
app.include_router(branches.router)
app.include_router(stats.router)
app.include_router(portal.router)


@app.get("/health", tags=["system"])
async def health_check():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.scalar()
        return {"status": "ok", "database": "connected", "test_query": row}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}


# веб-маршруты (чистые URL без .html)
# Регистрируются ДО монтирования статики, чтобы имели приоритет
app.include_router(pages.router)

# статика фронта (CSS, JS, .html файлы) 
# Монтируется последний как catch-all
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="frontend",
    )
