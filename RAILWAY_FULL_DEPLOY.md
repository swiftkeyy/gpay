# 🚂 Полный деплой на Railway (Backend + Frontend)

## Преимущества деплоя всего на Railway:
- ✅ Всё в одном месте
- ✅ Проще управлять
- ✅ Один домен для всего
- ✅ Меньше настроек CORS

---

## 🚀 Деплой (15 минут)

### Шаг 1: Создайте проект на Railway

1. Откройте https://railway.app
2. Войдите через GitHub
3. Нажмите **"New Project"**
4. Выберите **"Deploy from GitHub repo"**
5. Выберите репозиторий **swiftkeyy/gpay**

Railway создаст один сервис для Backend.

### Шаг 2: Добавьте PostgreSQL

1. В проекте нажмите **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway создаст базу данных
3. Переменная `DATABASE_URL` добавится автоматически

### Шаг 3: Добавьте Redis

1. В проекте нажмите **"New"** → **"Database"** → **"Redis"**
2. Railway создаст Redis
3. Переменная `REDIS_URL` добавится автоматически

### Шаг 4: Настройте Backend переменные

В настройках Backend сервиса добавьте:

```env
# JWT (ОБЯЗАТЕЛЬНО!)
SECRET_KEY=ваш-супер-секретный-ключ-минимум-32-символа
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Telegram Bot (ОБЯЗАТЕЛЬНО!)
BOT_TOKEN=ваш-токен-от-botfather
BOT_USERNAME=ваш_бот_username

# CORS (временно, обновим позже)
CORS_ORIGINS=*

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

### Шаг 5: Настройте Start Command

**В Railway Dashboard:**
1. Settings → Deploy → Start Command:
   ```bash
   ./entrypoint.sh
   ```

> **Примечание:** Файл `entrypoint.sh` автоматически запускает миграции Alembic и затем бота. Это гарантирует правильный порядок запуска и защиту от ошибок миграций.

**Альтернативно через Railway CLI:**
```bash
npm install -g @railway/cli
railway login
railway link
railway run alembic upgrade head
```

### Шаг 6: Получите URL Backend

1. Settings → Networking → Generate Domain
2. Скопируйте URL (например: `https://gpay-production.up.railway.app`)

### Шаг 7: Добавьте Frontend сервис

1. В проекте нажмите **"New"** → **"GitHub Repo"**
2. Выберите тот же репозиторий **swiftkeyy/gpay**
3. Railway создаст второй сервис

### Шаг 8: Настройте Frontend сервис

1. Откройте настройки нового сервиса
2. Settings → **Root Directory**: `frontend`
3. Settings → **Build Command**: `npm install && npm run build`
4. Settings → **Start Command**: `npm run preview -- --host 0.0.0.0 --port $PORT`

### Шаг 9: Добавьте Frontend переменные

В настройках Frontend сервиса добавьте:

```env
VITE_API_URL=https://ваш-backend.railway.app/api/v1
VITE_WS_URL=wss://ваш-backend.railway.app/api/v1
```

**ВАЖНО:** Замените `ваш-backend.railway.app` на реальный URL из Шага 6!

### Шаг 10: Получите URL Frontend

1. Settings → Networking → Generate Domain
2. Скопируйте URL (например: `https://gpay-frontend.up.railway.app`)

### Шаг 11: Обновите CORS на Backend

1. Вернитесь в настройки Backend сервиса
2. Обновите переменную `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://ваш-frontend.railway.app
   ```
3. Сохраните и подождите перезапуска

---

## 📱 Настройка Telegram Mini App

### Шаг 12: Создайте Mini App

1. Откройте @BotFather в Telegram
2. Отправьте `/newapp`
3. Выберите вашего бота
4. Введите название: **P2P Marketplace**
5. Введите описание: **Маркетплейс игровых товаров**
6. Загрузите иконку (640x360 px)
7. Введите URL: `https://ваш-frontend.railway.app`

### Шаг 13: Настройте кнопку меню

1. Отправьте `/mybots` в @BotFather
2. Выберите вашего бота
3. Выберите **"Bot Settings"** → **"Menu Button"**
4. Введите URL: `https://ваш-frontend.railway.app`

---

## 🧪 Тестирование

### Проверьте Backend API
```bash
curl https://ваш-backend.railway.app/docs
```

Должна открыться Swagger документация.

### Проверьте Frontend
Откройте `https://ваш-frontend.railway.app` в браузере.

### Проверьте Telegram Mini App
1. Откройте вашего бота в Telegram
2. Нажмите на кнопку меню
3. Должно открыться ваше приложение

---

## 📊 Структура проекта на Railway

```
Ваш проект
├── Backend Service (Python/FastAPI)
│   ├── URL: https://gpay-backend.railway.app
│   └── Переменные: SECRET_KEY, BOT_TOKEN, DATABASE_URL, REDIS_URL
├── Frontend Service (Vite/React)
│   ├── URL: https://gpay-frontend.railway.app
│   └── Переменные: VITE_API_URL, VITE_WS_URL
├── PostgreSQL Database
│   └── Автоматически подключен к Backend
└── Redis Database
    └── Автоматически подключен к Backend
```

---

## 💰 Стоимость

**Railway Hobby Plan:**
- $5/месяц
- 500 часов выполнения
- 2 сервиса (Backend + Frontend)
- PostgreSQL и Redis включены

**Итого:** $5/месяц (всё включено!)

---

## 🔄 Обновление

### Автоматическое обновление
Railway автоматически деплоит при push в GitHub:

```bash
git add .
git commit -m "Update"
git push origin main
```

Оба сервиса (Backend и Frontend) обновятся автоматически!

---

## 🆘 Troubleshooting

### Frontend не собирается
1. Проверьте логи: Dashboard → Frontend Service → Deployments → Logs
2. Убедитесь, что Root Directory = `frontend`
3. Проверьте Build Command: `npm install && npm run build`

### Frontend не подключается к Backend
1. Проверьте `VITE_API_URL` в переменных Frontend
2. Проверьте CORS на Backend
3. Откройте DevTools → Network в браузере

### WebSocket не работает
1. Убедитесь, что используете `wss://` (не `ws://`)
2. Проверьте `VITE_WS_URL` в переменных Frontend
3. Проверьте CORS для WebSocket на Backend

---

## 💡 Альтернативные варианты

### Вариант 1: Railway (Backend + Frontend) ✅ Рекомендуется
- Всё в одном месте
- $5/месяц
- Проще управлять

### Вариант 2: Railway (Backend) + Vercel (Frontend)
- Backend на Railway ($5/месяц)
- Frontend на Vercel (бесплатно)
- Больше настроек CORS

### Вариант 3: Railway (Backend) + Cloudflare Pages (Frontend)
- Backend на Railway ($5/месяц)
- Frontend на Cloudflare (бесплатно)
- Быстрый CDN

### Вариант 4: Railway (Backend) + Netlify (Frontend)
- Backend на Railway ($5/месяц)
- Frontend на Netlify (бесплатно)
- Хороший CI/CD

---

## 📚 Полезные команды

```bash
# Просмотр логов Backend
railway logs --service backend

# Просмотр логов Frontend
railway logs --service frontend

# Выполнение команды на Backend
railway run --service backend alembic upgrade head

# Подключение к базе данных
railway connect postgres

# Подключение к Redis
railway connect redis
```

---

## ✅ Чеклист готовности

- [ ] Backend задеплоен на Railway
- [ ] Frontend задеплоен на Railway
- [ ] PostgreSQL подключен
- [ ] Redis подключен
- [ ] Миграции выполнены
- [ ] Переменные окружения настроены
- [ ] CORS настроен правильно
- [ ] Telegram Mini App создан
- [ ] Всё протестировано

---

## 🎉 Готово!

Ваш P2P Marketplace полностью на Railway!

**Backend:** https://ваш-backend.railway.app
**Frontend:** https://ваш-frontend.railway.app
**Telegram Bot:** @ваш_бот

**Стоимость:** $5/месяц (всё включено)

---

Made with ❤️ by Kiro AI
