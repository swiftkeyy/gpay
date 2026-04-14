# Настройка CryptoBot для приема платежей

## Проблема HTTP 403 Error Code 1010

Ошибка возникает из-за того, что старый API `pay.crypt.bot` больше не работает.

## Решение

### Вариант 1: Использовать @CryptoBot (рекомендуется)

1. Открой [@CryptoBot](https://t.me/CryptoBot) в Telegram
2. Нажми "Create App" или "Создать приложение"
3. Получи API токен
4. В `.env` файле установи:
```env
CRYPTOBOT_API_TOKEN=твой_токен_от_cryptobot
CRYPTOBOT_API_BASE_URL=https://pay.crypt.bot/api
```

### Вариант 2: Использовать @CryptoTestnetBot (для тестов)

1. Открой [@CryptoTestnetBot](https://t.me/CryptoTestnetBot) в Telegram
2. Получи тестовый API токен
3. В `.env` файле установи:
```env
CRYPTOBOT_API_TOKEN=твой_тестовый_токен
CRYPTOBOT_API_BASE_URL=https://testnet-pay.crypt.bot/api
```

### Вариант 3: Отключить CryptoBot

Если не нужен прием крипты, просто отключи:
```env
CRYPTOBOT_ENABLED=false
```

## Конвертация Telegram Stars

Исправлена конвертация:
- **Старая**: 1 звезда = 1 рубль
- **Новая**: 1 звезда = 2 рубля (стандартный курс Telegram)

Можно изменить в `.env`:
```env
# 1 рубль = 0.5 звезды (или 1 звезда = 2 рубля)
TELEGRAM_STARS_PER_RUB=0.5

# Или другой курс, например 1 звезда = 3 рубля:
TELEGRAM_STARS_PER_RUB=0.333
```

## Проверка настроек

После настройки проверь:
1. Перезапусти бот
2. Попробуй создать заказ
3. Выбери способ оплаты
4. Проверь что инвойс создается без ошибок
