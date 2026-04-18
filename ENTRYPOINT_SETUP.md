# 🚀 Настройка Entrypoint для Railway

## Что сделано:

✅ Создан `entrypoint.sh` - скрипт запуска с миграциями
✅ Обновлен `Dockerfile` - использует entrypoint
✅ Обновлен `docker-compose.yml` - использует entrypoint
✅ Обновлена документация `RAILWAY_FULL_DEPLOY.md`

---

## Что нужно сделать в Railway:

### 1. Настрой Start Command

Зайди в Railway → твой сервис **gpay** → **Settings** → **Deploy**

**Start Command:** (замени на это)
```bash
./entrypoint.sh
```

**Pre-deploy command:** (оставь пустым или удали)

Нажми **Save**

### 2. Redeploy

Нажми **Redeploy** или сделай коммит:

```bash
cd ПРОЕКТЫ/gpay-main
git add .
git commit -m "Add entrypoint.sh for proper startup"
git push
```

---

## Что делает entrypoint.sh:

1. 📦 Запускает миграции Alembic (`alembic upgrade head`)
2. ✅ Проверяет успешность миграций
3. 🚀 Запускает бота (`python -m app.main`)

---

## Преимущества:

✅ Миграции всегда выполняются перед запуском
✅ Защита от ошибок дублирования таблиц
✅ Бот не запустится, если миграции упали
✅ Railway больше не будет показывать "Completed" сразу
✅ Работает и локально (docker-compose), и на Railway

---

## Проверка после деплоя:

1. Открой **Deploy Logs** в Railway
2. Должны увидеть:
   ```
   🚀 Запуск gpay маркетплейса (модернизированная версия)...
   📦 Применяем Alembic миграции...
   INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
   INFO  [alembic.runtime.migration] Will assume transactional DDL.
   ✅ Всё готово. Запускаем бот...
   ```

3. Бот должен запуститься и работать

---

## Если что-то пошло не так:

### Ошибка "permission denied: ./entrypoint.sh"
- Проверь, что в Dockerfile есть `RUN chmod +x /app/entrypoint.sh`
- Redeploy

### Миграции падают
- Проверь логи миграций
- Убедись, что `alembic_version` таблица существует и содержит `20260418_000001`

### Бот не запускается
- Проверь переменные окружения (BOT_TOKEN, DATABASE_URL, REDIS_URL)
- Проверь логи после строки "✅ Всё готово. Запускаем бот..."

---

Made with ❤️ by Kiro AI
