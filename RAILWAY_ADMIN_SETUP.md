# 🚂 Как Добавить Админа на Railway

## Способ 1: Railway CLI (Самый Простой) ✅

### Шаг 1: Установи Railway CLI

```bash
npm install -g @railway/cli
```

Или через PowerShell:
```powershell
iwr https://railway.app/install.ps1 | iex
```

### Шаг 2: Войди в Railway

```bash
railway login
```

Откроется браузер - подтверди вход.

### Шаг 3: Подключись к Проекту

```bash
cd ПРОЕКТЫ/gpay-main
railway link
```

Выбери свой проект из списка.

### Шаг 4: Выполни Команду

```bash
railway run python add_admin.py add YOUR_TELEGRAM_ID super_admin
```

**Пример:**
```bash
railway run python add_admin.py add 5118405789 super_admin
```

✅ Готово! Теперь у тебя есть доступ к админке.

---

## Способ 2: Через SQL (Если CLI не работает)

### Шаг 1: Открой Railway Dashboard

1. Зайди на [railway.app](https://railway.app)
2. Открой свой проект
3. Найди сервис **Postgres**
4. Нажми **Data** → **Query**

### Шаг 2: Узнай User ID

Выполни запрос:
```sql
SELECT id, telegram_id, username, first_name 
FROM users 
WHERE telegram_id = YOUR_TELEGRAM_ID;
```

**Пример:**
```sql
SELECT id, telegram_id, username, first_name 
FROM users 
WHERE telegram_id = 5118405789;
```

Запомни `id` из результата (например, `id = 1`).

### Шаг 3: Добавь Админа

Выполни запрос (замени `USER_ID` на id из предыдущего шага):
```sql
INSERT INTO admins (user_id, role, is_active, created_at)
VALUES (USER_ID, 'super_admin', true, NOW())
ON CONFLICT (user_id) DO UPDATE 
SET role = 'super_admin', is_active = true;
```

**Пример:**
```sql
INSERT INTO admins (user_id, role, is_active, created_at)
VALUES (1, 'super_admin', true, NOW())
ON CONFLICT (user_id) DO UPDATE 
SET role = 'super_admin', is_active = true;
```

✅ Готово!

---

## Способ 3: Через Переменные Окружения (Временный Доступ)

### Шаг 1: Открой Railway Dashboard

1. Зайди на [railway.app](https://railway.app)
2. Открой свой проект
3. Выбери сервис **web** (FastAPI)
4. Перейди в **Variables**

### Шаг 2: Добавь Переменную

Нажми **+ New Variable**:

- **Name:** `SUPER_ADMIN_TG_ID`
- **Value:** `YOUR_TELEGRAM_ID` (например, `5118405789`)

### Шаг 3: Перезапусти Сервис

Нажми **Deploy** → **Redeploy**

✅ Теперь у тебя есть временный доступ (пока переменная установлена).

---

## Проверка Доступа

После выполнения любого способа:

1. Полностью закрой Mini App
2. Открой заново
3. Напиши боту `/admin`
4. Должна открыться админ-панель! 🎉

---

## Troubleshooting

### Railway CLI: "command not found"

**Windows PowerShell:**
```powershell
iwr https://railway.app/install.ps1 | iex
```

**Или через npm:**
```bash
npm install -g @railway/cli
```

### SQL: "User not found"

➡️ Сначала авторизуйся в Mini App, чтобы создался пользователь в БД.

### Переменная не работает

➡️ Убедись, что переменная называется точно `SUPER_ADMIN_TG_ID` и перезапусти сервис.

---

## Рекомендация

Используй **Способ 1 (Railway CLI)** - это самый простой и безопасный способ.

Если CLI не работает, используй **Способ 2 (SQL)**.

**Способ 3** подходит только для временного доступа.
