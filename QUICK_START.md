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

```bash
# Установи Railway CLI (если еще не установлен)
npm install -g @railway/cli

# Войди в Railway
railway login

# Подключись к проекту
railway link

# Добавь себя админом
railway run python add_admin.py add YOUR_TELEGRAM_ID super_admin
```

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
