from __future__ import annotations

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Category, Game, Price, Product
from app.repositories.base import BaseRepository


class GameRepository(BaseRepository[Game]):
    model = Game
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_active(self) -> list[Game]:
        stmt = (
            select(Game)
            .where(Game.is_active.is_(True), Game.is_deleted.is_(False))
            .options(joinedload(Game.image))
            .order_by(Game.sort_order.asc(), Game.id.asc())
        )
        return list(await self.session.scalars(stmt))


class CategoryRepository(BaseRepository[Category]):
    model = Category
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_by_game(self, game_id: int) -> list[Category]:
        stmt = (
            select(Category)
            .where(
                Category.game_id == game_id,
                Category.is_active.is_(True),
                Category.is_deleted.is_(False),
            )
            .options(joinedload(Category.image))
            .order_by(Category.sort_order.asc(), Category.id.asc())
        )
        return list(await self.session.scalars(stmt))


class ProductRepository(BaseRepository[Product]):
    model = Product
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_full(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.is_deleted.is_(False))
            .options(joinedload(Product.image), joinedload(Product.game), joinedload(Product.category), selectinload(Product.prices))
        )
        return await self.session.scalar(stmt)

    async def list_by_category(self, category_id: int, *, limit: int, offset: int) -> list[Product]:
        stmt = (
            select(Product)
            .where(
                Product.category_id == category_id,
                Product.is_active.is_(True),
                Product.is_deleted.is_(False),
            )
            .options(joinedload(Product.image), selectinload(Product.prices))
            .order_by(Product.sort_order.asc(), Product.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(await self.session.scalars(stmt))

    async def count_by_category(self, category_id: int) -> int:
        stmt = select(Product.id).where(
            Product.category_id == category_id,
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
        return len(list(await self.session.scalars(stmt)))


class PriceRepository(BaseRepository[Price]):
    model = Price
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_current_for_product(self, product_id: int) -> Price | None:
        from sqlalchemy import func

        now = func.now()
        stmt = (
            select(Price)
            .where(
                Price.product_id == product_id,
                Price.is_active.is_(True),
                or_(Price.starts_at.is_(None), Price.starts_at <= now),
                or_(Price.ends_at.is_(None), Price.ends_at >= now),
            )
            .order_by(Price.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)
