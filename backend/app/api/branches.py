from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_active_user, require_admin
from app.models.branch import BranchKind
from app.schemas.branch import BranchCreate, BranchRead, BranchUpdate
from app.services import branch_service

router = APIRouter(prefix="/api/branches", tags=["branches"])


@router.get("", response_model=list[BranchRead],
            dependencies=[Depends(get_current_active_user)])
async def get_branches(kind: BranchKind | None = None, only_active: bool = False,
                       db: AsyncSession = Depends(get_db)):
    return await branch_service.list_branches(db, kind=kind, only_active=only_active)


@router.post("", response_model=BranchRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
async def create_branch(data: BranchCreate, db: AsyncSession = Depends(get_db)):
    return await branch_service.create_branch(db, data)


@router.patch("/{branch_id}", response_model=BranchRead,
              dependencies=[Depends(require_admin)])
async def update_branch(branch_id: int, data: BranchUpdate, db: AsyncSession = Depends(get_db)):
    b = await branch_service.update_branch(db, branch_id, data)
    if b is None:
        raise HTTPException(status_code=404, detail="Филиал не найден")
    return b


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
async def delete_branch(branch_id: int, db: AsyncSession = Depends(get_db)):
    ok = await branch_service.delete_branch(db, branch_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Филиал не найден")
