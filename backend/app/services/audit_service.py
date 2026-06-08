import contextlib
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.services import user_service


async def _snapshot(db: AsyncSession, user_id: int | None) -> dict:
    out = {"actor_user_id": None, "actor_name": None, "actor_role": None,
           "actor_branch": None, "branch_id": None}
    if user_id is None:
        return out
    with contextlib.suppress(Exception):
        user = await user_service.get_user(db, int(user_id))
        if user is not None:
            out["actor_user_id"] = user.id
            out["actor_name"] = user.full_name
            out["branch_id"] = user.branch_id
            with contextlib.suppress(Exception):
                out["actor_role"] = user.role.name if user.role else None
            with contextlib.suppress(Exception):
                out["actor_branch"] = user.branch.name if user.branch else None
    return out


async def record(method: str, path: str, status_code: int, action: str | None,
                 actor_user_id: int | None = None) -> None:
    """Записать одну строку аудита. Открывает собственную сессию,
    делает снимок исполнителя. Безопасно вызывать в try/except."""
    async with AsyncSessionLocal() as db:
        fields = await _snapshot(db, actor_user_id)
        db.add(AuditLog(
            method=method, path=path, status_code=status_code, action=action, **fields,
        ))
        await db.commit()


async def list_audit(
    db: AsyncSession,
    branch_id: int | None = None,
    method: str | None = None,
    actor_user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    q = select(AuditLog)
    if branch_id is not None:
        q = q.where(AuditLog.branch_id == branch_id)
    if method:
        q = q.where(AuditLog.method == method)
    if actor_user_id is not None:
        q = q.where(AuditLog.actor_user_id == actor_user_id)
    if date_from is not None:
        q = q.where(AuditLog.created_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        q = q.where(AuditLog.created_at <= datetime.combine(date_to, time.max))
    q = q.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    return list(res.scalars().all())