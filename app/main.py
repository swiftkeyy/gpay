from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.core.config import get_settings

# USER HANDLERS
from app.handlers.user import (
    start,
    catalog,
    cart,
    orders,
    profile,
    support,
    reviews,
)

# MIDDLEWARES
from app.middlewares.block import BlockMiddleware
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.user_context import UserContextMiddleware

settings = get_settings()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)

    dp = Dispatcher(storage=storage)

    # middlewares
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(UserContextMiddleware())
    dp.update.middleware(BlockMiddleware())

    # routers (ВАЖНО)
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(orders.router)
    dp.include_router(profile.router)
    dp.include_router(support.router)
    dp.include_router(reviews.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
