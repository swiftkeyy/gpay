"""Seed games, categories, products and prices."""
import asyncio
from decimal import Decimal
from sqlalchemy import select

from app.db.session import session_factory
from app.models.entities import Game, Category, Product, Price

GAMES_DATA = [
    {"slug": "brawl-stars", "title": "Brawl Stars", "sort_order": 1},
    {"slug": "standoff-2", "title": "Standoff 2", "sort_order": 2},
    {"slug": "clash-of-clans", "title": "Clash of Clans", "sort_order": 3},
    {"slug": "clash-royale", "title": "Clash Royale", "sort_order": 4},
    {"slug": "roblox", "title": "Roblox", "sort_order": 5},
    {"slug": "minecraft", "title": "Minecraft", "sort_order": 6},
    {"slug": "genshin-impact", "title": "Genshin Impact", "sort_order": 7},
    {"slug": "honkai-star-rail", "title": "Honkai: Star Rail", "sort_order": 8},
    {"slug": "pubg-mobile", "title": "PUBG Mobile", "sort_order": 9},
    {"slug": "free-fire", "title": "Free Fire", "sort_order": 10},
    {"slug": "valorant", "title": "Valorant", "sort_order": 11},
    {"slug": "cs2", "title": "Counter-Strike 2", "sort_order": 12},
    {"slug": "dota-2", "title": "Dota 2", "sort_order": 13},
    {"slug": "league-of-legends", "title": "League of Legends", "sort_order": 14},
    {"slug": "fortnite", "title": "Fortnite", "sort_order": 15},
    {"slug": "apex-legends", "title": "Apex Legends", "sort_order": 16},
    {"slug": "call-of-duty-mobile", "title": "Call of Duty Mobile", "sort_order": 17},
    {"slug": "mobile-legends", "title": "Mobile Legends", "sort_order": 18},
    {"slug": "arena-of-valor", "title": "Arena of Valor", "sort_order": 19},
    {"slug": "wild-rift", "title": "Wild Rift", "sort_order": 20},
]

CATEGORIES_DATA = {
    "brawl-stars": [
        {"slug": "gems", "title": "Гемы", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "brawl-pass", "title": "Brawl Pass", "sort_order": 3},
    ],
    "standoff-2": [
        {"slug": "gold", "title": "Золото", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "skins", "title": "Скины", "sort_order": 3},
    ],
    "clash-of-clans": [
        {"slug": "gems", "title": "Гемы", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "gold-pass", "title": "Gold Pass", "sort_order": 3},
    ],
    "roblox": [
        {"slug": "robux", "title": "Robux", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "game-passes", "title": "Game Passes", "sort_order": 3},
    ],
    "minecraft": [
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 1},
        {"slug": "minecoins", "title": "Minecoins", "sort_order": 2},
        {"slug": "realms", "title": "Realms", "sort_order": 3},
    ],
    "genshin-impact": [
        {"slug": "primogems", "title": "Примогемы", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "welkin-moon", "title": "Welkin Moon", "sort_order": 3},
    ],
    "pubg-mobile": [
        {"slug": "uc", "title": "UC", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "royal-pass", "title": "Royal Pass", "sort_order": 3},
    ],
    "valorant": [
        {"slug": "vp", "title": "Valorant Points", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "battle-pass", "title": "Battle Pass", "sort_order": 3},
    ],
    "cs2": [
        {"slug": "skins", "title": "Скины", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "cases", "title": "Кейсы", "sort_order": 3},
    ],
    "dota-2": [
        {"slug": "items", "title": "Предметы", "sort_order": 1},
        {"slug": "accounts", "title": "Аккаунты", "sort_order": 2},
        {"slug": "battle-pass", "title": "Battle Pass", "sort_order": 3},
    ],
}

# Товары для каждой категории
PRODUCTS_DATA = {
    "gems": [
        {"slug": "gems-30", "title": "30 гемов", "price": 99},
        {"slug": "gems-80", "title": "80 гемов", "price": 249},
        {"slug": "gems-170", "title": "170 гемов", "price": 499},
        {"slug": "gems-360", "title": "360 гемов", "price": 999},
        {"slug": "gems-950", "title": "950 гемов", "price": 2499},
        {"slug": "gems-2000", "title": "2000 гемов", "price": 4999},
    ],
    "gold": [
        {"slug": "gold-1000", "title": "1000 золота", "price": 49},
        {"slug": "gold-5000", "title": "5000 золота", "price": 199},
        {"slug": "gold-10000", "title": "10000 золота", "price": 349},
        {"slug": "gold-50000", "title": "50000 золота", "price": 1499},
    ],
    "robux": [
        {"slug": "robux-400", "title": "400 Robux", "price": 299},
        {"slug": "robux-800", "title": "800 Robux", "price": 599},
        {"slug": "robux-1700", "title": "1700 Robux", "price": 1199},
        {"slug": "robux-4500", "title": "4500 Robux", "price": 2999},
    ],
    "primogems": [
        {"slug": "primogems-60", "title": "60 Примогемов", "price": 59},
        {"slug": "primogems-300", "title": "300 Примогемов", "price": 299},
        {"slug": "primogems-980", "title": "980 Примогемов", "price": 899},
        {"slug": "primogems-1980", "title": "1980 Примогемов", "price": 1799},
        {"slug": "primogems-3280", "title": "3280 Примогемов", "price": 2999},
        {"slug": "primogems-6480", "title": "6480 Примогемов", "price": 5999},
    ],
    "uc": [
        {"slug": "uc-60", "title": "60 UC", "price": 59},
        {"slug": "uc-325", "title": "325 UC", "price": 299},
        {"slug": "uc-660", "title": "660 UC", "price": 599},
        {"slug": "uc-1800", "title": "1800 UC", "price": 1499},
    ],
    "vp": [
        {"slug": "vp-475", "title": "475 VP", "price": 399},
        {"slug": "vp-1000", "title": "1000 VP", "price": 799},
        {"slug": "vp-2050", "title": "2050 VP", "price": 1599},
        {"slug": "vp-3650", "title": "3650 VP", "price": 2799},
    ],
    "accounts": [
        {"slug": "starter-account", "title": "Стартовый аккаунт", "price": 199},
        {"slug": "mid-account", "title": "Средний аккаунт", "price": 999},
        {"slug": "high-account", "title": "Прокачанный аккаунт", "price": 2999},
        {"slug": "pro-account", "title": "ТОП аккаунт", "price": 9999},
    ],
    "brawl-pass": [
        {"slug": "brawl-pass-season", "title": "Brawl Pass (сезон)", "price": 169},
    ],
    "gold-pass": [
        {"slug": "gold-pass-month", "title": "Gold Pass (месяц)", "price": 399},
    ],
    "welkin-moon": [
        {"slug": "welkin-moon", "title": "Благословение луны", "price": 299},
    ],
    "royal-pass": [
        {"slug": "royal-pass-season", "title": "Royal Pass (сезон)", "price": 599},
    ],
    "battle-pass": [
        {"slug": "battle-pass-season", "title": "Battle Pass (сезон)", "price": 799},
    ],
    "minecoins": [
        {"slug": "minecoins-320", "title": "320 Minecoins", "price": 149},
        {"slug": "minecoins-1020", "title": "1020 Minecoins", "price": 449},
        {"slug": "minecoins-3500", "title": "3500 Minecoins", "price": 1499},
    ],
    "skins": [
        {"slug": "rare-skin", "title": "Редкий скин", "price": 299},
        {"slug": "epic-skin", "title": "Эпический скин", "price": 799},
        {"slug": "legendary-skin", "title": "Легендарный скин", "price": 1999},
    ],
    "items": [
        {"slug": "common-item", "title": "Обычный предмет", "price": 99},
        {"slug": "rare-item", "title": "Редкий предмет", "price": 299},
        {"slug": "mythical-item", "title": "Мифический предмет", "price": 999},
        {"slug": "immortal-item", "title": "Бессмертный предмет", "price": 2999},
    ],
    "cases": [
        {"slug": "weapon-case", "title": "Кейс с оружием", "price": 199},
        {"slug": "rare-case", "title": "Редкий кейс", "price": 499},
        {"slug": "operation-case", "title": "Операционный кейс", "price": 799},
    ],
    "game-passes": [
        {"slug": "vip-pass", "title": "VIP Pass", "price": 399},
        {"slug": "premium-pass", "title": "Premium Pass", "price": 799},
    ],
    "realms": [
        {"slug": "realm-1month", "title": "Realm (1 месяц)", "price": 499},
        {"slug": "realm-6months", "title": "Realm (6 месяцев)", "price": 2499},
    ],
}


async def seed_games():
    """Seed games, categories, products and prices."""
    async with session_factory() as session:
        # Check if games already exist
        result = await session.execute(select(Game).limit(1))
        if result.scalar_one_or_none():
            print("✅ Games already seeded")
            return
        
        print("🌱 Seeding games...")
        
        # Create games
        games_map = {}
        for game_data in GAMES_DATA:
            game = Game(**game_data, is_active=True)
            session.add(game)
            await session.flush()
            games_map[game.slug] = game
            print(f"  ✓ {game.title}")
        
        # Create categories
        print("\n🌱 Seeding categories...")
        categories_map = {}
        for game_slug, categories in CATEGORIES_DATA.items():
            if game_slug in games_map:
                game = games_map[game_slug]
                for cat_data in categories:
                    category = Category(
                        **cat_data,
                        game_id=game.id,
                        is_active=True
                    )
                    session.add(category)
                    await session.flush()
                    categories_map[f"{game_slug}:{cat_data['slug']}"] = category
                    print(f"  ✓ {game.title} → {category.title}")
        
        # Create products and prices
        print("\n🌱 Seeding products...")
        product_count = 0
        for cat_slug, products in PRODUCTS_DATA.items():
            # Find all categories with this slug
            matching_cats = [
                (key, cat) for key, cat in categories_map.items()
                if key.endswith(f":{cat_slug}")
            ]
            
            for cat_key, category in matching_cats:
                game_slug = cat_key.split(":")[0]
                game = games_map[game_slug]
                
                for prod_data in products:
                    product = Product(
                        slug=prod_data["slug"],
                        title=prod_data["title"],
                        game_id=game.id,
                        category_id=category.id,
                        is_active=True,
                        is_featured=(product_count % 5 == 0),  # Каждый 5-й товар featured
                    )
                    session.add(product)
                    await session.flush()
                    
                    # Create price
                    price = Price(
                        product_id=product.id,
                        base_price=Decimal(str(prod_data["price"])),
                        currency_code="RUB",
                        is_active=True,
                    )
                    session.add(price)
                    
                    product_count += 1
                    print(f"  ✓ {game.title} → {category.title} → {product.title} ({prod_data['price']} ₽)")
        
        await session.commit()
        print(f"\n✅ Seeding complete! Created {len(games_map)} games, {len(categories_map)} categories, {product_count} products!")


if __name__ == "__main__":
    asyncio.run(seed_games())
