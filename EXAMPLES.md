# Примеры использования

## 🛍️ Сценарии использования

### Сценарий 1: Покупатель покупает товар с автовыдачей

```
Покупатель:
1. /start
2. Выбирает "🎮 Игры"
3. Выбирает "Brawl Stars"
4. Выбирает "Валюта"
5. Выбирает "Gems 170"
6. Видит список лотов:
   - GameShop Pro - 150 ₽ ⭐4.8
   - FastGames - 145 ₽ ⭐4.5
   - TopSeller - 155 ₽ ⭐4.9
7. Выбирает FastGames (самая низкая цена)
8. Нажимает "🛒 Купить"
9. Подтверждает покупку
10. Получает код: CODE-123-456-XXXX-YYYY-ZZZZ
11. Подтверждает получение
12. Может оставить отзыв

Результат: Покупка завершена за 30 секунд!
```

### Сценарий 2: Продавец создает лот с автовыдачей

```
Продавец:
1. /seller
2. Вводит название магазина: "My Game Shop"
3. Ждет активации от админа
4. После активации: /seller
5. Выбирает "➕ Добавить лот"
6. Выбирает товар: "Brawl Stars - Gems 170"
7. Вводит название: "Gems 170 - Быстрая доставка"
8. Вводит описание: "Моментальная доставка, гарантия"
9. Вводит цену: 145
10. Выбирает тип доставки: "⚡ Автоматическая"
11. Добавляет коды (по одному на строку):
    CODE-001-XXXX-YYYY-ZZZZ
    CODE-002-XXXX-YYYY-ZZZZ
    CODE-003-XXXX-YYYY-ZZZZ
    ...
12. Активирует лот
13. Лот появляется в каталоге

Результат: Лот создан и готов к продаже!
```

### Сценарий 3: Ручная доставка с чатом

```
Покупатель:
1. Покупает товар с ручной доставкой
2. Получает уведомление: "Заказ создан"
3. /deals
4. Выбирает свою сделку
5. Нажимает "💬 Чат"
6. Пишет: "Здравствуйте, когда будет доставка?"

Продавец:
1. Получает уведомление: "Новый заказ"
2. /deals
3. Выбирает сделку
4. Нажимает "💬 Чат"
5. Видит сообщение покупателя
6. Отвечает: "Здравствуйте! Доставлю в течение 10 минут"
7. Подготавливает товар
8. Нажимает "📦 Доставить товар"
9. Отправляет данные: "Логин: user123, Пароль: pass456"

Покупатель:
1. Получает уведомление: "Товар доставлен"
2. Проверяет данные
3. Нажимает "✅ Подтвердить получение"

Результат: Сделка завершена, средства переведены продавцу!
```

### Сценарий 4: Спор и его разрешение

```
Покупатель:
1. Получил товар, но он не работает
2. /deals
3. Выбирает сделку
4. Нажимает "⚠️ Открыть спор"
5. Описывает проблему: "Код не активируется, пишет 'уже использован'"

Админ:
1. Получает уведомление о споре
2. /admin
3. Выбирает "⚠️ Споры"
4. Открывает спор
5. Читает переписку
6. Связывается с продавцом
7. Принимает решение: возврат средств
8. Нажимает "Решить в пользу покупателя"
9. Вводит решение: "Код действительно был использован. Возврат средств."

Покупатель:
1. Получает уведомление: "Спор решен"
2. Получает возврат средств

Продавец:
1. Получает предупреждение
2. Рейтинг снижается

Результат: Справедливое решение, покупатель защищен!
```

### Сценарий 5: Вывод средств продавцом

```
Продавец:
1. Накопил 5000 ₽ на балансе
2. /seller
3. Выбирает "💸 Вывести средства"
4. Вводит сумму: 5000
5. Выбирает способ: "Банковская карта"
6. Вводит реквизиты: 1234 5678 9012 3456
7. Подтверждает заявку

Админ:
1. Получает уведомление о заявке
2. /admin
3. Выбирает "💸 Выводы"
4. Проверяет заявку
5. Проверяет продавца (рейтинг, отзывы)
6. Переводит средства
7. Подтверждает выплату

Продавец:
1. Получает уведомление: "Средства выплачены"
2. Проверяет карту
3. Получил деньги!

Результат: Продавец получил свои заработанные средства!
```

## 💻 Примеры SQL запросов

### Активировать продавца
```sql
UPDATE sellers 
SET status = 'active', is_verified = true, verified_at = NOW() 
WHERE id = 1;
```

### Пополнить баланс пользователю
```sql
-- Обновить баланс
UPDATE users SET balance = balance + 1000 WHERE telegram_id = 123456789;

-- Создать транзакцию
INSERT INTO transactions (user_id, transaction_type, amount, status, balance_before, balance_after, description)
SELECT 
    id, 
    'deposit', 
    1000, 
    'completed', 
    balance - 1000, 
    balance, 
    'Пополнение баланса администратором'
FROM users WHERE telegram_id = 123456789;
```

### Посмотреть топ продавцов
```sql
SELECT 
    s.shop_name,
    s.rating,
    s.total_sales,
    s.total_reviews,
    u.username
FROM sellers s
JOIN users u ON s.user_id = u.id
WHERE s.status = 'active'
ORDER BY s.rating DESC, s.total_sales DESC
LIMIT 10;
```

### Посмотреть активные сделки
```sql
SELECT 
    d.id,
    d.status,
    d.amount,
    buyer.username as buyer,
    seller.shop_name as seller,
    l.title as lot_title
FROM deals d
JOIN users buyer ON d.buyer_id = buyer.id
JOIN sellers seller ON d.seller_id = seller.id
JOIN lots l ON d.lot_id = l.id
WHERE d.status IN ('paid', 'in_progress', 'waiting_confirmation')
ORDER BY d.created_at DESC;
```

### Статистика по продажам
```sql
SELECT 
    s.shop_name,
    COUNT(d.id) as total_deals,
    SUM(d.seller_amount) as total_earned,
    AVG(d.amount) as avg_deal_amount
FROM sellers s
LEFT JOIN deals d ON s.id = d.seller_id AND d.status = 'completed'
GROUP BY s.id, s.shop_name
ORDER BY total_earned DESC;
```

## 🐍 Примеры Python кода

### Создать продавца программно
```python
from app.db.session import SessionLocal
from app.services.seller import SellerService

async def create_seller_example():
    async with SessionLocal() as session:
        seller_service = SellerService(session)
        
        seller = await seller_service.create_seller(
            user_id=1,
            shop_name="Test Shop",
            description="Test description"
        )
        
        await seller_service.activate_seller(seller.id)
        await seller_service.verify_seller(seller.id)
        
        await session.commit()
        print(f"Seller created: {seller.shop_name}")
```

### Создать лот программно
```python
from app.db.session import SessionLocal
from app.services.lot import LotService
from app.models.enums import LotDeliveryType
from decimal import Decimal

async def create_lot_example():
    async with SessionLocal() as session:
        lot_service = LotService(session)
        
        lot = await lot_service.create_lot(
            seller_id=1,
            product_id=1,
            title="Test Product - Fast Delivery",
            price=Decimal("100.00"),
            description="Test lot",
            delivery_type=LotDeliveryType.AUTO,
            delivery_time_minutes=5
        )
        
        # Добавить коды
        codes = [f"CODE-{i:03d}-XXXX-YYYY" for i in range(1, 11)]
        await lot_service.add_stock_items(lot.id, codes)
        
        # Активировать
        await lot_service.activate_lot(lot.id)
        
        await session.commit()
        print(f"Lot created: {lot.title}")
```

### Обработать сделку программно
```python
from app.db.session import SessionLocal
from app.services.deal import DealService

async def process_deal_example():
    async with SessionLocal() as session:
        deal_service = DealService(session)
        
        # Создать сделку
        deal = await deal_service.create_deal(
            order_id=1,
            buyer_id=1,
            seller_id=1,
            lot_id=1,
            amount=Decimal("100.00")
        )
        
        # Отметить как оплаченную
        await deal_service.mark_as_paid(deal.id)
        
        # Для ручной доставки - доставить товар
        await deal_service.deliver_product(
            deal.id,
            "Your product code: XXXX-YYYY-ZZZZ"
        )
        
        # Покупатель подтверждает
        await deal_service.confirm_by_buyer(deal.id)
        
        await session.commit()
        print(f"Deal completed: {deal.id}")
```

## 🔧 Примеры настройки

### Изменить комиссию для продавца
```python
from app.db.session import SessionLocal
from decimal import Decimal

async def set_commission():
    async with SessionLocal() as session:
        from app.models.entities import Seller
        from sqlalchemy import update
        
        # Установить комиссию 5% для продавца с ID=1
        await session.execute(
            update(Seller)
            .where(Seller.id == 1)
            .values(commission_percent=Decimal("5.00"))
        )
        
        await session.commit()
```

### Настроить автозавершение сделок
```python
# В auto_complete_deals.py уже реализовано
# Запускайте через cron каждый час:
# 0 * * * * cd ~/bot && python auto_complete_deals.py
```

### Массовое добавление кодов
```python
from app.db.session import SessionLocal
from app.services.lot import LotService

async def bulk_add_codes():
    async with SessionLocal() as session:
        lot_service = LotService(session)
        
        # Читаем коды из файла
        with open('codes.txt', 'r') as f:
            codes = [line.strip() for line in f if line.strip()]
        
        # Добавляем в лот
        count = await lot_service.add_stock_items(lot_id=1, items_data=codes)
        
        await session.commit()
        print(f"Added {count} codes")
```

## 📊 Примеры отчетов

### Отчет по продажам за период
```sql
SELECT 
    DATE(d.created_at) as date,
    COUNT(d.id) as deals_count,
    SUM(d.amount) as total_amount,
    SUM(d.commission_amount) as total_commission,
    SUM(d.seller_amount) as total_to_sellers
FROM deals d
WHERE d.status = 'completed'
    AND d.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(d.created_at)
ORDER BY date DESC;
```

### Топ товаров
```sql
SELECT 
    p.title,
    COUNT(d.id) as sales_count,
    SUM(d.amount) as total_revenue
FROM deals d
JOIN lots l ON d.lot_id = l.id
JOIN products p ON l.product_id = p.id
WHERE d.status = 'completed'
GROUP BY p.id, p.title
ORDER BY sales_count DESC
LIMIT 10;
```

### Активность продавцов
```sql
SELECT 
    s.shop_name,
    COUNT(CASE WHEN d.created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as deals_last_week,
    COUNT(CASE WHEN d.created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as deals_last_month,
    s.rating,
    s.balance
FROM sellers s
LEFT JOIN deals d ON s.id = d.seller_id AND d.status = 'completed'
GROUP BY s.id, s.shop_name, s.rating, s.balance
ORDER BY deals_last_week DESC;
```

## 🎯 Полезные советы

### Для покупателей:
- Проверяйте рейтинг продавца перед покупкой
- Читайте отзывы других покупателей
- Используйте чат для уточнения деталей
- Подтверждайте получение только после проверки товара

### Для продавцов:
- Поддерживайте высокий рейтинг
- Быстро отвечайте в чате
- Используйте автовыдачу для популярных товаров
- Устанавливайте конкурентные цены
- Отвечайте на отзывы

### Для админов:
- Проверяйте продавцов перед активацией
- Быстро решайте споры
- Мониторьте подозрительную активность
- Регулярно делайте бэкапы
- Анализируйте статистику

Эти примеры помогут вам быстро освоить все возможности маркетплейса!
