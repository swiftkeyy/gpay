"""Seed games via raw SQL to bypass enum issues."""
import asyncio
from app.db.session import engine

SQL = """
-- Insert games
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
ON CONFLICT (slug) DO NOTHING;

-- Insert categories
INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
SELECT id, 'gems', 'Гемы', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'brawl-stars'
ON CONFLICT DO NOTHING;

INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
SELECT id, 'accounts', 'Аккаунты', true, 2, false, NOW(), NOW() FROM games WHERE slug = 'brawl-stars'
ON CONFLICT DO NOTHING;

INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
SELECT id, 'gold', 'Золото', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'standoff-2'
ON CONFLICT DO NOTHING;

INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
SELECT id, 'robux', 'Robux', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'roblox'
ON CONFLICT DO NOTHING;

INSERT INTO categories (game_id, slug, title, is_active, sort_order, is_deleted, created_at, updated_at)
SELECT id, 'primogems', 'Примогемы', true, 1, false, NOW(), NOW() FROM games WHERE slug = 'genshin-impact'
ON CONFLICT DO NOTHING;

-- Insert products
INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
SELECT g.id, c.id, 'brawl-stars-gems-30', '30 гемов', true, true, 1, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'brawl-stars' AND c.slug = 'gems'
ON CONFLICT DO NOTHING;

INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
SELECT g.id, c.id, 'brawl-stars-gems-80', '80 гемов', true, false, 2, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'brawl-stars' AND c.slug = 'gems'
ON CONFLICT DO NOTHING;

INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
SELECT g.id, c.id, 'roblox-robux-400', '400 Robux', true, false, 1, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'roblox' AND c.slug = 'robux'
ON CONFLICT DO NOTHING;

INSERT INTO products (game_id, category_id, slug, title, is_active, is_featured, sort_order, is_deleted, fulfillment_type, requires_player_id, requires_nickname, requires_region, requires_manual_review, requires_screenshot, extra_fields_schema_json, created_at, updated_at)
SELECT g.id, c.id, 'genshin-primogems-60', '60 Примогемов', true, false, 1, false, 'manual', false, false, false, false, false, '{}'::jsonb, NOW(), NOW()
FROM games g JOIN categories c ON c.game_id = g.id WHERE g.slug = 'genshin-impact' AND c.slug = 'primogems'
ON CONFLICT DO NOTHING;

-- Insert prices
INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
SELECT id, 99.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'brawl-stars-gems-30'
ON CONFLICT DO NOTHING;

INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
SELECT id, 249.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'brawl-stars-gems-80'
ON CONFLICT DO NOTHING;

INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
SELECT id, 299.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'roblox-robux-400'
ON CONFLICT DO NOTHING;

INSERT INTO prices (product_id, base_price, currency_code, is_active, created_at, updated_at)
SELECT id, 59.00, 'RUB', true, NOW(), NOW() FROM products WHERE slug = 'genshin-primogems-60'
ON CONFLICT DO NOTHING;
"""

async def seed():
    async with engine.begin() as conn:
        await conn.execute(SQL)
        print("✅ Games seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
