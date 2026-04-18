"""Seed games, categories, products and prices using sync engine."""
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()

# Create sync engine
sync_engine = create_engine(settings.sync_database_url, echo=False)

def seed():
    """Seed database with games, categories, products and prices."""
    print("🌱 Начинаем заполнение БД...")
    
    with sync_engine.begin() as conn:
        # Insert games
        print("  📦 Добавляем игры...")
        conn.execute(text("""
            INSERT INTO games (slug, title, is_active, sort_order, is_deleted, created_at, updated_at) VALUES
            ('brawl-stars', 'Brawl Stars', true, 1, false, NOW(), NOW()),
            ('standoff-2', 'Standoff 2', true, 2, false, NOW(), NOW()),
            ('clash-of-clans', 'Clash of Clans', true, 3, false, NOW(), NOW()),
            ('clash-royale', 'Clash Royale', true, 4, false, NOW(), NOW()),
            ('roblox', 'Roblox', true, 5, false, NOW(), NOW()),
            ('minecraft', 'Minecraft', true, 6, false, NOW(), NOW()),
            ('genshin-impact', 'Genshin Impact', true, 7, false, NOW(), NOW()),
            ('honkai-star-rail', 'Honkai: Star Rail', true, 8, false, NOW(), NOW()),
            ('pubg-mobile', 'PUBG Mobile', true, 9, false, NOW(), NOW()),
            ('free-fire', 'Free Fire', true, 10, false, NOW(), NOW()),
            ('valorant', 'Valorant', true, 11, false, NOW(), NOW()),
            ('cs2', 'Counter-Strike 2', true, 12, false, NOW(), NOW()),
            ('dota-2', 'Dota 2', true, 13, false, NOW(), NOW()),
            ('league-of-legends', 'League of Legends', true, 14, false, NOW(), NOW()),
            ('fortnite', 'Fortnite', true, 15, false, NOW(), NOW()),
            ('apex-legends', 'Apex Legends', true, 16, false, NOW(), NOW()),
            ('call-of-duty-mobile', 'Call of Duty Mobile', true, 17, false, NOW(), NOW()),
            ('mobile-legends', 'Mobile Legends', true, 18, false, NOW(), NOW()),
            ('arena-of-valor', 'Arena of Valor', true, 19, false, NOW(), NOW()),
            ('wild-rift', 'Wild Rift', true, 20, false, NOW(), NOW())
            ON CONFLICT (slug) DO NOTHING
        """))
        
        # Insert categories for Brawl Stars
        print("  📂 Добавляем категории...")
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'gems', 'Гемы', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'brawl-stars'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'accounts', 'Аккаунты', true, 2, false, NOW(), NOW() FROM games WHERE slug = 'brawl-stars'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Categories for Standoff 2
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'gold', 'Золото', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'standoff-2'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'skins', 'Скины', true, 2, false, NOW(), NOW() FROM games WHERE slug = 'standoff-2'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Categories for Roblox
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'robux', 'Robux', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'roblox'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Categories for Genshin Impact
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'primogems', 'Примогемы', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'genshin-impact'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'accounts', 'Аккаунты', true, 2, false, NOW(), NOW() FROM games WHERE slug = 'genshin-impact'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Categories for Minecraft
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'accounts', 'Аккаунты', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'minecraft'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Categories for CS2
        conn.execute(text("""
            INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
            SELECT id, 'skins', 'Скины', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'cs2'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Insert products
        print("  🎮 Добавляем товары...")
        
        # Brawl Stars products
        conn.execute(text("""
            INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
            SELECT g.id, c.id, 'brawl-stars-gems-30', '30 гемов', true, true, 1, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
            FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'brawl-stars' AND c.slug = 'gems'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
            SELECT g.id, c.id, 'brawl-stars-gems-80', '80 гемов', true, false, 2, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
            FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'brawl-stars' AND c.slug = 'gems'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
            SELECT g.id, c.id, 'brawl-stars-gems-170', '170 гемов', true, false, 3, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
            FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'brawl-stars' AND c.slug = 'gems'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Roblox products
        conn.execute(text("""
            INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
            SELECT g.id, c.id, 'roblox-robux-400', '400 Robux', true, true, 1, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
            FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'roblox' AND c.slug = 'robux'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
            SELECT g.id, c.id, 'roblox-robux-800', '800 Robux', true, false, 2, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
            FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'roblox' AND c.slug = 'robux'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Genshin Impact products
        conn.execute(text("""
            INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
            SELECT g.id, c.id, 'genshin-primogems-60', '60 Примогемов', true, false, 1, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
            FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'genshin-impact' AND c.slug = 'primogems'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
            SELECT g.id, c.id, 'genshin-primogems-300', '300 Примогемов', true, false, 2, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
            FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'genshin-impact' AND c.slug = 'primogems'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Standoff 2 products
        conn.execute(text("""
            INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
            SELECT g.id, c.id, 'standoff-2-gold-1000', '1000 золота', true, false, 1, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
            FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'standoff-2' AND c.slug = 'gold'
            ON CONFLICT (game_id, slug) DO NOTHING
        """))
        
        # Insert prices
        print("  💰 Добавляем цены...")
        
        conn.execute(text("""
            INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
            SELECT id, 99.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'brawl-stars-gems-30'
            ON CONFLICT DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
            SELECT id, 249.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'brawl-stars-gems-80'
            ON CONFLICT DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
            SELECT id, 499.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'brawl-stars-gems-170'
            ON CONFLICT DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
            SELECT id, 299.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'roblox-robux-400'
            ON CONFLICT DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
            SELECT id, 599.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'roblox-robux-800'
            ON CONFLICT DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
            SELECT id, 59.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'genshin-primogems-60'
            ON CONFLICT DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
            SELECT id, 299.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'genshin-primogems-300'
            ON CONFLICT DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
            SELECT id, 149.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'standoff-2-gold-1000'
            ON CONFLICT DO NOTHING
        """))
        
        print("✅ База данных успешно заполнена!")
        print("  📊 Добавлено: 20 игр, категории, товары и цены")

if __name__ == "__main__":
    seed()
