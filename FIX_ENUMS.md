# Исправление проблемы с ENUM типами

## Проблема
ENUM типы не были созданы в базе данных, из-за чего API выдаёт ошибку:
```
type "lot_status_enum" does not exist
```

## Решение

### Вариант 1: Через Railway CLI (рекомендуется)

1. Подключитесь к базе данных через Railway:
```bash
railway connect postgres
```

2. Выполните SQL скрипт:
```bash
\i create_enums.sql
```

Или скопируйте содержимое `create_enums.sql` и выполните в psql.

### Вариант 2: Через Railway Dashboard

1. Откройте Railway Dashboard
2. Перейдите в сервис PostgreSQL
3. Откройте вкладку "Data" или "Query"
4. Скопируйте и выполните содержимое файла `create_enums.sql`

### Вариант 3: Пересоздать миграцию

Если ENUM типы не создались из-за ошибки в миграции:

1. Откатите миграцию:
```bash
railway run alembic downgrade -1
```

2. Примените миграцию заново:
```bash
railway run alembic upgrade head
```

## Проверка

После выполнения SQL скрипта проверьте, что ENUM типы созданы:

```sql
SELECT typname FROM pg_type WHERE typname LIKE '%_enum';
```

Должны быть созданы:
- seller_status_enum
- lot_delivery_type_enum
- lot_status_enum
- deal_status_enum
- dispute_status_enum
- transaction_type_enum
- transaction_status_enum
- withdrawal_status_enum
- notification_type_enum

После этого перезапустите приложение на Railway.
