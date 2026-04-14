from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar('ModelT', bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    def query(self) -> Select[tuple[ModelT]]:
        return select(self.model)

    async def get(self, entity_id: Any) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 20, offset: int = 0, **filters: Any) -> list[ModelT]:
        stmt = self.query().filter_by(**filters).limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return list(result)

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        return int(await self.session.scalar(stmt) or 0)

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update_by_id(self, entity_id: Any, **kwargs: Any) -> ModelT | None:
        stmt = update(self.model).where(self.model.id == entity_id).values(**kwargs).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_id(self, entity_id: Any) -> None:
        await self.session.execute(delete(self.model).where(self.model.id == entity_id))
