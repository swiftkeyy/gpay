from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select, update, and_, or_, Integer as sa_Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Lot, LotStockItem, Product, Seller
from app.models.enums import LotStatus, LotDeliveryType
from app.repositories.base import BaseRepository


class LotRepository(BaseRepository[Lot]):
    def __init__(self, session: AsyncSession):
        super().__init__(Lot, session)

    async def get_by_id_with_relations(self, lot_id: int) -> Lot | None:
        stmt = (
            select(Lot)
            .where(Lot.id == lot_id)
            .options(
                selectinload(Lot.seller).selectinload(Seller.user),
                selectinload(Lot.product),
                selectinload(Lot.stock_items)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_lots_by_product(
        self,
        product_id: int,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "price"
    ) -> list[Lot]:
        stmt = (
            select(Lot)
            .where(
                Lot.product_id == product_id,
                Lot.status == LotStatus.ACTIVE,
                Lot.is_deleted == False,
                Lot.stock_count > Lot.reserved_count
            )
            .options(selectinload(Lot.seller).selectinload(Seller.user))
        )
        
        if sort_by == "price":
            stmt = stmt.order_by(Lot.price.asc())
        elif sort_by == "rating":
            stmt = stmt.join(Seller).order_by(Seller.rating.desc())
        elif sort_by == "sales":
            stmt = stmt.join(Seller).order_by(Seller.total_sales.desc())
        
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_seller_lots(
        self,
        seller_id: int,
        include_deleted: bool = False
    ) -> list[Lot]:
        stmt = select(Lot).where(Lot.seller_id == seller_id)
        
        if not include_deleted:
            stmt = stmt.where(Lot.is_deleted == False)
        
        stmt = stmt.options(selectinload(Lot.product)).order_by(Lot.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_stock_counts(self, lot_id: int) -> None:
        """Recalculate stock and reserved counts from stock items"""
        from sqlalchemy import func, Integer
        
        stock_stmt = (
            select(
                func.count(LotStockItem.id).label("total"),
                func.sum(func.cast(LotStockItem.is_reserved, Integer)).label("reserved"),
                func.sum(func.cast(LotStockItem.is_sold, Integer)).label("sold")
            )
            .where(LotStockItem.lot_id == lot_id)
        )
        result = await self.session.execute(stock_stmt)
        row = result.one()
        
        total = row.total or 0
        reserved = row.reserved or 0
        sold = row.sold or 0
        available = total - sold
        
        await self.session.execute(
            update(Lot)
            .where(Lot.id == lot_id)
            .values(
                stock_count=available,
                reserved_count=reserved,
                sold_count=sold
            )
        )

    async def search_lots(
        self,
        query: str | None = None,
        game_id: int | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        delivery_type: LotDeliveryType | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Lot]:
        stmt = (
            select(Lot)
            .join(Product)
            .where(
                Lot.status == LotStatus.ACTIVE,
                Lot.is_deleted == False,
                Lot.stock_count > Lot.reserved_count
            )
            .options(
                selectinload(Lot.seller).selectinload(Seller.user),
                selectinload(Lot.product)
            )
        )
        
        if query:
            stmt = stmt.where(
                or_(
                    Lot.title.ilike(f"%{query}%"),
                    Product.title.ilike(f"%{query}%")
                )
            )
        
        if game_id:
            stmt = stmt.where(Product.game_id == game_id)
        
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        
        if min_price:
            stmt = stmt.where(Lot.price >= min_price)
        
        if max_price:
            stmt = stmt.where(Lot.price <= max_price)
        
        if delivery_type:
            stmt = stmt.where(Lot.delivery_type == delivery_type)
        
        stmt = stmt.order_by(Lot.price.asc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class LotStockItemRepository(BaseRepository[LotStockItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(LotStockItem, session)

    async def get_available_item(self, lot_id: int) -> LotStockItem | None:
        """Get first available (not sold, not reserved) stock item"""
        stmt = (
            select(LotStockItem)
            .where(
                LotStockItem.lot_id == lot_id,
                LotStockItem.is_sold == False,
                LotStockItem.is_reserved == False
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def reserve_item(self, item_id: int, deal_id: int, minutes: int = 15) -> None:
        """Reserve stock item for a deal"""
        from datetime import datetime, timedelta
        
        reserved_until = datetime.utcnow() + timedelta(minutes=minutes)
        await self.session.execute(
            update(LotStockItem)
            .where(LotStockItem.id == item_id)
            .values(
                is_reserved=True,
                reserved_until=reserved_until,
                deal_id=deal_id
            )
        )

    async def mark_as_sold(self, item_id: int) -> None:
        """Mark stock item as sold"""
        from datetime import datetime
        
        await self.session.execute(
            update(LotStockItem)
            .where(LotStockItem.id == item_id)
            .values(
                is_sold=True,
                is_reserved=False,
                sold_at=datetime.utcnow()
            )
        )

    async def release_reservation(self, item_id: int) -> None:
        """Release reserved stock item"""
        await self.session.execute(
            update(LotStockItem)
            .where(LotStockItem.id == item_id)
            .values(
                is_reserved=False,
                reserved_until=None,
                deal_id=None
            )
        )
