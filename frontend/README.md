# P2P Marketplace - Frontend (Telegram Mini App)

React + TypeScript приложение для Telegram Mini App.

## 🚀 Запуск

### 1. Установка зависимостей
```bash
cd frontend
npm install
```

### 2. Настройка .env
```bash
cp .env.example .env
```

Отредактировать `.env`:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1
```

### 3. Запуск dev сервера
```bash
npm run dev
```

Откроется на http://localhost:3000

### 4. Сборка для продакшна
```bash
npm run build
```

Результат в папке `dist/`

## 📁 Структура

```
frontend/
├── src/
│   ├── pages/           # Страницы
│   │   ├── HomePage.tsx
│   │   ├── ProductPage.tsx
│   │   ├── CartPage.tsx
│   │   ├── CheckoutPage.tsx
│   │   ├── OrdersPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── SellerDashboard.tsx
│   │   ├── ProfilePage.tsx
│   │   └── AdminPanel.tsx
│   ├── store/           # Zustand stores
│   │   ├── authStore.ts
│   │   └── cartStore.ts
│   ├── api/             # API client
│   │   └── client.ts
│   ├── App.tsx          # Main app
│   ├── main.tsx         # Entry point
│   └── index.css        # Styles
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## 🎨 Страницы

1. **HomePage** (`/`) - Каталог товаров с поиском
2. **ProductPage** (`/product/:id`) - Детали товара
3. **CartPage** (`/cart`) - Корзина
4. **CheckoutPage** (`/checkout`) - Оформление заказа
5. **OrdersPage** (`/orders`) - История заказов
6. **ChatPage** (`/chat/:dealId`) - WebSocket чат с продавцом
7. **SellerDashboard** (`/seller`) - Кабинет продавца
8. **ProfilePage** (`/profile`) - Профиль пользователя
9. **AdminPanel** (`/admin`) - Админ-панель

## 🔧 Технологии

- **React 18** - UI библиотека
- **TypeScript** - Типизация
- **Vite** - Сборщик
- **React Router** - Роутинг
- **Zustand** - State management
- **Axios** - HTTP клиент
- **Tailwind CSS** - Стили
- **@twa-dev/sdk** - Telegram WebApp SDK

## 🌐 Деплой на Vercel

### 1. Установить Vercel CLI
```bash
npm i -g vercel
```

### 2. Логин
```bash
vercel login
```

### 3. Деплой
```bash
vercel
```

### 4. Настроить переменные окружения
В Vercel Dashboard → Settings → Environment Variables:
- `VITE_API_URL` = `https://your-backend.railway.app/api/v1`
- `VITE_WS_URL` = `wss://your-backend.railway.app/api/v1`

### 5. Production deploy
```bash
vercel --prod
```

## 📱 Настройка в Telegram

### 1. Открыть BotFather
```
/newapp
```

### 2. Указать данные
- **Title:** P2P Marketplace
- **Description:** Маркетплейс игровых товаров
- **Web App URL:** https://your-app.vercel.app

### 3. Настроить меню
```
/setmenubutton
```
- **Button text:** 🛍 Открыть магазин
- **Web App URL:** https://your-app.vercel.app

## 🔐 Аутентификация

Приложение использует Telegram initData для аутентификации:

1. Получает `initData` из `WebApp.initData`
2. Отправляет на `/auth/telegram`
3. Получает JWT токен
4. Использует токен для всех запросов

## 💬 WebSocket чат

Чат использует WebSocket для real-time сообщений:

```typescript
const ws = new WebSocket(`${WS_URL}/ws/chat/${dealId}?token=${token}`)

ws.send(JSON.stringify({
  type: 'text',
  content: 'Привет!'
}))
```

## 🎨 Темы Telegram

Приложение автоматически использует цвета темы Telegram:

```css
--tg-theme-bg-color
--tg-theme-text-color
--tg-theme-button-color
--tg-theme-button-text-color
```

## 📝 TODO

- [ ] Добавить поиск с автодополнением
- [ ] Добавить фильтры по категориям
- [ ] Добавить сортировку
- [ ] Добавить пагинацию
- [ ] Добавить загрузку изображений
- [ ] Добавить отзывы
- [ ] Добавить уведомления
- [ ] Добавить i18n (русский/английский)
- [ ] Добавить темную/светлую тему
- [ ] Добавить анимации

## 🐛 Известные проблемы

- WebSocket может не работать в dev режиме (CORS)
- Нужно настроить HTTPS для продакшна
- Изображения пока не загружаются

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте что Backend запущен
2. Проверьте переменные окружения
3. Проверьте консоль браузера
4. Проверьте Network tab

---

Made with ❤️ and ☕
