"""Simplified bot - only welcome message and Mini App button."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Handle /start command - show welcome and Mini App button."""
    
    # Create Mini App button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Открыть магазин",
                    web_app=WebAppInfo(url="https://gpay-frontend-at0uiargi-swiftkeyys-projects.vercel.app")
                )
            ]
        ]
    )
    
    welcome_text = (
        "👋 <b>Добро пожаловать в Game Pay!</b>\n\n"
        "🎮 Маркетплейс игровых товаров\n"
        "💎 Покупай и продавай игровые предметы безопасно\n\n"
        "Нажми кнопку ниже, чтобы открыть магазин:"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=keyboard
    )


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    
    logger.info("🚀 Starting simplified bot...")
    
    await dp.start_polling(bot, allowed_updates=["message"])


if __name__ == "__main__":
    asyncio.run(main())
