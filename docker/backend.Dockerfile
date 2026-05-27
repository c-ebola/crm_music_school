# Python 3.12 пока что slim
FROM python:3.12-slim

# Настройка работы импортов 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

# Posgresql клиент пакеты , нужные для psycopg2 и сборки asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливка uv в контейнер
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Рабочая директория внутри контейнера
WORKDIR /app

# сначала копируем только файлы зависимостей и ставим пакеты.
# это слой кешируется: если код меняется, а зависимости — нет,
# пересборка будет мгновенной.
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

# копируем сам код приложения
COPY backend/ ./backend/
COPY .env* ./

# Порт FastAPI
EXPOSE 8000

# команда запуска: переход в папку backend и запуск uvicorn
# --reload включаем для разработки (автоперезапуск при изменении кода)
WORKDIR /app/backend
ENV PYTHONPATH=/app/backend
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]