# 🚂 Деплой на Railway

## Подготовка

### 1. Создайте аккаунт на Railway
- Перейдите на https://railway.app
- Зарегистрируйтесь через GitHub

### 2. Установите Railway CLI (опционально)
```bash
npm install -g @railway/cli
railway login
```

## Деплой Backend

### Шаг 1: Создайте новый проект на Railway

1. Войдите в Railway Dashboard
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите ваш репозиторий `gpay-main`

### Шаг 2: Добавьте PostgreSQL

1. В проекте нажмите "New"
2. Выберите "Database" → "PostgreSQL"
3. Railway автоматически создаст базу данных
4. Скопируйте `DATABASE_URL` из переменных окружения

### Шаг 3: Добавьте Redis

1. В проекте нажмите "New"
2. Выберите "Database" → "Redis"
3. Railway автоматически создаст Redis
4. Скопируйте `REDIS_URL` из переменных окружения

### Шаг 4: Настройте переменные окружения

В настройках вашего Backend сервиса добавьте переменные:

```env
# Database (автоматически добавляется Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (автоматически добавляется Railway)
REDIS_URL=${{Redis.REDIS_URL}}

# JWT
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Telegram Bot
BOT_TOKEN=your-telegram-bot-token
BOT_USERNAME=your_bot_username

# Payment Providers
YUKASSA_SHOP_ID=your-yukassa-shop-id
YUKASSA_SECRET_KEY=your-yukassa-secret-key

TINKOFF_TERMINAL_KEY=your-tinkoff-terminal-key
TINKOFF_SECRET_KEY=your-tinkoff-secret-key

CLOUDPAYMENTS_PUBLIC_ID=your-cloudpayments-public-id
CLOUDPAYMENTS_API_SECRET=your-cloudpayments-api-secret

CRYPTOBOT_TOKEN=your-cryptobot-token

# CORS (добавьте ваш frontend домен)
CORS_ORIGINS=https://your-frontend.vercel.app

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
```

### Шаг 5: Запустите миграции

После первого деплоя выполните миграции:

**Через Railway CLI:**
```bash
railway run alembic upgrade head
```

**Или через Railway Dashboard:**
1. Откройте вкладку "Settings"
2. В разделе "Deploy" добавьте команду:
   ```
   alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```

### Шаг 6: Получите URL вашего API

1. Откройте вкладку "Settings"
2. В разделе "Networking" нажмите "Generate Domain"
3. Скопируйте URL (например: `https://your-app.railway.app`)

## Деплой Frontend на Vercel

### Шаг 1: Подготовьте Frontend

1. Обновите `.env` в папке `frontend`:
```env
VITE_API_URL=https://your-backend.railway.app/api/v1
VITE_WS_URL=wss://your-backend.railway.app/api/v1
```

### Шаг 2: Деплой на Vercel

1. Перейдите на https://vercel.com
2. Импортируйте ваш GitHub репозиторий
3. Настройте проект:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

4. Добавьте переменные окружения:
   - `VITE_API_URL`: `https://your-backend.railway.app/api/v1`
   - `VITE_WS_URL`: `wss://your-backend.railway.app/api/v1`

5. Нажмите "Deploy"

### Шаг 3: Обновите CORS на Backend

После деплоя Frontend обновите `CORS_ORIGINS` на Railway:
```
CORS_ORIGINS=https://your-frontend.vercel.app
```

## Настройка Telegram Mini App

### Шаг 1: Создайте Mini App в BotFather

1. Откройте @BotFather в Telegram
2. Отправьте `/newapp`
3. Выберите вашего бота
4. Введите название приложения
5. Введите описание
6. Загрузите иконку (640x360 px)
7. Загрузите GIF/фото для демонстрации
8. Введите URL вашего Frontend: `https://your-frontend.vercel.app`

### Шаг 2: Настройте Webhook для платежей

Для каждого платежного провайдера настройте webhook:

**ЮKassa:**
- URL: `https://your-backend.railway.app/api/v1/webhooks/yukassa`

**Tinkoff:**
- URL: `https://your-backend.railway.app/api/v1/webhooks/tinkoff`

**CloudPayments:**
- URL: `https://your-backend.railway.app/api/v1/webhooks/cloudpayments`

**Crypto Bot:**
- URL: `https://your-backend.railway.app/api/v1/webhooks/cryptobot`

## Проверка деплоя

### 1. Проверьте Backend API
```bash
curl https://your-backend.railway.app/api/v1/health
```

Должен вернуть:
```json
{"status": "ok"}
```

### 2. Проверьте Frontend
Откройте `https://your-frontend.vercel.app` в браузере

### 3. Проверьте Telegram Mini App
1. Откройте вашего бота в Telegram
2. Нажмите на кнопку меню
3. Выберите ваше Mini App
4. Приложение должно открыться

## Мониторинг

### Railway Logs
```bash
railway logs
```

### Vercel Logs
Откройте Dashboard → Deployments → Logs

## Обновление

### Backend
```bash
git add .
git commit -m "Update backend"
git push origin main
```
Railway автоматически задеплоит изменения

### Frontend
```bash
git add .
git commit -m "Update frontend"
git push origin main
```
Vercel автоматически задеплоит изменения

## Troubleshooting

### Backend не запускается
1. Проверьте логи: `railway logs`
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что миграции выполнены

### Frontend не подключается к Backend
1. Проверьте CORS настройки на Backend
2. Убедитесь, что `VITE_API_URL` правильный
3. Проверьте Network в DevTools браузера

### WebSocket не работает
1. Убедитесь, что используете `wss://` (не `ws://`)
2. Проверьте, что Railway поддерживает WebSocket (должен по умолчанию)
3. Проверьте CORS для WebSocket

### Платежи не работают
1. Проверьте webhook URL в настройках провайдера
2. Убедитесь, что webhook использует HTTPS
3. Проверьте логи Railway на наличие ошибок webhook

## Полезные команды

```bash
# Просмотр логов
railway logs

# Выполнение команды в Railway
railway run <command>

# Подключение к базе данных
railway connect postgres

# Подключение к Redis
railway connect redis

# Откат миграции
railway run alembic downgrade -1

# Создание новой миграции
railway run alembic revision --autogenerate -m "description"
```

## Стоимость

**Railway:**
- $5/месяц за Hobby план (500 часов выполнения)
- PostgreSQL и Redis включены
- Дополнительно оплачивается по использованию

**Vercel:**
- Бесплатный план для личных проектов
- Pro план $20/месяц для коммерческих проектов

## Альтернативы

### Backend:
- Heroku
- Render
- DigitalOcean App Platform
- AWS Elastic Beanstalk

### Frontend:
- Netlify
- Cloudflare Pages
- GitHub Pages (для статики)

---

Made with ❤️ by Kiro AI
