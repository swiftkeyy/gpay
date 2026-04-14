from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Lot, LotStockItem
from app.models.enums import LotStatus, LotDeliveryType
from app.repositories.lots import LotRepository, LotStockItemRepository


class LotService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.lot_repo = LotRepository(session)
        self.stock_repo = LotStockItemRepository(session)

    async def create_lot(
        self,
        seller_id: int,
        product_id: int,
        title: str,
        price: Decimal,
        description: str | None = None,
        delivery_type: LotDeliveryType = LotDeliveryType.MANUAL,
        delivery_time_minutes: int | None = None
    ) -> Lot:
        """Create new lot"""
        lot = Lot(
            seller_id=seller_id,
            product_id=product_id,
            title=title,
            description=description,
            price=price,
            delivery_type=delivery_type,
            delivery_time_minutes=delivery_time_minutes,
            status=LotStatus.DRAFT
        )
        self.session.add(lot)
        await self.session.flush()
        return lot

    async def update_lot(
        self,
        lot_id: int,
        title: str | None = None,
        description: str | None = None,
        price: Decimal | None = None,
        delivery_type: LotDeliveryType | None = None,
        delivery_time_minutes: int | None = None
    ) -> Lot | None:
        """Update lot details"""
        lot = await self.lot_repo.get_by_id(lot_id)
        if not lot:
            return None
        
        if title is not None:
            lot.title = title
        if description is not None:
            lot.description = description
        if price is not None:
            lot.price = price
        if delivery_type is not None:
            lot.delivery_type = delivery_type
        if delivery_time_minutes is not None:
            lot.delivery_time_minutes = delivery_time_minutes
        
        await self.session.flush()
        return lot

    async def activate_lot(self, lot_id: int) -> bool:
        """Activate lot (make it visible)"""
        lot = await self.lot_repo.get_by_id(lot_id)
        if not lot:
            return False
        
        # Check if lot has stock for auto delivery
        if lot.delivery_type == LotDeliveryType.AUTO and lot.stock_count == 0:
            return False
        
        lot.status = LotStatus.ACTIVE
        await self.session.flush()
        return True

    async def pause_lot(self, lot_id: int) -> bool:
        """Pause lot (hide from catalog)"""
        lot = await self.lot_repo.get_by_id(lot_id)
        if not lot:
            return False
        
        lot.status = LotStatus.PAUSED
        await self.session.flush()
        return True

    async def delete_lot(self, lot_id: int) -> bool:
        """Soft delete lot"""
        lot = await self.lot_repo.get_by_id(lot_id)
        if not lot:
            return False
        
        lot.is_deleted = True
        lot.status = LotStatus.DELETED
        await self.session.flush()
        return True

    async def add_stock_items(
        self,
        lot_id: int,
        items_data: list[str]
    ) -> int:
        """Add stock items for auto-delivery"""
        lot = await self.lot_repo.get_by_id(lot_id)
        if not lot or lot.delivery_type != LotDeliveryType.AUTO:
            return 0
        
        added_count = 0
        for data in items_data:
            stock_item = LotStockItem(
                lot_id=lot_id,
                data=data
            )
            self.session.add(stock_item)
            added_count += 1
        
        await self.session.flush()
        await self.lot_repo.update_stock_counts(lot_id)
        
        # Update lot status if it was out of stock
        if lot.status == LotStatus.OUT_OF_STOCK:
            lot.status = LotStatus.ACTIVE
        
        await self.session.flush()
        return added_count

    async def reserve_stock_item(
        self,
        lot_id: int,
        deal_id: int,
        minutes: int = 15
    ) -> LotStockItem | None:
        """Reserve a stock item for purchase"""
        item = await self.stock_repo.get_available_item(lot_id)
        if not item:
            # Mark lot as out of stock
            lot = await self.lot_repo.get_by_id(lot_id)
            if lot:
                lot.status = LotStatus.OUT_OF_STOCK
                await self.session.flush()
            return None
        
        await self.stock_repo.reserve_item(item.id, deal_id, minutes)
        await self.lot_repo.update_stock_counts(lot_id)
        await self.session.flush()
        return item

    async def release_stock_item(self, item_id: int) -> None:
        """Release reserved stock item"""
        await self.stock_repo.release_reservation(item_id)
        
        # Get lot_id and update counts
        item = await self.stock_repo.get_by_id(item_id)
        if item:
            await self.lot_repo.update_stock_counts(item.lot_id)
        
        await self.session.flush()

    async def mark_stock_item_sold(self, item_id: int) -> None:
        """Mark stock item as sold"""
        await self.stock_repo.mark_as_sold(item_id)
        
        # Get lot_id and update counts
        item = await self.stock_repo.get_by_id(item_id)
        if item:
            await self.lot_repo.update_stock_counts(item.lot_id)
            
            # Check if lot is now out of stock
            lot = await self.lot_repo.get_by_id(item.lot_id)
            if lot and lot.stock_count == 0 and lot.delivery_type == LotDeliveryType.AUTO:
                lot.status = LotStatus.OUT_OF_STOCK
        
        await self.session.flush()

    async def get_lots_by_product(
        self,
        product_id: int,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "price"
    ) -> list[Lot]:
        """Get all active lots for a product"""
        return await self.lot_repo.get_active_lots_by_product(
            product_id=product_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by
        )

    async def get_seller_lots(
        self,
        seller_id: int,
        include_deleted: bool = False
    ) -> list[Lot]:
        """Get all lots for a seller"""
        return await self.lot_repo.get_seller_lots(
            seller_id=seller_id,
            include_deleted=include_deleted
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
        """Search lots with filters"""
        return await self.lot_repo.search_lots(
            query=query,
            game_id=game_id,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            delivery_type=delivery_type,
            limit=limit,
            offset=offset
        )

    async def get_lot_with_details(self, lot_id: int) -> Lot | None:
        """Get lot with all relations"""
        return await self.lot_repo.get_by_id_with_relations(lot_id)

    async def cleanup_expired_reservations(self) -> int:
        """Release expired reservations"""
        from sqlalchemy import select, update
        
        now = datetime.utcnow()
        
        # Find expired reservations
        stmt = select(LotStockItem).where(
            LotStockItem.is_reserved == True,
            LotStockItem.reserved_until < now
        )
        result = await self.session.execute(stmt)
        expired_items = result.scalars().all()
        
        # Release them
        for item in expired_items:
            await self.stock_repo.release_reservation(item.id)
            await self.lot_repo.update_stock_counts(item.lot_id)
        
        await self.session.flush()
        return len(expired_items)
