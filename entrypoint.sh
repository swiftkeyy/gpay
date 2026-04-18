#!/bin/sh
set -e

echo "🚀 Запуск gpay маркетплейса (модернизированная версия)..."

# === Миграции (защита от DuplicateObject уже должна быть в миграциях) ===
echo "📦 Применяем Alembic миграции..."
alembic upgrade head

# === Опционально: сидирование (раскомментируй только если нужно каждый раз) ===
# echo "🌱 Запускаем seed.py..."
# python seed.py

echo "✅ Всё готово. Запускаем Game Pay API и бот..."

# Запуск упрощенного FastAPI в фоне
uvicorn api.main_simple:app --host 0.0.0.0 --port ${PORT:-8000} &

# Запуск упрощенного бота (только приветствие + кнопка Mini App)
exec python -m app.main_simple_bot
