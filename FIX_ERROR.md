# 🔧 Исправление ошибки AttributeError

## ❌ Ошибка
```
AttributeError: 'NoneType' object has no attribute 'id'
```

## ✅ Что исправлено

Файл `app/handlers/user/profile.py` обновлен - добавлена проверка на `None`.

---

## 🚀 Что делать дальше

### Шаг 1: Загрузи исправленный файл на сервер

Загрузи обновленный файл `app/handlers/user/profile.py` на bothost.ru через FTP или панель управления.

### Шаг 2: Перезапусти бота

В панели bothost.ru:
1. Останови бота
2. Запусти снова

Или через SSH:
```bash
pkill -f "python -m app.main"
python -m app.main
```

### Шаг 3: Проверь базу данных

**ВАЖНО:** Эта ошибка возникает когда пользователь не найден в БД.

Запусти скрипт проверки:
```bash
python check_db.py
```

Он покажет:
- ✅ Какие таблицы созданы
- ✅ Есть ли новые таблицы маркетплейса
- ✅ Сколько пользователей в БД

### Шаг 4: Примени миграцию (если не применена)

Если скрипт показал что таблиц маркетплейса нет:

```bash
# Проверь текущую версию
alembic current

# Должно быть: 20260414_000001

# Если нет - примени миграцию
alembic upgrade head
```

### Шаг 5: Создай тестового пользователя

Если в БД нет пользователей, создай через SQL:

```sql
-- Подключись к БД
psql -d your_database

-- Создай пользователя
INSERT INTO users (telegram_id, username, first_name, balance)
VALUES (123456789, 'test_user', 'Test', 0.00);
```

Замени `123456789` на свой Telegram ID (узнай у @userinfobot).

---

## 🔍 Диагностика

### Проверка 1: Бот запускается?
```bash
python -m app.main
```

Должно быть:
```
INFO | Bot started successfully
```

### Проверка 2: Миграция применена?
```bash
alembic current
```

Должно быть:
```
20260414_000001 (head)
```

### Проверка 3: Таблицы созданы?
```bash
python check_db.py
```

Должно показать все таблицы маркетплейса.

### Проверка 4: Пользователь создается?

Отправь боту `/start` и проверь в БД:
```sql
SELECT * FROM users ORDER BY created_at DESC LIMIT 1;
```

---

## 🆘 Если ошибка осталась

### Вариант 1: Middleware не создает пользователя

Проверь файл `app/middlewares/user_context.py`:
```python
# Должна быть логика создания пользователя
if user is None:
    user = User(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        ...
    )
    session.add(user)
    await session.flush()
```

### Вариант 2: Проблема с подключением к БД

Проверь `.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

Проверь подключение:
```bash
psql -d your_database -c "SELECT 1"
```

### Вариант 3: Старая версия кода на сервере

Убедись что загрузил ВСЕ обновленные файлы:
- `app/models/entities.py`
- `app/models/enums.py`
- `app/repositories/*`
- `app/services/*`
- `app/handlers/user/profile.py` (исправленный)
- `app/handlers/user/seller.py`
- `app/handlers/user/deals.py`
- `app/main.py`

---

## ✅ Чеклист исправления

- [ ] Загружен исправленный `profile.py`
- [ ] Бот перезапущен
- [ ] Миграция применена (`alembic upgrade head`)
- [ ] Таблицы созданы (проверено через `check_db.py`)
- [ ] Пользователь создается при `/start`
- [ ] Ошибка больше не появляется

---

## 📞 Если нужна помощь

Пришли результаты:
1. `alembic current` - текущая версия миграции
2. `python check_db.py` - состояние БД
3. Логи бота при запуске
4. Новый текст ошибки (если есть)

И я помогу дальше! 🚀
