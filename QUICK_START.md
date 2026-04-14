# Быстрый старт - Обновление до маркетплейса

## 🚀 За 5 минут

### 1. Бэкап (ОБЯЗАТЕЛЬНО!)
```bash
# Сделайте бэкап базы данных
pg_dump your_database > backup_$(date +%Y%m%d).sql
```

### 2. Остановите бота
```bash
# В панели bothost.ru или
pkill -f "python -m app.main"
```

### 3. Примените миграцию
```bash
cd /path/to/your/bot
source venv/bin/activate  # если используете venv
alembic upgrade head
```

### 4. Добавьте тестовые данные (опционально)
```bash
python seed_marketplace.py
```

### 5. Запустите бота
```bash
python -m app.main
# Или через панель bothost.ru
```

## ✅ Проверка

### Тест 1: Регистрация продавца
```
1. Отправьте боту: /seller
2. Введите название магазина
3. Проверьте, что магазин создан
```

### Тест 2: Просмотр лотов
```
1. Выберите любой товар в каталоге
2. Должны увидеть список лотов от разных продавцов
3. Выберите лот и посмотрите детали
```

### Тест 3: Покупка (если есть баланс)
```
1. Пополните баланс через админку или SQL:
   UPDATE users SET balance = 1000 WHERE telegram_id = YOUR_TG_ID;
2. Купите товар
3. Проверьте сделку: /deals
```

## 🔧 Быстрые команды SQL

### Активировать продавца:
```sql
UPDATE sellers SET status = 'active' WHERE user_id = (
    SELECT id FROM users WHERE telegram_id = YOUR_TG_ID
);
```

### Пополнить баланс:
```sql
UPDATE users SET balance = balance + 1000 WHERE telegram_id = YOUR_TG_ID;
```

### Посмотреть всех продавцов:
```sql
SELECT s.id, s.shop_name, s.status, u.username 
FROM sellers s 
JOIN users u ON s.user_id = u.id;
```

### Посмотреть все лоты:
```sql
SELECT l.id, l.title, l.price, l.status, s.shop_name 
FROM lots l 
JOIN sellers s ON l.seller_id = s.id 
WHERE l.is_deleted = false;
```

## 📋 Чеклист после установки

- [ ] Миграция применена успешно
- [ ] Бот запускается без ошибок
- [ ] Команда `/seller` работает
- [ ] Лоты отображаются в каталоге
- [ ] Можно создать сделку
- [ ] Чат в сделке работает
- [ ] Транзакции записываются
- [ ] Уведомления приходят

## ⚠️ Если что-то не работает

### Ошибка импорта:
```bash
pip install -r requirements.txt --upgrade
```

### Ошибка миграции:
```bash
# Проверьте текущую версию
alembic current

# Если нужно, откатите
alembic downgrade -1

# Попробуйте снова
alembic upgrade head
```

### Бот не запускается:
```bash
# Проверьте логи
tail -f logs/bot.log

# Или запустите в режиме отладки
python -m app.main
```

### Таблицы не созданы:
```bash
# Проверьте в PostgreSQL
psql -d your_database -c "\dt"

# Должны быть таблицы: sellers, lots, deals, transactions и т.д.
```

## 🎯 Следующие шаги

1. **Настройте комиссии** - отредактируйте `commission_percent` для продавцов
2. **Добавьте админ-хендлеры** - для управления продавцами и спорами
3. **Настройте cron-задачи** - для автозавершения сделок
4. **Интегрируйте платежи** - для пополнения баланса
5. **Настройте вывод средств** - для продавцов

## 📚 Документация

- `MARKETPLACE_FEATURES.md` - полное описание функций
- `UPGRADE_INSTRUCTIONS.md` - детальные инструкции
- `MODERNIZATION_PLAN.md` - план развития

## 💬 Основные команды бота

- `/start` - главное меню
- `/seller` - меню продавца
- `/deals` - список сделок
- `/admin` - админ-панель (для админов)

## 🎉 Готово!

Ваш бот теперь работает как полноценный маркетплейс в стиле FunPay и PlayerOK!
