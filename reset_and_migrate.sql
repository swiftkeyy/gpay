-- ВНИМАНИЕ: Этот скрипт удалит ВСЕ данные!
-- Используй только если готов потерять все данные в базе

-- Удалить таблицу версий Alembic
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Удалить все таблицы (в обратном порядке зависимостей)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS user_blocks CASCADE;
DROP TABLE IF EXISTS broadcasts CASCADE;
DROP TABLE IF EXISTS bot_settings CASCADE;
DROP TABLE IF EXISTS referral_rewards CASCADE;
DROP TABLE IF EXISTS referrals CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS order_status_history CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS promo_code_usages CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS promo_codes CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS carts CASCADE;
DROP TABLE IF EXISTS lot_stock_items CASCADE;
DROP TABLE IF EXISTS deal_disputes CASCADE;
DROP TABLE IF EXISTS deal_messages CASCADE;
DROP TABLE IF EXISTS deals CASCADE;
DROP TABLE IF EXISTS lots CASCADE;
DROP TABLE IF EXISTS seller_withdrawals CASCADE;
DROP TABLE IF EXISTS seller_reviews CASCADE;
DROP TABLE IF EXISTS sellers CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS favorites CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS prices CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS games CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS media_files CASCADE;

-- Готово! Теперь можно запустить миграции заново
-- Railway автоматически запустит: alembic upgrade head
