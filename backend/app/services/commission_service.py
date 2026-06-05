from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commission import Commission
from app.models.commission_member import CommissionMember
from app.schemas.commission import CommissionCreate, CommissionUpdate, CommissionMemberCreate


def _fio(u) -> str | None:
    if u is None:
        return None
    return " ".join(filter(None, [u.last_name, u.first_name])) or None


def _member_read(m: CommissionMember) -> dict:
    return {"id": m.id, "user_id": m.user_id, "user_name": _fio(m.user), "role": m.role}


def _to_read(c: Commission) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "members": [_member_read(m) for m in c.members],
        "created_at": c.created_at,
    }


async def list_commissions(db: AsyncSession) -> list[dict]:
    res = await db.execute(select(Commission).order_by(Commission.id.desc()))
    return [_to_read(c) for c in res.scalars().all()]


async def get_commission(db: AsyncSession, commission_id: int) -> dict | None:
    res = await db.execute(select(Commission).where(Commission.id == commission_id))
    c = res.scalar_one_or_none()
    return _to_read(c) if c else None


async def create_commission(db: AsyncSession, data: CommissionCreate) -> dict:
    commission = Commission(name=data.name)
    db.add(commission)
    await db.flush()
    for m in data.members:
        db.add(CommissionMember(commission_id=commission.id, user_id=m.user_id, role=m.role))
    await db.commit()
    return await get_commission(db, commission.id)


async def update_commission(db: AsyncSession, commission_id: int, data: CommissionUpdate) -> dict | None:
    res = await db.execute(select(Commission).where(Commission.id == commission_id))
    c = res.scalar_one_or_none()
    if c is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(c, field, value)
    await db.commit()
    return await get_commission(db, commission_id)


async def delete_commission(db: AsyncSession, commission_id: int) -> bool:
    res = await db.execute(select(Commission).where(Commission.id == commission_id))
    c = res.scalar_one_or_none()
    if c is None:
        return False
    await db.delete(c)
    await db.commit()
    return True


async def add_member(db: AsyncSession, commission_id: int, data: CommissionMemberCreate) -> dict | None:
    c = await db.get(Commission, commission_id)
    if c is None:
        return None
    db.add(CommissionMember(commission_id=commission_id, user_id=data.user_id, role=data.role))
    await db.commit()
    return await get_commission(db, commission_id)


async def remove_member(db: AsyncSession, commission_id: int, member_id: int) -> dict | None:
    res = await db.execute(
        select(CommissionMember).where(
            CommissionMember.id == member_id, CommissionMember.commission_id == commission_id
        )
    )
    m = res.scalar_one_or_none()
    if m is None:
        return None
    await db.delete(m)
    await db.commit()
    return await get_commission(db, commission_id)
