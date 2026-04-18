# ✅ Чеклист деплоя на Railway и Vercel

## 📋 Подготовка (5 минут)

### ✅ Шаг 1: Проверьте, что код на GitHub
```bash
git status  # Должно быть: "nothing to commit, working tree clean"
```

✅ **ГОТОВО!** Код уже на GitHub: https://github.com/swiftkeyy/gpay

---

## 🚂 Деплой Backend на Railway (15 минут)

### ✅ Шаг 2: Создайте проект на Railway

1. Откройте https://railway.app
2. Войдите через GitHub
3. Нажмите **"New Project"**
4. Выберите **"Deploy from GitHub repo"**
5. Выберите репозиторий **swiftkeyy/gpay**
6. Railway начнет автоматический деплой

### ✅ Шаг 3: Добавьте PostgreSQL

1. В проекте нажмите **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway создаст базу данных
3. Переменная `DATABASE_URL` добавится автоматически

### ✅ Шаг 4: Добавьте Redis

1. В проекте нажмите **"New"** → **"Database"** → **"Redis"**
2. Railway создаст Redis
3. Переменная `REDIS_URL` добавится автоматически

### ✅ Шаг 5: Настройте переменные окружения

В настройках Backend сервиса добавьте:

```env
# JWT (ОБЯЗАТЕЛЬНО!)
SECRET_KEY=ваш-супер-секретный-ключ-минимум-32-символа
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Telegram Bot (ОБЯЗАТЕЛЬНО!)
BOT_TOKEN=ваш-токен-от-botfather
BOT_USERNAME=ваш_бот_username

# CORS (ОБЯЗАТЕЛЬНО! Обновите после деплоя Frontend)
CORS_ORIGINS=http://localhost:3000

# App Settings
APP_NAME=P2P Marketplace
APP_VERSION=1.0.0
DEBUG=False

# Commission
PLATFORM_COMMISSION_PERCENT=5.0

# Referral
REFERRAL_REWARD_PERCENT=5.0

# Auto-completion
AUTO_COMPLETE_HOURS=72

# Payment Providers (ОПЦИОНАЛЬНО - добавьте когда получите ключи)
YUKASSA_SHOP_ID=ваш-shop-id
YUKASSA_SECRET_KEY=ваш-secret-key

TINKOFF_TERMINAL_KEY=ваш-terminal-key
TINKOFF_SECRET_KEY=ваш-secret-key

CLOUDPAYMENTS_PUBLIC_ID=ваш-public-id
CLOUDPAYMENTS_API_SECRET=ваш-api-secret

CRYPTOBOT_TOKEN=ваш-cryptobot-token
```

### ✅ Шаг 6: Запустите миграции

**Вариант 1: Через Railway CLI**
```bash
npm install -g @railway/cli
railway login
railway link
railway run alembic upgrade head
```

**Вариант 2: Через Railway Dashboard**
1. Откройте **Settings** → **Deploy**
2. В **Start Command** добавьте:
   ```
   alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
3. Нажмите **Save** и **Redeploy**

### ✅ Шаг 7: Получите URL Backend

1. Откройте **Settings** → **Networking**
2. Нажмите **"Generate Domain"**
3. Скопируйте URL (например: `https://gpay-production.up.railway.app`)

**Сохраните этот URL!** Он понадобится для Frontend.

### ✅ Шаг 8: Проверьте Backend

Откройте в браузере:
```
https://ваш-backend.railway.app/docs
```

Должна открыться Swagger документация API.

---

## 🌐 Деплой Frontend на Vercel (10 минут)

### ✅ Шаг 9: Создайте проект на Vercel

1. Откройте https://vercel.com
2. Войдите через GitHub
3. Нажмите **"Add New"** → **"Project"**
4. Импортируйте репозиторий **swiftkeyy/gpay**

### ✅ Шаг 10: Настройте проект

**Framework Preset:** Vite
**Root Directory:** `frontend`
**Build Command:** `npm run build`
**Output Directory:** `dist`

### ✅ Шаг 11: Добавьте переменные окружения

В разделе **Environment Variables** добавьте:

```env
VITE_API_URL=https://ваш-backend.railway.app/api/v1
VITE_WS_URL=wss://ваш-backend.railway.app/api/v1
```

**ВАЖНО:** Замените `ваш-backend.railway.app` на реальный URL из Шага 7!

### ✅ Шаг 12: Деплой

1. Нажмите **"Deploy"**
2. Дождитесь завершения (2-3 минуты)
3. Скопируйте URL Frontend (например: `https://gpay-frontend.vercel.app`)

### ✅ Шаг 13: Обновите CORS на Backend

1. Вернитесь в Railway
2. Откройте настройки Backend сервиса
3. Обновите переменную `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://ваш-frontend.vercel.app
   ```
4. Сохраните и подождите перезапуска

---

## 📱 Настройка Telegram Mini App (5 минут)

### ✅ Шаг 14: Создайте Mini App

1. Откройте @BotFather в Telegram
2. Отправьте `/newapp`
3. Выберите вашего бота
4. Введите название: **P2P Marketplace**
5. Введите описание: **Маркетплейс игровых товаров**
6. Загрузите иконку (640x360 px)
7. Введите URL: `https://ваш-frontend.vercel.app`

### ✅ Шаг 15: Настройте кнопку меню

1. Отправьте `/mybots` в @BotFather
2. Выберите вашего бота
3. Выберите **"Bot Settings"** → **"Menu Button"**
4. Введите URL: `https://ваш-frontend.vercel.app`

---

## 🧪 Тестирование (10 минут)

### ✅ Шаг 16: Проверьте Backend API

```bash
curl https://ваш-backend.railway.app/api/v1/games
```

Должен вернуть список игр (или пустой массив).

### ✅ Шаг 17: Проверьте Frontend

1. Откройте `https://ваш-frontend.vercel.app`
2. Должна открыться главная страница
3. Проверьте, что нет ошибок в консоли браузера

### ✅ Шаг 18: Проверьте Telegram Mini App

1. Откройте вашего бота в Telegram
2. Нажмите на кнопку меню
3. Должно открыться ваше приложение

### ✅ Шаг 19: Проверьте основной флоу

1. Зарегистрируйтесь через Telegram
2. Просмотрите каталог
3. Добавьте товар в корзину
4. Попробуйте оформить заказ

---

## 💳 Настройка платежей (ОПЦИОНАЛЬНО)

### Шаг 20: ЮKassa

1. Зарегистрируйтесь на https://yookassa.ru
2. Получите `SHOP_ID` и `SECRET_KEY`
3. Добавьте в Railway переменные:
   ```
   YUKASSA_SHOP_ID=ваш-shop-id
   YUKASSA_SECRET_KEY=ваш-secret-key
   ```
4. Настройте webhook:
   ```
   https://ваш-backend.railway.app/api/v1/webhooks/yukassa
   ```

### Шаг 21: Tinkoff

1. Зарегистрируйтесь на https://www.tinkoff.ru/business/
2. Получите `TERMINAL_KEY` и `SECRET_KEY`
3. Добавьте в Railway
4. Настройте webhook:
   ```
   https://ваш-backend.railway.app/api/v1/webhooks/tinkoff
   ```

### Шаг 22: CloudPayments

1. Зарегистрируйтесь на https://cloudpayments.ru
2. Получите `PUBLIC_ID` и `API_SECRET`
3. Добавьте в Railway
4. Настройте webhook:
   ```
   https://ваш-backend.railway.app/api/v1/webhooks/cloudpayments
   ```

### Шаг 23: Crypto Bot

1. Создайте приложение на https://t.me/CryptoBot
2. Получите `TOKEN`
3. Добавьте в Railway
4. Настройте webhook:
   ```
   https://ваш-backend.railway.app/api/v1/webhooks/cryptobot
   ```

---

## 📊 Мониторинг

### Railway Logs
```bash
railway logs
```

Или в Dashboard: **Deployments** → **View Logs**

### Vercel Logs
Dashboard → **Deployments** → выберите деплой → **Logs**

---

## 🎉 Готово!

Ваш P2P Marketplace запущен в production!

**Backend:** https://ваш-backend.railway.app
**Frontend:** https://ваш-frontend.vercel.app
**Telegram Bot:** @ваш_бот

---

## 🔄 Обновление

### Backend
```bash
git add .
git commit -m "Update backend"
git push origin main
```
Railway автоматически задеплоит изменения.

### Frontend
```bash
git add .
git commit -m "Update frontend"
git push origin main
```
Vercel автоматически задеплоит изменения.

---

## 🆘 Помощь

### Backend не запускается
1. Проверьте логи: `railway logs`
2. Убедитесь, что все переменные установлены
3. Проверьте, что миграции выполнены

### Frontend не подключается
1. Проверьте CORS на Backend
2. Проверьте `VITE_API_URL` в Vercel
3. Откройте DevTools → Network

### Telegram Mini App не открывается
1. Проверьте URL в BotFather
2. Убедитесь, что Frontend доступен
3. Проверьте HTTPS (должен быть включен)

---

## 💰 Стоимость

**Railway:**
- $5/месяц (Hobby план)
- 500 часов выполнения
- PostgreSQL и Redis включены

**Vercel:**
- Бесплатно для личных проектов
- $20/месяц для коммерческих

**Итого:** ~$5-25/месяц

---

Made with ❤️ by Kiro AI
