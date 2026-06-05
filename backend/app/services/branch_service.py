from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch, BranchKind
from app.schemas.branch import BranchCreate, BranchUpdate


async def list_branches(db: AsyncSession, kind: BranchKind | None = None,
                        only_active: bool = False):
    q = select(Branch)
    if kind is not None:
        q = q.where(Branch.kind == kind)
    if only_active:
        q = q.where(Branch.is_active.is_(True))
    q = q.order_by(Branch.name.asc())
    res = await db.execute(q)
    return res.scalars().all()


async def get_branch(db: AsyncSession, branch_id: int):
    return await db.get(Branch, branch_id)


async def create_branch(db: AsyncSession, data: BranchCreate):
    b = Branch(**data.model_dump())
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


async def update_branch(db: AsyncSession, branch_id: int, data: BranchUpdate):
    b = await db.get(Branch, branch_id)
    if b is None:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    await db.commit()
    await db.refresh(b)
    return b


async def delete_branch(db: AsyncSession, branch_id: int) -> bool:
    b = await db.get(Branch, branch_id)
    if b is None:
        return False
    await db.delete(b)
    await db.commit()
    return True
