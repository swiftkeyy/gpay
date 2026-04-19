#!/bin/sh
set -e

echo "🚀 Запуск Game Pay маркетплейса..."

echo "📦 Применяем миграции..."
alembic upgrade head

echo "🌱 Заполняем базу данных..."
python seed_games.py || echo "⚠️ Seed уже выполнен или произошла ошибка"

echo "✅ Готово. Запускаем FastAPI и бот..."

# Запуск FastAPI в фоне (полная версия с orders)
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} &

# Запуск бота (основной процесс)
exec python -m app.main
