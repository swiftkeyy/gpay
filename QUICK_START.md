# Quick Start - P2P Marketplace

## 🚀 Быстрый запуск за 5 минут

### 1. Backend (2 минуты)

```bash
cd ПРОЕКТЫ/gpay-main

# Установить зависимости (если еще не установлены)
pip install -r requirements.txt

# Создать .env файл
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://user:password@localhost/gpay
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key-change-this
BOT_TOKEN=your-telegram-bot-token
YUKASSA_SHOP_ID=your-shop-id
YUKASSA_SECRET_KEY=your-secret-key
EOF

# Запустить миграции
alembic upgrade head

# Запустить сервер
uvicorn api.main:app --reload
```

Backend будет доступен на http://localhost:8000

### 2. Frontend (3 минуты)

```bash
cd ПРОЕКТЫ/gpay-main/frontend

# Установить зависимости
npm install

# Создать .env файл
cat > .env << EOF
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1
EOF

# Запустить dev сервер
npm run dev
```

Frontend будет доступен на http://localhost:3000

---

## 📝 Что проверить

### Backend:
1. Открыть http://localhost:8000/health - должен вернуть `{"status":"ok"}`
2. Открыть http://localhost:8000/api/docs - Swagger UI
3. Проверить что PostgreSQL и Redis запущены

### Frontend:
1. Открыть http://localhost:3000
2. Должна открыться главная страница с каталогом
3. Проверить консоль браузера на ошибки

---

## 🐛 Troubleshooting

### Backend не запускается:
- Проверьте что PostgreSQL запущен: `pg_isready`
- Проверьте что Redis запущен: `redis-cli ping`
- Проверьте .env файл

### Frontend не запускается:
- Проверьте версию Node.js: `node --version` (нужна 18+)
- Удалите node_modules и переустановите: `rm -rf node_modules && npm install`
- Проверьте .env файл

### Ошибки в консоли браузера:
- Проверьте что Backend запущен
- Проверьте CORS настройки в Backend
- Проверьте URL в .env файле

---

## 📚 Дополнительная информация

- **Полный статус проекта:** PROJECT_STATUS.md
- **Статус Frontend:** FRONTEND_STATUS.md
- **Backend документация:** BACKEND_ГОТОВ.md
- **Инструкция по деплою:** DEPLOY.md

---

## 🎯 Следующие шаги

1. Протестировать основной флоу: регистрация → каталог → корзина → оформление
2. Доработать ChatPage (см. FRONTEND_STATUS.md)
3. Добавить формы в SellerDashboard и AdminPanel
4. Задеплоить на staging

---

Made with ❤️ by Kiro AI
