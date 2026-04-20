#!/bin/bash
set -e

echo "🔄 Running database migrations..."
alembic upgrade head

echo "🌱 Seeding database with initial data..."
python seed_games.py

echo "✅ Database initialization complete!"
