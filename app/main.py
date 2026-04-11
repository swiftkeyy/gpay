from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, ErrorEvent, Message, Update
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.handlers.admin import broadcasts, catalog as admin_catalog, misc as admin_misc, orders as admin_orders, panel, prices, promos
from app.handlers.user import cart, catalog, checkout, orders, profile, reviews, start, support
from app.middlewares.block import BlockCheckMiddleware
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.user_context import UserContextMiddleware

logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    middlewares = [DbSessionMiddleware(), UserContextMiddleware(), BlockCheckMiddleware(), RateLimitMiddleware()]
    for mw in middlewares:
        dp.update.middleware(mw)

    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(orders.router)
    dp.include_router(profile.router)
    dp.include_router(reviews.router)
    dp.include_router(support.router)

    dp.include_router(panel.router)
    dp.include_router(admin_catalog.router)
    dp.include_router(admin_orders.router)
    dp.include_router(prices.router)
    dp.include_router(promos.router)
    dp.include_router(broadcasts.router)
    dp.include_router(admin_misc.router)

    @dp.callback_query(F.data == 'noop')
    async def noop(callback: CallbackQuery) -> None:
        await callback.answer()

    @dp.errors()
    async def on_error(event: ErrorEvent) -> None:
        update = event.update
        exc = event.exception
        logger.exception('Unhandled error: %s', exc)
        try:
            if update.callback_query:
                await update.callback_query.answer('Произошла ошибка. Попробуйте ещё раз.', show_alert=True)
            elif update.message:
                await update.message.answer('Произошла ошибка. Команда не выполнена.')
        except TelegramBadRequest:
            pass

    return dp


async def main() -> None:
    setup_logging()
    settings = get_settings()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher()
    logger.info('Starting Game Pay bot')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
