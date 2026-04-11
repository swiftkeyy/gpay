from __future__ import annotations

from sqlalchemy import select

from app.models import Admin, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await self.session.scalar(stmt)


class AdminRepository(BaseRepository[Admin]):
    model = Admin

    async def get_by_telegram_id(self, telegram_id: int) -> Admin | None:
        stmt = select(Admin).join(User).where(User.telegram_id == telegram_id, Admin.is_active.is_(True))
        return await self.session.scalar(stmt)
