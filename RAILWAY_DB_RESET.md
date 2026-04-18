# Railway Database Reset Instructions

База данных содержит остатки от неудачных миграций. Нужно очистить её перед запуском новой миграции.

## Вариант 1: Через Railway Dashboard (РЕКОМЕНДУЕТСЯ)

1. Зайди в Railway Dashboard: https://railway.app/
2. Открой свой проект
3. Найди PostgreSQL сервис
4. Перейди в вкладку **Data**
5. Нажми **Query** и выполни следующий SQL:

```sql
-- Удалить все таблицы
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS favorites CASCADE;
DROP TABLE IF EXISTS seller_reviews CASCADE;
DROP TABLE IF EXISTS seller_withdrawals CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS deal_disputes CASCADE;
DROP TABLE IF EXISTS deal_messages CASCADE;
DROP TABLE IF EXISTS lot_stock_items CASCADE;
DROP TABLE IF EXISTS deals CASCADE;
DROP TABLE IF EXISTS lots CASCADE;
DROP TABLE IF EXISTS sellers CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS media_files CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS games CASCADE;
DROP TABLE IF EXISTS carts CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Удалить все enum типы
DROP TYPE IF EXISTS seller_review_status_enum CASCADE;
DROP TYPE IF EXISTS notification_type_enum CASCADE;
DROP TYPE IF EXISTS dispute_status_enum CASCADE;
DROP TYPE IF EXISTS withdrawal_status_enum CASCADE;
DROP TYPE IF EXISTS transaction_status_enum CASCADE;
DROP TYPE IF EXISTS transaction_type_enum CASCADE;
DROP TYPE IF EXISTS deal_status_enum CASCADE;
DROP TYPE IF EXISTS lot_delivery_type_enum CASCADE;
DROP TYPE IF EXISTS lot_status_enum CASCADE;
DROP TYPE IF EXISTS seller_status_enum CASCADE;
DROP TYPE IF EXISTS payment_status_enum CASCADE;
DROP TYPE IF EXISTS payment_provider_enum CASCADE;
DROP TYPE IF EXISTS order_status_enum CASCADE;
DROP TYPE IF EXISTS product_type_enum CASCADE;
DROP TYPE IF EXISTS game_enum CASCADE;
DROP TYPE IF EXISTS admin_role_enum CASCADE;
```

6. После выполнения SQL, Railway автоматически перезапустит приложение
7. Миграции выполнятся автоматически при следующем деплое

## Вариант 2: Пересоздать PostgreSQL сервис (ЯДЕРНЫЙ ВАРИАНТ)

**ВНИМАНИЕ**: Это удалит ВСЕ данные!

1. Зайди в Railway Dashboard
2. Открой свой проект
3. Найди PostgreSQL сервис
4. Нажми на три точки (⋮) → **Remove Service**
5. Добавь новый PostgreSQL сервис:
   - Нажми **+ New**
   - Выбери **Database** → **Add PostgreSQL**
6. Railway автоматически создаст новую переменную `DATABASE_URL`
7. Перезапусти backend сервис - миграции выполнятся автоматически

## Вариант 3: Через Railway CLI (для продвинутых)

```bash
# Установи Railway CLI
npm install -g @railway/cli

# Залогинься
railway login

# Подключись к проекту
railway link

# Подключись к PostgreSQL
railway run psql $DATABASE_URL

# Выполни SQL из Варианта 1
```

## После очистки

После выполнения любого из вариантов:
1. Railway автоматически перезапустит приложение
2. Миграции выполнятся с чистой базой
3. Проверь логи деплоя - должно быть `INFO [alembic.runtime.migration] Running upgrade -> 20260418_000001, initial schema`
4. Если всё прошло успешно, увидишь `INFO [alembic.runtime.migration] Context impl PostgresqlImpl.` без ошибок
