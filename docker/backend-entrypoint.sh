#!/bin/sh
# Скрипт запуска бэкенда: ждёт БД, применяет миграции, запускает приложение
set -e

echo "[entrypoint] Ожидание готовности базы данных ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q; do
    echo "[entrypoint] БД пока недоступна, ждём 2 секунды..."
    sleep 2
done

echo "[entrypoint] БД готова. Применяем миграции Alembic..."
cd /app/backend
uv run alembic upgrade head

echo "[entrypoint] Создаём первого администратора (если нужно)..."
uv run python -m app.initial_data

echo "[entrypoint] Запускаем приложение..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload