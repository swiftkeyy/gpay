# Развертывание на bothost.ru

## ✅ Совместимость

Бот полностью совместим с хостингом bothost.ru и не требует специальных настроек.

## 📦 Что нужно на bothost.ru

### Минимальные требования:
- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- 512 MB RAM (рекомендуется 1 GB)
- 1 GB дискового пространства

### Все это уже есть на bothost.ru! ✅

## 🚀 Пошаговое развертывание

### Шаг 1: Подготовка файлов

1. **Загрузите все файлы** через FTP или панель управления bothost.ru
2. **Структура должна быть:**
```
/home/your_user/bot/
├── app/
│   ├── core/
│   ├── db/
│   ├── handlers/
│   ├── keyboards/
│   ├── middlewares/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── states/
│   ├── templates/
│   └── utils/
├── alembic/
│   └── versions/
├── .env
├── requirements.txt
├── seed.py
├── seed_marketplace.py
└── main.py (или app/main.py)
```

### Шаг 2: Настройка окружения

1. **Создайте .env файл** (если еще не создан):
```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
ADMIN_IDS=123456789,987654321
```

2. **На bothost.ru обычно используется:**
```env
DATABASE_URL=postgresql+asyncpg://bothost_user:password@localhost/bothost_db
REDIS_URL=redis://localhost:6379/0
```

### Шаг 3: Установка зависимостей

```bash
# Подключитесь по SSH к bothost.ru
ssh your_user@your_server.bothost.ru

# Перейдите в директорию бота
cd ~/bot

# Активируйте виртуальное окружение (если есть)
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### Шаг 4: Миграция базы данных

```bash
# ВАЖНО: Сделайте бэкап!
pg_dump bothost_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Примените миграции
alembic upgrade head

# Проверьте, что все таблицы созданы
psql -d bothost_db -c "\dt" | grep -E "sellers|lots|deals"
```

### Шаг 5: Заполнение тестовых данных

```bash
# Если база пустая, сначала запустите основной seed
python seed.py

# Затем добавьте маркетплейс данные
python seed_marketplace.py
```

### Шаг 6: Запуск бота

#### Через панель bothost.ru:
1. Откройте панель управления
2. Найдите ваш бот
3. Нажмите "Перезапустить"
4. Проверьте статус - должен быть "Запущен"

#### Через SSH:
```bash
# Остановите старый процесс
pkill -f "python -m app.main"

# Запустите новый
nohup python -m app.main > bot.log 2>&1 &

# Проверьте логи
tail -f bot.log
```

## 🔧 Настройка автозадач на bothost.ru

### Через crontab:

```bash
# Откройте crontab
crontab -e

# Добавьте задачи:
# Автозавершение сделок каждый час
0 * * * * cd ~/bot && ~/venv/bin/python auto_complete_deals.py >> ~/bot/logs/cron.log 2>&1

# Очистка резерваций каждые 15 минут
*/15 * * * * cd ~/bot && ~/venv/bin/python cleanup_reservations.py >> ~/bot/logs/cron.log 2>&1
```

### Через панель bothost.ru:
1. Откройте раздел "Cron задачи"
2. Добавьте новую задачу
3. Укажите команду и расписание
4. Сохраните

## 📊 Мониторинг

### Проверка работы бота:

```bash
# Проверьте процесс
ps aux | grep "python -m app.main"

# Проверьте логи
tail -f ~/bot/bot.log

# Проверьте ошибки
tail -f ~/bot/bot.log | grep ERROR
```

### Проверка базы данных:

```bash
# Подключитесь к PostgreSQL
psql -d bothost_db

# Проверьте количество продавцов
SELECT COUNT(*) FROM sellers;

# Проверьте количество лотов
SELECT COUNT(*) FROM lots WHERE is_deleted = false;

# Проверьте активные сделки
SELECT COUNT(*) FROM deals WHERE status IN ('paid', 'in_progress', 'waiting_confirmation');
```

## 🔒 Безопасность на bothost.ru

### Рекомендации:

1. **Используйте сильные пароли** для БД
2. **Ограничьте доступ** к .env файлу:
```bash
chmod 600 .env
```

3. **Регулярные бэкапы**:
```bash
# Создайте скрипт backup.sh
#!/bin/bash
pg_dump bothost_db > ~/backups/db_$(date +%Y%m%d_%H%M%S).sql
find ~/backups -name "db_*.sql" -mtime +7 -delete

# Добавьте в crontab (каждый день в 3:00)
0 3 * * * ~/bot/backup.sh
```

4. **Мониторинг логов**:
```bash
# Настройте ротацию логов
cat > /etc/logrotate.d/bot << EOF
~/bot/bot.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
EOF
```

## 🐛 Решение проблем на bothost.ru

### Проблема: Бот не запускается

```bash
# Проверьте логи
tail -100 ~/bot/bot.log

# Проверьте права на файлы
ls -la ~/bot/

# Проверьте зависимости
pip list | grep -E "aiogram|sqlalchemy|redis"
```

### Проблема: Ошибки БД

```bash
# Проверьте подключение к PostgreSQL
psql -d bothost_db -c "SELECT 1"

# Проверьте миграции
cd ~/bot && alembic current

# Проверьте таблицы
psql -d bothost_db -c "\dt"
```

### Проблема: Ошибки Redis

```bash
# Проверьте Redis
redis-cli ping

# Проверьте подключение
redis-cli -h localhost -p 6379 ping
```

### Проблема: Высокая нагрузка

```bash
# Проверьте использование ресурсов
top -u your_user

# Проверьте количество запросов к БД
psql -d bothost_db -c "SELECT count(*) FROM pg_stat_activity"

# Оптимизируйте БД
psql -d bothost_db -c "VACUUM ANALYZE"
```

## 📈 Оптимизация для bothost.ru

### 1. Индексы БД (уже созданы в миграции)
```sql
-- Проверьте индексы
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;
```

### 2. Настройка пула соединений

В `app/db/session.py` уже настроено оптимально:
```python
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
)
```

### 3. Кэширование Redis

Используйте Redis для кэширования частых запросов:
```python
# Пример кэширования в сервисах
async def get_active_lots_cached(product_id: int):
    cache_key = f"lots:product:{product_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    lots = await lot_service.get_lots_by_product(product_id)
    await redis.setex(cache_key, 300, json.dumps(lots))  # 5 минут
    return lots
```

## 📞 Поддержка bothost.ru

Если возникли проблемы:
1. Проверьте документацию bothost.ru
2. Обратитесь в поддержку bothost.ru
3. Проверьте форум/чат bothost.ru

## ✅ Чеклист развертывания

- [ ] Файлы загружены на сервер
- [ ] .env файл настроен
- [ ] Зависимости установлены
- [ ] Бэкап БД создан
- [ ] Миграции применены
- [ ] Тестовые данные загружены
- [ ] Бот запущен
- [ ] Cron задачи настроены
- [ ] Логи проверены
- [ ] Тестовая покупка выполнена
- [ ] Мониторинг настроен

## 🎉 Готово!

Ваш маркетплейс-бот успешно развернут на bothost.ru и готов к работе!
