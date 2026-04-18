# 🚀 Деплой P2P Marketplace

## Варианты деплоя

### Вариант 1: Railway (Рекомендуется)
**Плюсы:** Простой деплой, автоматические миграции, встроенный PostgreSQL и Redis
**Минусы:** Платный после trial периода

### Вариант 2: Heroku
**Плюсы:** Бесплатный tier, простой деплой
**Минусы:** Ограничения на бесплатном плане

### Вариант 3: VPS (DigitalOcean, Hetzner)
**Плюсы:** Полный контроль, дешевле на долгосрочной перспективе
**Минусы:** Требует настройки

---

## 🚂 Деплой на Railway

### 1. Подготовка

#### Создать railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Создать Procfile
```
web: alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

#### Обновить requirements.txt
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
redis==5.0.1
httpx==0.25.2
```

### 2. Создать проект на Railway

1. Зайти на https://railway.app
2. Создать новый проект
3. Добавить PostgreSQL
4. Добавить Redis
5. Добавить GitHub репозиторий

### 3. Настроить переменные окружения

В Railway Dashboard → Variables:

```env
# Database (автоматически из PostgreSQL сервиса)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (автоматически из Redis сервиса)
REDIS_URL=${{Redis.REDIS_URL}}

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-this

# Telegram
BOT_TOKEN=your-telegram-bot-token

# CORS
CORS_ORIGINS=https://your-frontend-domain.vercel.app

# Payment providers
YUKASSA_SHOP_ID=your-shop-id
YUKASSA_SECRET_KEY=your-secret-key
TINKOFF_TERMINAL_KEY=your-terminal-key
TINKOFF_SECRET_KEY=your-secret-key
CLOUDPAYMENTS_PUBLIC_ID=your-public-id
CLOUDPAYMENTS_API_SECRET=your-api-secret
CRYPTOBOT_TOKEN=your-cryptobot-token

# Commission
COMMISSION_RATE=0.10
```

### 4. Деплой

```bash
# Пушим в GitHub
git add .
git commit -m "Deploy to Railway"
git push origin main
```

Railway автоматически задеплоит приложение.

### 5. Проверка

```bash
# Проверить health check
curl https://your-app.railway.app/health

# Проверить API docs
open https://your-app.railway.app/api/docs
```

---

## 🌊 Деплой на Heroku

### 1. Подготовка

#### Создать Procfile
```
web: alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

#### Создать runtime.txt
```
python-3.11
```

### 2. Создать приложение

```bash
# Установить Heroku CLI
brew install heroku/brew/heroku

# Логин
heroku login

# Создать приложение
heroku create your-app-name

# Добавить PostgreSQL
heroku addons:create heroku-postgresql:mini

# Добавить Redis
heroku addons:create heroku-redis:mini
```

### 3. Настроить переменные

```bash
heroku config:set JWT_SECRET_KEY=your-secret-key
heroku config:set BOT_TOKEN=your-bot-token
heroku config:set CORS_ORIGINS=https://your-frontend.vercel.app
heroku config:set YUKASSA_SHOP_ID=your-shop-id
heroku config:set YUKASSA_SECRET_KEY=your-secret-key
# ... остальные переменные
```

### 4. Деплой

```bash
git push heroku main
```

### 5. Проверка

```bash
heroku logs --tail
heroku open
```

---

## 🖥️ Деплой на VPS (Ubuntu 22.04)

### 1. Подключиться к серверу

```bash
ssh root@your-server-ip
```

### 2. Установить зависимости

```bash
# Обновить систему
apt update && apt upgrade -y

# Установить Python 3.11
apt install python3.11 python3.11-venv python3-pip -y

# Установить PostgreSQL
apt install postgresql postgresql-contrib -y

# Установить Redis
apt install redis-server -y

# Установить Nginx
apt install nginx -y

# Установить Supervisor
apt install supervisor -y
```

### 3. Настроить PostgreSQL

```bash
# Создать пользователя и базу
sudo -u postgres psql

CREATE USER gpay WITH PASSWORD 'your-password';
CREATE DATABASE gpay OWNER gpay;
GRANT ALL PRIVILEGES ON DATABASE gpay TO gpay;
\q
```

### 4. Настроить Redis

```bash
# Редактировать конфиг
nano /etc/redis/redis.conf

# Изменить:
# bind 127.0.0.1
# requirepass your-redis-password

# Перезапустить
systemctl restart redis
```

### 5. Клонировать репозиторий

```bash
cd /var/www
git clone https://github.com/your-username/gpay.git
cd gpay
```

### 6. Создать виртуальное окружение

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. Создать .env

```bash
nano .env
```

```env
DATABASE_URL=postgresql+asyncpg://gpay:your-password@localhost/gpay
REDIS_URL=redis://:your-redis-password@localhost:6379
JWT_SECRET_KEY=your-secret-key
BOT_TOKEN=your-bot-token
CORS_ORIGINS=https://your-frontend.com
# ... остальные переменные
```

### 8. Запустить миграции

```bash
alembic upgrade head
```

### 9. Настроить Supervisor

```bash
nano /etc/supervisor/conf.d/gpay.conf
```

```ini
[program:gpay]
directory=/var/www/gpay
command=/var/www/gpay/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gpay.log
```

```bash
supervisorctl reread
supervisorctl update
supervisorctl start gpay
```

### 10. Настроить Nginx

```bash
nano /etc/nginx/sites-available/gpay
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/gpay /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 11. Настроить SSL (Let's Encrypt)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

### 12. Проверка

```bash
# Проверить статус
supervisorctl status gpay

# Проверить логи
tail -f /var/log/gpay.log

# Проверить API
curl https://your-domain.com/health
```

---

## 🎨 Деплой Frontend (Vercel)

### 1. Создать Next.js/React проект

```bash
npx create-next-app@latest frontend
cd frontend
```

### 2. Настроить .env.local

```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app
```

### 3. Деплой на Vercel

```bash
# Установить Vercel CLI
npm i -g vercel

# Логин
vercel login

# Деплой
vercel
```

Или через GitHub:
1. Зайти на https://vercel.com
2. Import GitHub репозиторий
3. Настроить переменные окружения
4. Deploy

---

## 🤖 Настройка Telegram Mini App

### 1. Открыть BotFather

```
/newapp
```

### 2. Выбрать бота

Выбрать существующего бота или создать нового.

### 3. Указать данные

- **Title:** P2P Marketplace
- **Description:** Маркетплейс игровых товаров
- **Photo:** Загрузить иконку 640x360
- **Demo GIF:** Загрузить демо (опционально)
- **Web App URL:** https://your-frontend.vercel.app

### 4. Настроить меню

```
/setmenubutton
```

- **Button text:** 🛍 Открыть магазин
- **Web App URL:** https://your-frontend.vercel.app

### 5. Настроить команды

```
/setcommands
```

```
start - Запустить бота
help - Помощь
shop - Открыть магазин
orders - Мои заказы
profile - Профиль
```

---

## 🔧 Настройка Webhook для платежей

### YooKassa

1. Зайти в личный кабинет YooKassa
2. Настройки → Уведомления
3. HTTP URL: `https://your-backend.railway.app/api/v1/webhooks/yukassa`
4. Включить уведомления о платежах

### Tinkoff

1. Зайти в личный кабинет Tinkoff
2. Настройки → Уведомления
3. URL: `https://your-backend.railway.app/api/v1/webhooks/tinkoff`

### CloudPayments

1. Зайти в личный кабинет CloudPayments
2. Настройки → Уведомления
3. Check URL: `https://your-backend.railway.app/api/v1/webhooks/cloudpayments`
4. Pay URL: `https://your-backend.railway.app/api/v1/webhooks/cloudpayments`

### Crypto Bot

1. Создать бота в @CryptoBot
2. Получить API токен
3. Настроить webhook: `https://your-backend.railway.app/api/v1/webhooks/cryptobot`

---

## 📊 Мониторинг

### 1. Логи

**Railway:**
```bash
railway logs
```

**Heroku:**
```bash
heroku logs --tail
```

**VPS:**
```bash
tail -f /var/log/gpay.log
```

### 2. Метрики

**Установить Prometheus + Grafana (VPS):**

```bash
# Prometheus
docker run -d -p 9090:9090 prom/prometheus

# Grafana
docker run -d -p 3000:3000 grafana/grafana
```

### 3. Uptime мониторинг

**UptimeRobot:**
1. Зайти на https://uptimerobot.com
2. Добавить монитор
3. URL: `https://your-backend.railway.app/health`
4. Интервал: 5 минут

---

## 🔐 Безопасность

### 1. Firewall (VPS)

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

### 2. Fail2Ban (VPS)

```bash
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

### 3. Регулярные обновления

```bash
# Создать cron job
crontab -e

# Добавить:
0 2 * * * apt update && apt upgrade -y
```

### 4. Бэкапы PostgreSQL

```bash
# Создать скрипт backup.sh
#!/bin/bash
pg_dump -U gpay gpay > /backups/gpay_$(date +%Y%m%d).sql
find /backups -mtime +7 -delete

# Добавить в cron
0 3 * * * /path/to/backup.sh
```

---

## ✅ Чеклист деплоя

- [ ] Backend задеплоен (Railway/Heroku/VPS)
- [ ] PostgreSQL настроен и доступен
- [ ] Redis настроен и доступен
- [ ] Миграции выполнены
- [ ] Переменные окружения настроены
- [ ] SSL сертификат установлен (HTTPS)
- [ ] Frontend задеплоен (Vercel)
- [ ] Telegram Mini App настроен в BotFather
- [ ] Webhook для платежей настроены
- [ ] Мониторинг настроен
- [ ] Бэкапы настроены
- [ ] Firewall настроен (VPS)
- [ ] Health check работает
- [ ] API docs доступны
- [ ] WebSocket работает
- [ ] Платежи работают

---

## 🎉 Готово!

**Backend:** https://your-backend.railway.app
**Frontend:** https://your-frontend.vercel.app
**API Docs:** https://your-backend.railway.app/api/docs
**Telegram Bot:** @your_bot

---

**Дата:** 2024-01-XX
**Статус:** 🚀 Готов к продакшну
