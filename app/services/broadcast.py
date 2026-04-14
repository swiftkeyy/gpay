from __future__ import annotations

import hashlib

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Broadcast, User
from app.models.enums import BroadcastStatus
from app.repositories.settings import BroadcastRepository


class BroadcastService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BroadcastRepository(session)

    async def send(self, bot: Bot, broadcast: Broadcast) -> int:
        send_hash = hashlib.sha256(f'{broadcast.title}:{broadcast.text}'.encode()).hexdigest()
        if broadcast.send_hash and broadcast.send_hash == send_hash and broadcast.status == BroadcastStatus.SENT:
            raise ValueError('Такая рассылка уже была отправлена.')
        users = list(await self.session.scalars(select(User).where(User.is_blocked.is_(False))))
        sent = 0
        for user in users:
            try:
                await bot.send_message(user.telegram_id, broadcast.text)
                sent += 1
            except TelegramBadRequest:
                continue
        broadcast.status = BroadcastStatus.SENT
        broadcast.send_hash = send_hash
        await self.session.flush()
        return sent
