import asyncio

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.branch import Branch, BranchKind
from app.models.role import Role
from app.models.user import User

# ─── Филиалы и площадки ──────────────────────────────────────────────────────
# (name, city, address, kind)
SEED_BRANCHES = [
    ("Центральный",         "Москва", "ул. Ленина, 1",      BranchKind.school),
    ("Северный",            "Москва", "ул. Садовая, 10",    BranchKind.school),
    ("Концертный зал ЦДМ", "Москва", "Театральный пр., 3", BranchKind.venue),
]

# ─── Пользователи ────────────────────────────────────────────────────────────
# (email, пароль, фамилия, имя, код_роли, суперпользователь, имя_филиала|None)
SEED_USERS = [
    (settings.first_admin_email, settings.first_admin_password,
     "Администратор", "Системный", "admin", True, None),
    ("manager1@crm.com",    "password123", "Соколова", "Мария",   "manager",      False, "Центральный"),
    ("manager2@crm.com",    "password123", "Орлов",    "Игорь",   "manager",      False, "Северный"),
    ("teacher1@crm.com",    "password123", "Петров",   "Андрей",  "teacher",      False, "Центральный"),
    ("teacher2@crm.com",    "password123", "Кузнецова","Елена",   "teacher",      False, "Северный"),
    ("methodist1@crm.com",  "password123", "Васильева","Ольга",   "methodist",    False, "Центральный"),
    ("branch1@crm.com",     "password123", "Смирнов",  "Дмитрий", "branch_admin", False, "Центральный"),
    ("accountant1@crm.com", "password123", "Зайцева",  "Анна",    "accountant",   False, None),
]


async def main() -> None:
    try:
        async with AsyncSessionLocal() as db:

            # ── 1. Филиалы (создаём если нет) ──────────────────────────────
            branch_by_name: dict[str, Branch] = {}
            branches_created = 0
            for name, city, address, kind in SEED_BRANCHES:
                row = (await db.execute(
                    select(Branch).where(Branch.name == name)
                )).scalar_one_or_none()
                if row is None:
                    row = Branch(name=name, city=city, address=address,
                                 kind=kind, is_active=True)
                    db.add(row)
                    branches_created += 1
                branch_by_name[name] = row
            if branches_created:
                await db.flush()
                print(f"[seed] создано филиалов/площадок: {branches_created}")
            else:
                print("[seed] филиалы уже есть, пропуск")

            # ── 2. Роли ─────────────────────────────────────────────────────
            roles = (await db.execute(select(Role))).scalars().all()
            role_by_code = {r.code: r for r in roles}

            # ── 3. Пользователи: создать новых + дозаполнить филиал у старых ─
            users_created = 0
            users_updated = 0
            for email, pwd, last, first, role_code, is_super, branch_name in SEED_USERS:
                role = role_by_code.get(role_code)
                if role is None:
                    print(f"[seed] роль '{role_code}' не найдена, пропуск {email}")
                    continue

                branch = branch_by_name.get(branch_name) if branch_name else None

                exists = (await db.execute(
                    select(User).where(User.email == email)
                )).scalar_one_or_none()

                if exists is not None:
                    # пользователь уже есть — проставим филиал, если ещё не задан
                    if branch is not None and exists.branch_id is None:
                        exists.branch_id = branch.id
                        users_updated += 1
                    continue

                db.add(User(
                    email=email,
                    hashed_password=hash_password(pwd),
                    last_name=last,
                    first_name=first,
                    role_id=role.id,
                    is_active=True,
                    is_superuser=is_super,
                    branch_id=branch.id if branch else None,
                ))
                users_created += 1

            await db.commit()
            print(f"[seed] пользователей создано: {users_created}, "
                  f"филиал дозаполнен у: {users_updated}")

    except SQLAlchemyError as e:
        print(f"[seed] пропуск (БД не готова): {e}")


if __name__ == "__main__":
    asyncio.run(main())
