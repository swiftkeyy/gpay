from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Order, OrderStatusHistory
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    model = Order
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_full(self, order_id: int) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.status_history))
        )
        return await self.session.scalar(stmt)

    async def get_by_checkout_key(self, checkout_key: str) -> Order | None:
        stmt = select(Order).where(Order.checkout_key == checkout_key)
        return await self.session.scalar(stmt)

    async def list_by_user(self, user_id: int, *, status: str | None = None, limit: int = 20) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Order.status == status)
        return list(await self.session.scalars(stmt))

    async def list_recent(self, *, limit: int = 20) -> list[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), joinedload(Order.status_history))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars())


class OrderStatusHistoryRepository(BaseRepository[OrderStatusHistory]):
    model = OrderStatusHistory
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
