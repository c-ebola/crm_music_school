from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserRead
from app.services import user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Вход. Поле username = email."""
    user = await user_service.authenticate(db, form.username, form.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь неактивен")
    token = create_access_token(user.id)
    return Token(access_token=token, user=user)


@router.get("/me", response_model=UserRead)
async def read_me(current: User = Depends(get_current_active_user)):
    """Текущий пользователь по токену."""
    return current
