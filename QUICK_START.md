# 🚀 Быстрый Старт - Добавить Себя Админом

## Шаг 1: Узнай свой Telegram ID

Открой бота [@userinfobot](https://t.me/userinfobot) и нажми `/start`

Или используй [@getmyid_bot](https://t.me/getmyid_bot)

## Шаг 2: Авторизуйся в приложении

1. Открой своего бота Game Pay
2. Нажми "🛍️ Открыть магазин"
3. Дождись загрузки Mini App

## Шаг 3: Добавь себя админом

### Локально (если запускаешь на своем компьютере):

```bash
cd ПРОЕКТЫ/gpay-main
python add_admin.py add YOUR_TELEGRAM_ID super_admin
```

### На Railway:

**Вариант A: Railway CLI (Рекомендуется)**

```bash
# 1. Установи Railway CLI
npm install -g @railway/cli

# Или через PowerShell:
iwr https://railway.app/install.ps1 | iex

# 2. Войди в Railway
railway login

# 3. Подключись к проекту
cd ПРОЕКТЫ/gpay-main
railway link

# 4. Добавь себя админом
railway run python add_admin.py add YOUR_TELEGRAM_ID super_admin
```

**Вариант B: Через SQL в Railway Dashboard**

1. Открой [railway.app](https://railway.app) → твой проект
2. Выбери сервис **Postgres** → **Data** → **Query**
3. Узнай свой user_id:
   ```sql
   SELECT id FROM users WHERE telegram_id = YOUR_TELEGRAM_ID;
   ```
4. Добавь админа (замени USER_ID на результат из шага 3):
   ```sql
   INSERT INTO admins (user_id, role, is_active, created_at)
   VALUES (USER_ID, 'super_admin', true, NOW());
   ```

**Вариант C: Через переменные окружения**

1. Railway Dashboard → твой проект → сервис **web** → **Variables**
2. Добавь переменную:
   - Name: `SUPER_ADMIN_TG_ID`
   - Value: `YOUR_TELEGRAM_ID`
3. Redeploy сервис

📖 Подробнее: **RAILWAY_ADMIN_SETUP.md**

## Шаг 4: Проверь доступ

1. Полностью закрой Mini App
2. Открой заново
3. Напиши боту `/admin`
4. Должна открыться админ-панель! 🎉

---

## Примеры Команд

```bash
# Добавить супер админа
python add_admin.py add 123456789 super_admin

# Добавить модератора
python add_admin.py add 987654321 moderator

# Добавить продавца
python add_admin.py seller 555555555

# Посмотреть всех админов
python add_admin.py list

# Удалить админа
python add_admin.py remove 123456789
```

---

## Роли

- **super_admin** 👑 - Полный доступ ко всему
- **admin** ⚙️ - Управление контентом
- **moderator** 🛡️ - Модерация отзывов и споров
- **security** 🔒 - Блокировка пользователей

---

## Troubleshooting

### "User not found"
➡️ Сначала авторизуйся в Mini App

### Кнопка админки не появилась
➡️ Полностью закрой и открой Mini App заново

### Railway: "command not found"
➡️ Установи Railway CLI: `npm install -g @railway/cli`

---

Подробная документация: **ADMIN_MANAGEMENT.md**
