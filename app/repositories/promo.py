from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PromoCode, PromoCodeUsage
from app.repositories.base import BaseRepository


class PromoCodeRepository(BaseRepository[PromoCode]):
    model = PromoCode
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_code(self, code: str) -> PromoCode | None:
        stmt = select(PromoCode).where(PromoCode.code == code.upper(), PromoCode.is_deleted.is_(False))
        return await self.session.scalar(stmt)


class PromoCodeUsageRepository(BaseRepository[PromoCodeUsage]):
    model = PromoCodeUsage
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
