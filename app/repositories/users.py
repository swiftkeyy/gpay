from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Admin, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await self.session.scalar(stmt)


class AdminRepository(BaseRepository[Admin]):
    model = Admin
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_telegram_id(self, telegram_id: int) -> Admin | None:
        stmt = select(Admin).join(User).where(User.telegram_id == telegram_id, Admin.is_active.is_(True))
        return await self.session.scalar(stmt)
