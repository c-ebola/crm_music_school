from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles, get_branch_filter
from app.db.session import get_db
from app.schemas.audit import AuditLogRead
from app.services import audit_service

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogRead],
            dependencies=[Depends(require_roles("branch_admin", "admin"))])
async def get_audit(
    method: str | None = None,
    actor_user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    branch_filter: int | None = Depends(get_branch_filter),
):
    """Журнал действий. Админ филиала видит только свой филиал, админ сети — всё"""
    return await audit_service.list_audit(
        db,
        branch_id=branch_filter,
        method=method,
        actor_user_id=actor_user_id,
        date_from=date_from,
        date_to=date_to,
        limit=min(limit, 500),
        offset=offset,
    )