#!/bin/sh
set -e

echo "🚀 Запуск gpay маркетплейса (модернизированная версия)..."

# === Миграции (защита от DuplicateObject уже должна быть в миграциях) ===
echo "📦 Применяем Alembic миграции..."
alembic upgrade head

# === Опционально: сидирование (раскомментируй только если нужно каждый раз) ===
# echo "🌱 Запускаем seed.py..."
# python seed.py

echo "✅ Всё готово. Запускаем FastAPI и бот..."

# Запуск FastAPI в фоне
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} &

# Запуск бота (Telegram bot через aiogram)
exec python -m app.main
