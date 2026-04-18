# ⚡ Быстрый деплой за 15 минут

## Вариант 1: Всё на Railway (Рекомендуется) 🚂

### Backend + Frontend на Railway ($5/месяц)

1. **Создайте проект:**
   - https://railway.app → New Project → Deploy from GitHub
   - Выберите `swiftkeyy/gpay`

2. **Добавьте базы данных:**
   - New → Database → PostgreSQL
   - New → Database → Redis

3. **Настройте Backend:**
   - Добавьте переменные:
   ```env
   SECRET_KEY=ваш-секретный-ключ-32-символа
   BOT_TOKEN=ваш-токен-от-botfather
   BOT_USERNAME=ваш_бот
   CORS_ORIGINS=*
   ```
   - Запустите миграции: `railway run alembic upgrade head`
   - Settings → Networking → Generate Domain

4. **Добавьте Frontend:**
   - New → GitHub Repo → `swiftkeyy/gpay`
   - Settings → Root Directory: `frontend`
   - Settings → Build Command: `npm install && npm run build`
   - Settings → Start Command: `npm run preview -- --host 0.0.0.0 --port $PORT`
   - Добавьте переменные:
   ```env
   VITE_API_URL=https://ваш-backend.railway.app/api/v1
   VITE_WS_URL=wss://ваш-backend.railway.app/api/v1
   ```
   - Settings → Networking → Generate Domain

5. **Обновите CORS:**
   - Backend → Variables → `CORS_ORIGINS=https://ваш-frontend.railway.app`

6. **Telegram Mini App:**
   - @BotFather → `/newapp` → URL: `https://ваш-frontend.railway.app`

**Готово!** 🎉

---

## Вариант 2: Railway + Vercel

### Backend на Railway + Frontend на Vercel (бесплатно)

1. **Railway Backend:**
   - https://railway.app → New Project → `swiftkeyy/gpay`
   - New → PostgreSQL + Redis
   - Добавьте переменные (SECRET_KEY, BOT_TOKEN)
   - `railway run alembic upgrade head`
   - Generate Domain

2. **Vercel Frontend:**
   - https://vercel.com → New Project → `swiftkeyy/gpay`
   - Root Directory: `frontend`
   - Добавьте переменные (VITE_API_URL, VITE_WS_URL)
   - Deploy

3. **Обновите CORS:**
   - Railway → `CORS_ORIGINS=https://ваш-frontend.vercel.app`

4. **Telegram Mini App:**
   - @BotFather → `/newapp` → URL: `https://ваш-frontend.vercel.app`

**Готово!** 🎉

---

## 📚 Полные инструкции:

- **Railway (всё в одном):** [RAILWAY_FULL_DEPLOY.md](RAILWAY_FULL_DEPLOY.md)
- **Railway + Vercel:** [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)
- **Подробная документация:** [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)
