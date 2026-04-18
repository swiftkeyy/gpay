"""Seed games and categories."""
import asyncio
from sqlalchemy import select

from app.db.session import async_session_maker
from app.models.entities import Game, Category

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


async def seed_games():
    """Seed games and categories."""
    async with async_session_maker() as session:
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
                    print(f"  ✓ {game.title} → {category.title}")
        
        await session.commit()
        print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_games())
