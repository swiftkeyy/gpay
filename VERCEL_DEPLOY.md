# Деплой Frontend на Vercel

## Шаг 1: Установи Vercel CLI (если ещё не установлен)

```bash
npm install -g vercel
```

## Шаг 2: Залогинься в Vercel

```bash
vercel login
```

Выбери способ входа (GitHub, GitLab, Bitbucket или Email).

## Шаг 3: Перейди в папку frontend

```bash
cd ПРОЕКТЫ/gpay-main/frontend
```

## Шаг 4: Задеплой на Vercel

```bash
vercel
```

Vercel задаст несколько вопросов:

1. **Set up and deploy?** → `Y` (Yes)
2. **Which scope?** → Выбери свой аккаунт
3. **Link to existing project?** → `N` (No, создать новый)
4. **What's your project's name?** → `gpay-frontend` (или любое другое имя)
5. **In which directory is your code located?** → `.` (текущая папка)
6. **Want to override the settings?** → `N` (No, использовать автоопределение)

Vercel автоматически:
- Определит, что это Vite проект
- Установит зависимости (`npm install`)
- Соберёт проект (`npm run build`)
- Задеплоит на URL типа `https://gpay-frontend-xxx.vercel.app`

## Шаг 5: Настрой переменные окружения

После деплоя нужно добавить переменные окружения:

### Вариант 1: Через веб-интерфейс Vercel

1. Открой https://vercel.com/dashboard
2. Найди свой проект `gpay-frontend`
3. Перейди в **Settings** → **Environment Variables**
4. Добавь переменные:

```
VITE_API_URL = https://твой-railway-url.railway.app/api/v1
VITE_WS_URL = wss://твой-railway-url.railway.app/api/v1
```

**Важно:** Замени `твой-railway-url.railway.app` на реальный URL твоего Railway деплоймента!

### Вариант 2: Через CLI

```bash
vercel env add VITE_API_URL
# Вставь: https://твой-railway-url.railway.app/api/v1

vercel env add VITE_WS_URL
# Вставь: wss://твой-railway-url.railway.app/api/v1
```

## Шаг 6: Передеплой с новыми переменными

```bash
vercel --prod
```

## Шаг 7: Получи финальный URL

После деплоя Vercel покажет URL типа:
```
✅ Production: https://gpay-frontend.vercel.app
```

Скопируй этот URL - он понадобится для подключения к боту!

---

## Шаг 8: Подключи Mini App к боту

### Через BotFather:

1. Открой Telegram и найди **@BotFather**
2. Отправь команду: `/mybots`
3. Выбери своего бота **@GamePay_marketbot**
4. Нажми **Bot Settings**
5. Нажми **Menu Button**
6. Нажми **Configure menu button**
7. Отправь URL: `https://gpay-frontend.vercel.app`
8. Отправь текст кнопки: `🚀 Открыть маркетплейс`

Готово! Теперь в чате с ботом появится кнопка "Открыть маркетплейс".

---

## Альтернатива: Деплой через GitHub

Если хочешь автоматический деплой при каждом push:

1. Залей код на GitHub (если ещё не залит)
2. Открой https://vercel.com/new
3. Нажми **Import Git Repository**
4. Выбери свой репозиторий
5. В **Root Directory** укажи: `frontend`
6. Добавь переменные окружения (как в Шаге 5)
7. Нажми **Deploy**

Теперь при каждом push в GitHub Vercel будет автоматически деплоить новую версию!

---

## Проверка деплоя

После деплоя открой URL в браузере и проверь:

1. ✅ Страница загружается
2. ✅ Нет ошибок в консоли (F12 → Console)
3. ✅ API запросы идут на правильный URL
4. ✅ Telegram WebApp SDK работает (если открыть через бот)

---

## Troubleshooting

### Ошибка: "Failed to fetch"

**Проблема:** Frontend не может подключиться к backend.

**Решение:**
1. Проверь, что `VITE_API_URL` правильный
2. Проверь, что backend запущен на Railway
3. Проверь CORS настройки в backend (должен разрешать твой Vercel домен)

### Ошибка: "WebSocket connection failed"

**Проблема:** WebSocket не работает.

**Решение:**
1. Проверь, что `VITE_WS_URL` использует `wss://` (не `ws://`)
2. Проверь, что Railway поддерживает WebSocket (должен по умолчанию)

### Страница пустая / белый экран

**Проблема:** Ошибка при сборке или загрузке.

**Решение:**
1. Открой консоль браузера (F12)
2. Посмотри ошибки
3. Проверь логи сборки в Vercel Dashboard

---

## Команды для управления

```bash
# Посмотреть список деплойментов
vercel ls

# Посмотреть логи
vercel logs

# Удалить деплоймент
vercel rm <deployment-url>

# Открыть проект в браузере
vercel open
```

---

## Готово! 🎉

Теперь у тебя:
- ✅ Backend на Railway
- ✅ Frontend на Vercel
- ✅ Mini App подключен к боту

Пользователи могут открыть маркетплейс прямо в Telegram!
