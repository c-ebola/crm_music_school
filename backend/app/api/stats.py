from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.services import stats_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/dashboard", dependencies=[Depends(require_roles("admin", "branch_admin"))])
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    return await stats_service.dashboard(db)
