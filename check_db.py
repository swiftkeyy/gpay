"""
Скрипт для проверки состояния базы данных
"""
import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal


async def check_database():
    print("🔍 Проверка базы данных...\n")
    
    async with SessionLocal() as session:
        try:
            # Проверяем существующие таблицы
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"✅ Найдено таблиц: {len(tables)}\n")
            
            # Проверяем новые таблицы маркетплейса
            marketplace_tables = [
                'sellers', 'lots', 'lot_stock_items', 'deals', 
                'deal_messages', 'deal_disputes', 'transactions',
                'seller_withdrawals', 'seller_reviews', 'favorites', 'notifications'
            ]
            
            print("📋 Проверка таблиц маркетплейса:")
            for table in marketplace_tables:
                if table in tables:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} - НЕ НАЙДЕНА!")
            
            # Проверяем поле balance в users
            print("\n📋 Проверка поля balance в таблице users:")
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'balance'
            """))
            if result.fetchone():
                print("  ✅ Поле balance существует")
            else:
                print("  ❌ Поле balance НЕ НАЙДЕНО!")
            
            # Проверяем количество пользователей
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            users_count = result.scalar()
            print(f"\n👥 Пользователей в БД: {users_count}")
            
            # Проверяем продавцов
            if 'sellers' in tables:
                result = await session.execute(text("SELECT COUNT(*) FROM sellers"))
                sellers_count = result.scalar()
                print(f"🏪 Продавцов в БД: {sellers_count}")
            
            # Проверяем лоты
            if 'lots' in tables:
                result = await session.execute(text("SELECT COUNT(*) FROM lots WHERE is_deleted = false"))
                lots_count = result.scalar()
                print(f"📦 Активных лотов: {lots_count}")
            
            print("\n✅ Проверка завершена!")
            
        except Exception as e:
            print(f"\n❌ Ошибка при проверке БД: {e}")
            print("\n💡 Возможные причины:")
            print("  1. Миграция не применена - запустите: alembic upgrade head")
            print("  2. Неправильные данные подключения в .env")
            print("  3. PostgreSQL не запущен")


if __name__ == "__main__":
    asyncio.run(check_database())
