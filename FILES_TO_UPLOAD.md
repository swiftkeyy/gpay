# 📦 Файлы для загрузки на сервер

## ✅ Исправленные файлы (ОБЯЗАТЕЛЬНО загрузить)

### 1. Репозитории
```
app/repositories/__init__.py
```
**Что исправлено:** Убран несуществующий `CatalogRepository`, добавлены правильные импорты

### 2. Хендлеры
```
app/handlers/user/profile.py
```
**Что исправлено:** Добавлена проверка на `None` для `db_user`

---

## 📋 Новые файлы (нужно загрузить)

### Репозитории
```
app/repositories/sellers.py
app/repositories/lots.py
app/repositories/deals.py
app/repositories/transactions.py
```

### Сервисы
```
app/services/seller.py
app/services/lot.py
app/services/deal.py
```

### Хендлеры
```
app/handlers/user/seller.py
app/handlers/user/deals.py
```

### Модели
```
app/models/entities.py (обновлен - добавлены новые модели)
app/models/enums.py (обновлен - добавлены новые enum'ы)
```

### Другие обновленные файлы
```
app/handlers/user/catalog.py (обновлен - добавлена поддержка лотов)
app/keyboards/user.py (обновлен - новые клавиатуры)
app/states/user.py (обновлен - новые состояния)
app/main.py (обновлен - подключены новые роутеры)
```

### Миграция БД
```
alembic/versions/20260414_000001_add_marketplace_features.py
```

### Скрипты
```
seed_marketplace.py
auto_complete_deals.py
cleanup_reservations.py
check_db.py
```

---

## 🚀 Порядок действий

### Шаг 1: Загрузи ИСПРАВЛЕННЫЕ файлы (критично!)
1. `app/repositories/__init__.py`
2. `app/handlers/user/profile.py`

### Шаг 2: Загрузи ВСЕ новые файлы
Используй FTP клиент или панель управления bothost.ru

### Шаг 3: Примени миграцию
```bash
cd /path/to/bot
alembic upgrade head
```

### Шаг 4: Перезапусти бота
Через панель bothost.ru или:
```bash
pkill -f "python -m app.main"
python -m app.main
```

---

## 📁 Структура для загрузки

```
bot/
├── app/
│   ├── handlers/
│   │   ├── user/
│   │   │   ├── profile.py ⚠️ ИСПРАВЛЕН
│   │   │   ├── seller.py ✨ НОВЫЙ
│   │   │   ├── deals.py ✨ НОВЫЙ
│   │   │   └── catalog.py 🔄 ОБНОВЛЕН
│   │   └── admin/
│   ├── repositories/
│   │   ├── __init__.py ⚠️ ИСПРАВЛЕН
│   │   ├── sellers.py ✨ НОВЫЙ
│   │   ├── lots.py ✨ НОВЫЙ
│   │   ├── deals.py ✨ НОВЫЙ
│   │   └── transactions.py ✨ НОВЫЙ
│   ├── services/
│   │   ├── seller.py ✨ НОВЫЙ
│   │   ├── lot.py ✨ НОВЫЙ
│   │   └── deal.py ✨ НОВЫЙ
│   ├── models/
│   │   ├── entities.py 🔄 ОБНОВЛЕН
│   │   └── enums.py 🔄 ОБНОВЛЕН
│   ├── keyboards/
│   │   └── user.py 🔄 ОБНОВЛЕН
│   ├── states/
│   │   └── user.py 🔄 ОБНОВЛЕН
│   └── main.py 🔄 ОБНОВЛЕН
├── alembic/
│   └── versions/
│       └── 20260414_000001_add_marketplace_features.py ✨ НОВЫЙ
├── seed_marketplace.py ✨ НОВЫЙ
├── auto_complete_deals.py ✨ НОВЫЙ
├── cleanup_reservations.py ✨ НОВЫЙ
└── check_db.py ✨ НОВЫЙ
```

---

## ⚡ Быстрая загрузка через FTP

### Используя FileZilla или WinSCP:

1. Подключись к серверу
2. Перейди в папку бота
3. Загрузи файлы с сохранением структуры папок
4. Перезапусти бота

### Используя командную строку (если есть SSH):

```bash
# Загрузи через scp
scp -r app/ user@server:/path/to/bot/
scp -r alembic/ user@server:/path/to/bot/
scp *.py user@server:/path/to/bot/
```

---

## ✅ Проверка после загрузки

```bash
# 1. Проверь что файлы на месте
ls -la app/repositories/__init__.py
ls -la app/handlers/user/profile.py
ls -la app/repositories/sellers.py

# 2. Проверь импорты
python -c "from app.repositories import *; print('OK')"

# 3. Примени миграцию
alembic upgrade head

# 4. Проверь БД
python check_db.py

# 5. Запусти бота
python -m app.main
```

---

## 🆘 Если ошибки остались

Пришли:
1. Текст новой ошибки
2. Результат `alembic current`
3. Результат `python check_db.py`

И я помогу дальше! 🚀
