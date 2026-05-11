from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


# подключение к бд, через энджайн запросы в бд
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # debug логи всех SQL-запросы
    pool_pre_ping=True,   # проверка соеднинения
)

# "фабрика сессий"
# Одно сессия одно действие(чтение, добавление, изменения, удаление данных)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # отменяет авто сброс до коммита
    autoflush=False,         # отменяет авто отправку до коммита
)

# функция  get_db реагирующая на каждый http запрос по создаю сессии,
# передает эндпоинт, закрывает сессию
async def get_db():
    """Создаем сессию на один запрос."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()