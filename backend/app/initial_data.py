import asyncio

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.role import Role
from app.models.user import User


async def main() -> None:
    try:
        async with AsyncSessionLocal() as db:
            existing = await db.execute(select(User).limit(1))
            if existing.scalar_one_or_none() is not None:
                print("[seed] Пользователи уже есть, создание админа пропущено")
                return

            role_res = await db.execute(select(Role).where(Role.code == "admin"))
            admin_role = role_res.scalar_one_or_none()
            if admin_role is None:
                print("[seed] Роль 'admin' не найдена — пропуск")
                return

            admin = User(
                email=settings.first_admin_email,
                hashed_password=hash_password(settings.first_admin_password),
                last_name="Администратор",
                first_name="Системный",
                role_id=admin_role.id,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            await db.commit()
            print(f"[seed] Создан администратор: {settings.first_admin_email}")
    except SQLAlchemyError as e:
        # Таблицы users ещё нет (миграция не применена) — не валим запуск
        print(f"[seed] Пропуск создания админа (БД не готова): {e}")


if __name__ == "__main__":
    asyncio.run(main())
