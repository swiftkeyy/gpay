# 🔧 Фикс таблицы bot_settings

## Проблема
Таблица `bot_settings` отсутствует в базе данных, хотя модель существует в коде.

## Решение

### Вариант 1: Быстрый фикс (рекомендуется) ✅

Таблица `bot_settings` уже добавлена в миграцию. Просто сбрось базу и перезапусти:

1. **Зайди в Railway** → PostgreSQL → Query
2. **Скопируй и выполни** содержимое файла `reset_and_migrate.sql`
3. **Redeploy** сервис gpay в Railway

После этого миграция создаст ВСЕ таблицы включая `bot_settings`.

---

### Вариант 2: Создать таблицу вручную (если не хочешь терять данные)

Если в базе уже есть важные данные, выполни только создание таблицы:

```sql
-- Создать таблицу bot_settings
CREATE TABLE bot_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL,
    value TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_bot_settings_key UNIQUE (key)
);

CREATE INDEX ix_bot_settings_key ON bot_settings(key);
```

Затем Redeploy в Railway.

---

## Что было сделано

✅ Добавлена таблица `bot_settings` в миграцию `20260418_000001_initial_schema.py`
✅ Модель `BotSetting` уже существует в `app/models/entities.py`
✅ Создан скрипт для сброса базы `reset_and_migrate.sql`

---

## Проверка после деплоя

1. Открой Deploy Logs в Railway
2. Должно быть:
   ```
   📦 Применяем Alembic миграции...
   INFO  [alembic.runtime.migration] Running upgrade  -> 20260418_000001, initial schema
   ✅ Всё готово. Запускаем бот...
   ```

3. Бот должен запуститься без ошибки `relation "bot_settings" does not exist`

---

## Если всё равно не работает

Проверь, что в Railway Variables есть:
- `DATABASE_URL` (автоматически от PostgreSQL)
- `REDIS_URL` (автоматически от Redis)
- `BOT_TOKEN` (от BotFather)
- `SECRET_KEY` (любая строка минимум 32 символа)

---

Made with ❤️ by Kiro AI
