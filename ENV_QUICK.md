# ⚡ Быстрая шпаргалка по .env

## ✅ Обязательные переменные

### 1. DATABASE_URL
**Откуда:** Railway создаст автоматически
```
Railway → New → PostgreSQL
```

### 2. REDIS_URL
**Откуда:** Railway создаст автоматически
```
Railway → New → Redis
```

### 3. SECRET_KEY
**Откуда:** Сгенерируйте сами
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. BOT_TOKEN
**Откуда:** @BotFather в Telegram
```
1. Откройте @BotFather
2. /newbot
3. Введите название и username
4. Скопируйте токен
```

### 5. BOT_USERNAME
**Откуда:** Username бота (без @)
```
Тот же username, что указали в BotFather
```

### 6. CORS_ORIGINS
**Откуда:** URL вашего Frontend
```
Сначала: CORS_ORIGINS=*
После деплоя Frontend: CORS_ORIGINS=https://ваш-frontend.railway.app
```

---

## 📋 Минимальная конфигурация

Добавьте в Railway Variables:

```env
# Автоматически от Railway
DATABASE_URL=postgresql://...  (создастся сам)
REDIS_URL=redis://...          (создастся сам)

# Добавьте вручную
SECRET_KEY=ваш-сгенерированный-ключ-32-символа
BOT_TOKEN=6123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
BOT_USERNAME=ваш_бот
CORS_ORIGINS=*

# Настройки (опционально, есть значения по умолчанию)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=False
PLATFORM_COMMISSION_PERCENT=5.0
REFERRAL_REWARD_PERCENT=5.0
AUTO_COMPLETE_HOURS=72
```

---

## 🚀 Пошаговая инструкция

### 1. Создайте бота (2 минуты)
```
@BotFather → /newbot → скопируйте токен
```

### 2. Сгенерируйте SECRET_KEY (10 секунд)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Добавьте в Railway (1 минута)
```
Railway → Backend → Variables → Add:
- SECRET_KEY
- BOT_TOKEN
- BOT_USERNAME
- CORS_ORIGINS=*
```

### 4. Обновите CORS после деплоя Frontend
```
Railway → Backend → Variables → Edit:
CORS_ORIGINS=https://ваш-frontend.railway.app
```

---

## 💳 Платежи (опционально, добавите позже)

### ЮKassa
```
https://yookassa.ru → Интеграция → скопируйте ключи
YUKASSA_SHOP_ID=...
YUKASSA_SECRET_KEY=...
```

### Tinkoff
```
https://www.tinkoff.ru/business/ → Эквайринг → ключи
TINKOFF_TERMINAL_KEY=...
TINKOFF_SECRET_KEY=...
```

### CloudPayments
```
https://cloudpayments.ru → API → ключи
CLOUDPAYMENTS_PUBLIC_ID=...
CLOUDPAYMENTS_API_SECRET=...
```

### Crypto Bot
```
@CryptoBot → Create App → скопируйте токен
CRYPTOBOT_TOKEN=...
```

---

## 📚 Полная документация

Подробности в [ENV_GUIDE.md](ENV_GUIDE.md)
