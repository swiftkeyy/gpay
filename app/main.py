from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.core.config import get_settings
from app.handlers.admin import panel
from app.handlers.user import cart, catalog, checkout, orders, profile, reviews, start, support
from app.middlewares.block import BlockMiddleware
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.user_context import UserContextMiddleware

settings = get_settings()


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)

    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(UserContextMiddleware())
    dp.update.middleware(BlockMiddleware())

    # user
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(orders.router)
    dp.include_router(profile.router)
    dp.include_router(support.router)
    dp.include_router(reviews.router)

    # admin: только один стабильный роутер
    dp.include_router(panel.router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
