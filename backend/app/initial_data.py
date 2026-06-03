import asyncio

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.role import Role
from app.models.user import User

# (email, пароль, фамилия, имя, код_роли, суперпользователь)
SEED_USERS = [
    (settings.first_admin_email, settings.first_admin_password,
     "Администратор", "Системный", "admin", True),
    ("manager1@crm.com", "password123", "Соколова", "Мария", "manager", False),
    ("manager2@crm.com", "password123", "Орлов", "Игорь", "manager", False),
    ("teacher1@crm.com", "password123", "Петров", "Андрей", "teacher", False),
    ("teacher2@crm.com", "password123", "Кузнецова", "Елена", "teacher", False),
    ("methodist1@crm.com", "password123", "Васильева", "Ольга", "methodist", False),
]


async def main() -> None:
    try:
        async with AsyncSessionLocal() as db:
            roles = (await db.execute(select(Role))).scalars().all()
            role_by_code = {r.code: r for r in roles}

            created = 0
            for email, pwd, last, first, role_code, is_super in SEED_USERS:
                role = role_by_code.get(role_code)
                if role is None:
                    print(f"[seed] роль '{role_code}' не найдена, пропуск {email}")
                    continue

                exists = await db.execute(select(User).where(User.email == email))
                if exists.scalar_one_or_none() is not None:
                    continue

                db.add(User(
                    email=email,
                    hashed_password=hash_password(pwd),
                    last_name=last,
                    first_name=first,
                    role_id=role.id,
                    is_active=True,
                    is_superuser=is_super,
                ))
                created += 1

            if created:
                await db.commit()
                print(f"[seed] создано пользователей: {created}")
            else:
                print("[seed] пользователи уже есть, пропуск")
    except SQLAlchemyError as e:
        print(f"[seed] пропуск создания пользователей (БД не готова): {e}")


if __name__ == "__main__":
    asyncio.run(main())
