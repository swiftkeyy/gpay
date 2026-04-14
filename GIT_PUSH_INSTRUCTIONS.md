# 🚀 Инструкция для Git Push

## Шаг 1: Открой терминал

Открой PowerShell или Git Bash в папке проекта:
```
C:\Users\pp775\Desktop\ПРОЕКТЫ\gpay-main
```

Или через командную строку:
```bash
cd C:\Users\pp775\Desktop\ПРОЕКТЫ\gpay-main
```

---

## Шаг 2: Проверь статус

```bash
git status
```

Должно показать все измененные файлы (красным цветом).

---

## Шаг 3: Добавь все файлы

```bash
git add .
```

Это добавит ВСЕ измененные и новые файлы.

Или добавь только нужные файлы:
```bash
git add app/
git add alembic/
git add *.py
git add *.md
```

---

## Шаг 4: Проверь что добавлено

```bash
git status
```

Теперь файлы должны быть зелеными (готовы к коммиту).

---

## Шаг 5: Сделай коммит

```bash
git commit -m "Add marketplace features: sellers, lots, deals, transactions, chat"
```

Или с более подробным описанием:
```bash
git commit -m "Modernize bot to marketplace like FunPay/PlayerOK

- Add sellers system with profiles and ratings
- Add lots (offers) from multiple sellers
- Add deals with escrow protection
- Add buyer-seller chat
- Add auto-delivery for codes
- Add transactions and balances
- Add disputes and arbitration
- Add seller reviews
- Add notifications
- Add favorites
- Fix profile.py NoneType error
- Fix repositories __init__.py import error"
```

---

## Шаг 6: Отправь на GitHub

```bash
git push origin main
```

Или если ветка называется `master`:
```bash
git push origin master
```

Или просто:
```bash
git push
```

---

## ✅ Проверка

После успешного push:

1. **Открой GitHub** - проверь что коммит появился
2. **Подожди 1-2 минуты** - bothost.ru подтянет изменения
3. **Проверь логи** на bothost.ru - бот должен перезапуститься
4. **Отправь боту** `/start` - проверь что работает

---

## 🆘 Если ошибки

### Ошибка: "Please tell me who you are"
```bash
git config --global user.email "your@email.com"
git config --global user.name "Your Name"
```

### Ошибка: "Permission denied"
Нужно настроить SSH ключ или использовать HTTPS с токеном.

### Ошибка: "Your branch is behind"
```bash
git pull origin main
# Разреши конфликты если есть
git push origin main
```

### Ошибка: "fatal: not a git repository"
```bash
# Инициализируй репозиторий
git init
git remote add origin https://github.com/your-username/your-repo.git
git add .
git commit -m "Initial commit with marketplace features"
git push -u origin main
```

---

## 📋 Полная последовательность команд

Скопируй и выполни по порядку:

```bash
# 1. Перейди в папку
cd C:\Users\pp775\Desktop\ПРОЕКТЫ\gpay-main

# 2. Проверь статус
git status

# 3. Добавь все файлы
git add .

# 4. Проверь что добавлено
git status

# 5. Сделай коммит
git commit -m "Add marketplace features: sellers, lots, deals, chat"

# 6. Отправь на GitHub
git push

# 7. Проверь результат
git log --oneline -1
```

---

## 🎯 После успешного push

### На bothost.ru:

1. **Проверь логи деплоя** - должно быть "Deployment successful"
2. **Примени миграцию** (если не применяется автоматически):
   ```bash
   # Подключись по SSH
   ssh user@your-server.bothost.ru
   
   # Перейди в папку бота
   cd ~/bot
   
   # Примени миграцию
   alembic upgrade head
   ```

3. **Перезапусти бота** (если не перезапускается автоматически)
   - Через панель bothost.ru
   - Или: `systemctl restart bot`

4. **Проверь работу**:
   - Отправь боту `/start`
   - Попробуй `/seller`
   - Проверь каталог товаров

---

## ✅ Чеклист

- [ ] Открыл терминал в папке проекта
- [ ] Выполнил `git status`
- [ ] Выполнил `git add .`
- [ ] Выполнил `git commit -m "..."`
- [ ] Выполнил `git push`
- [ ] Коммит появился на GitHub
- [ ] Bothost.ru подтянул изменения
- [ ] Миграция применена
- [ ] Бот перезапущен
- [ ] Бот работает без ошибок

---

Готово! Выполняй команды по порядку и пиши если будут ошибки! 🚀
