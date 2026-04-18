# ⚡ Быстрый деплой за 10 минут

## 🚀 Railway Backend

1. **Создайте проект:**
   - https://railway.app → New Project → Deploy from GitHub
   - Выберите `swiftkeyy/gpay`

2. **Добавьте базы данных:**
   - New → Database → PostgreSQL
   - New → Database → Redis

3. **Добавьте переменные:**
   ```env
   SECRET_KEY=ваш-секретный-ключ-32-символа
   BOT_TOKEN=ваш-токен-от-botfather
   BOT_USERNAME=ваш_бот
   CORS_ORIGINS=http://localhost:3000
   ```

4. **Запустите миграции:**
   ```bash
   railway run alembic upgrade head
   ```

5. **Получите URL:**
   - Settings → Networking → Generate Domain
   - Скопируйте URL

## 🌐 Vercel Frontend

1. **Создайте проект:**
   - https://vercel.com → New Project
   - Импортируйте `swiftkeyy/gpay`

2. **Настройте:**
   - Root Directory: `frontend`
   - Framework: Vite

3. **Добавьте переменные:**
   ```env
   VITE_API_URL=https://ваш-backend.railway.app/api/v1
   VITE_WS_URL=wss://ваш-backend.railway.app/api/v1
   ```

4. **Деплой:**
   - Deploy → Скопируйте URL

5. **Обновите CORS:**
   - Railway → Backend → Variables
   - `CORS_ORIGINS=https://ваш-frontend.vercel.app`

## 📱 Telegram Mini App

1. **@BotFather:**
   - `/newapp` → Выберите бота
   - URL: `https://ваш-frontend.vercel.app`

2. **Готово!** 🎉

---

**Полная инструкция:** [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)
