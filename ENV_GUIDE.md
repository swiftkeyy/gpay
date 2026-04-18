# 🔐 Гид по переменным окружения (.env)

## 📋 Обязательные переменные (без них не запустится)

### 1. DATABASE_URL
**Что это:** Подключение к PostgreSQL базе данных

**Откуда взять:**
- **Railway:** Создается автоматически при добавлении PostgreSQL
  - New → Database → PostgreSQL
  - Переменная `DATABASE_URL` появится автоматически
  - Формат: `postgresql://user:password@host:port/dbname`

**Пример:**
```env
DATABASE_URL=postgresql://postgres:password@containers-us-west-123.railway.app:5432/railway
```

**Действие:** Ничего делать не нужно - Railway добавит автоматически!

---

### 2. REDIS_URL
**Что это:** Подключение к Redis (для кеширования и WebSocket)

**Откуда взять:**
- **Railway:** Создается автоматически при добавлении Redis
  - New → Database → Redis
  - Переменная `REDIS_URL` появится автоматически
  - Формат: `redis://default:password@host:port`

**Пример:**
```env
REDIS_URL=redis://default:password@containers-us-west-456.railway.app:6379
```

**Действие:** Ничего делать не нужно - Railway добавит автоматически!

---

### 3. SECRET_KEY
**Что это:** Секретный ключ для шифрования JWT токенов

**Откуда взять:** Сгенерируйте сами!

**Как сгенерировать:**

**Вариант 1 - Python:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Вариант 2 - OpenSSL:**
```bash
openssl rand -base64 32
```

**Вариант 3 - Онлайн:**
https://randomkeygen.com/ (выберите "CodeIgniter Encryption Keys")

**Пример:**
```env
SECRET_KEY=8f4e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e
```

**⚠️ ВАЖНО:**
- Минимум 32 символа
- Используйте случайные символы
- НЕ используйте простые пароли типа "password123"
- НЕ публикуйте в GitHub

---

### 4. BOT_TOKEN
**Что это:** Токен вашего Telegram бота

**Откуда взять:** От @BotFather в Telegram

**Как получить:**
1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте `/newbot`
4. Введите название бота (например: "P2P Marketplace Bot")
5. Введите username бота (например: "p2p_marketplace_bot")
6. BotFather пришлет токен

**Пример:**
```env
BOT_TOKEN=6123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
```

**Формат:** `числа:буквы_и_цифры`

---

### 5. BOT_USERNAME
**Что это:** Username вашего бота (без @)

**Откуда взять:** Тот же username, который вы указали при создании бота

**Пример:**
```env
BOT_USERNAME=p2p_marketplace_bot
```

**⚠️ ВАЖНО:** Без символа @

---

### 6. CORS_ORIGINS
**Что это:** Разрешенные домены для Frontend

**Откуда взять:** URL вашего Frontend

**Для Railway:**
```env
CORS_ORIGINS=https://ваш-frontend.railway.app
```

**Для Vercel:**
```env
CORS_ORIGINS=https://ваш-frontend.vercel.app
```

**Для разработки:**
```env
CORS_ORIGINS=http://localhost:3000
```

**Несколько доменов (через запятую):**
```env
CORS_ORIGINS=http://localhost:3000,https://ваш-frontend.railway.app
```

**⚠️ ВАЖНО:** Обновите после деплоя Frontend!

---

## 📋 Опциональные переменные (можно добавить позже)

### 7. YUKASSA_SHOP_ID и YUKASSA_SECRET_KEY
**Что это:** Ключи для приема платежей через ЮKassa

**Откуда взять:**
1. Зарегистрируйтесь на https://yookassa.ru
2. Создайте магазин
3. Перейдите в "Настройки" → "Интеграция"
4. Скопируйте `shopId` и `Секретный ключ`

**Пример:**
```env
YUKASSA_SHOP_ID=123456
YUKASSA_SECRET_KEY=live_abcdefghijklmnopqrstuvwxyz123456
```

**Когда нужно:** Если хотите принимать оплату картами через ЮKassa

---

### 8. TINKOFF_TERMINAL_KEY и TINKOFF_SECRET_KEY
**Что это:** Ключи для приема платежей через Tinkoff

**Откуда взять:**
1. Зарегистрируйтесь на https://www.tinkoff.ru/business/
2. Подключите эквайринг
3. В личном кабинете получите `TerminalKey` и `Password`

**Пример:**
```env
TINKOFF_TERMINAL_KEY=1234567890ABCDEF
TINKOFF_SECRET_KEY=abcdefghijklmnop
```

**Когда нужно:** Если хотите принимать оплату через Tinkoff

---

### 9. CLOUDPAYMENTS_PUBLIC_ID и CLOUDPAYMENTS_API_SECRET
**Что это:** Ключи для приема платежей через CloudPayments

**Откуда взять:**
1. Зарегистрируйтесь на https://cloudpayments.ru
2. Перейдите в "Настройки" → "API"
3. Скопируйте `Public ID` и `API Secret`

**Пример:**
```env
CLOUDPAYMENTS_PUBLIC_ID=pk_1234567890abcdef
CLOUDPAYMENTS_API_SECRET=1234567890abcdef1234567890abcdef
```

**Когда нужно:** Если хотите принимать оплату через CloudPayments

---

### 10. CRYPTOBOT_TOKEN
**Что это:** Токен для приема криптовалюты через Crypto Bot

**Откуда взять:**
1. Откройте @CryptoBot в Telegram
2. Отправьте `/start`
3. Выберите "Create App"
4. Скопируйте токен

**Пример:**
```env
CRYPTOBOT_TOKEN=12345:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
```

**Когда нужно:** Если хотите принимать криптовалюту (TON, USDT)

---

## 📋 Настройки приложения (можно оставить по умолчанию)

### 11. ALGORITHM
**Что это:** Алгоритм шифрования JWT

**Значение по умолчанию:**
```env
ALGORITHM=HS256
```

**Действие:** Оставьте как есть

---

### 12. ACCESS_TOKEN_EXPIRE_MINUTES
**Что это:** Время жизни токена авторизации (в минутах)

**Значение по умолчанию:**
```env
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Рекомендация:** 30-60 минут

---

### 13. APP_NAME
**Что это:** Название вашего приложения

**Значение по умолчанию:**
```env
APP_NAME=P2P Marketplace
```

**Действие:** Можете изменить на свое название

---

### 14. APP_VERSION
**Что это:** Версия приложения

**Значение по умолчанию:**
```env
APP_VERSION=1.0.0
```

**Действие:** Оставьте как есть

---

### 15. DEBUG
**Что это:** Режим отладки

**Для production:**
```env
DEBUG=False
```

**Для разработки:**
```env
DEBUG=True
```

**⚠️ ВАЖНО:** На production всегда `False`!

---

### 16. PLATFORM_COMMISSION_PERCENT
**Что это:** Комиссия платформы с каждой сделки (в процентах)

**Значение по умолчанию:**
```env
PLATFORM_COMMISSION_PERCENT=5.0
```

**Рекомендация:** 3-10%

---

### 17. REFERRAL_REWARD_PERCENT
**Что это:** Процент вознаграждения за реферала

**Значение по умолчанию:**
```env
REFERRAL_REWARD_PERCENT=5.0
```

**Рекомендация:** 3-10%

---

### 18. AUTO_COMPLETE_HOURS
**Что это:** Через сколько часов автоматически завершать сделку

**Значение по умолчанию:**
```env
AUTO_COMPLETE_HOURS=72
```

**Рекомендация:** 48-72 часа

---

## 🚀 Минимальная конфигурация для запуска

Для запуска проекта нужны только эти переменные:

```env
# Автоматически от Railway
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Сгенерируйте сами
SECRET_KEY=ваш-случайный-ключ-32-символа

# От @BotFather
BOT_TOKEN=6123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
BOT_USERNAME=ваш_бот

# URL вашего Frontend
CORS_ORIGINS=https://ваш-frontend.railway.app

# Настройки (можно оставить по умолчанию)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_NAME=P2P Marketplace
APP_VERSION=1.0.0
DEBUG=False
PLATFORM_COMMISSION_PERCENT=5.0
REFERRAL_REWARD_PERCENT=5.0
AUTO_COMPLETE_HOURS=72
```

**Платежные провайдеры добавите позже, когда получите ключи!**

---

## 📝 Пошаговая инструкция

### Шаг 1: Создайте бота
1. Откройте @BotFather
2. `/newbot` → введите название и username
3. Скопируйте `BOT_TOKEN`

### Шаг 2: Сгенерируйте SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Шаг 3: Добавьте переменные в Railway
1. Откройте ваш проект на Railway
2. Выберите Backend сервис
3. Перейдите в "Variables"
4. Добавьте:
   - `SECRET_KEY` = ваш сгенерированный ключ
   - `BOT_TOKEN` = токен от BotFather
   - `BOT_USERNAME` = username бота (без @)
   - `CORS_ORIGINS` = `*` (временно, обновите после деплоя Frontend)

### Шаг 4: Задеплойте Frontend
1. Получите URL Frontend
2. Вернитесь в Railway Backend
3. Обновите `CORS_ORIGINS` на реальный URL

### Шаг 5: Готово!
Проект запущен с минимальной конфигурацией.

### Шаг 6: Добавьте платежи (опционально)
Когда получите ключи от платежных провайдеров, добавьте их в Variables.

---

## ⚠️ Важные правила безопасности

1. **НЕ публикуйте .env в GitHub**
   - Файл `.env` уже в `.gitignore`
   - Используйте `.env.example` для документации

2. **Используйте сильный SECRET_KEY**
   - Минимум 32 символа
   - Случайные символы
   - Не используйте простые пароли

3. **Храните токены в безопасности**
   - Не делитесь BOT_TOKEN
   - Не публикуйте платежные ключи
   - Используйте переменные окружения Railway

4. **Обновляйте CORS_ORIGINS**
   - Не оставляйте `*` на production
   - Указывайте только ваши домены

---

## 🆘 Частые ошибки

### "Invalid BOT_TOKEN"
- Проверьте, что скопировали токен полностью
- Формат: `числа:буквы_и_цифры`
- Получите новый токен от @BotFather

### "Database connection failed"
- Проверьте, что PostgreSQL создан в Railway
- `DATABASE_URL` должен быть добавлен автоматически
- Проверьте формат: `postgresql://...`

### "CORS error"
- Обновите `CORS_ORIGINS` на реальный URL Frontend
- Не забудьте `https://` в начале
- Проверьте, что нет лишних пробелов

### "Redis connection failed"
- Проверьте, что Redis создан в Railway
- `REDIS_URL` должен быть добавлен автоматически
- Проверьте формат: `redis://...`

---

Made with ❤️ by Kiro AI
