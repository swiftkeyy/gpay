from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Seller, User, SellerReview
from app.models.enums import SellerStatus, ReviewStatus
from app.repositories.base import BaseRepository


class SellerRepository(BaseRepository[Seller]):
    def __init__(self, session: AsyncSession):
        super().__init__(Seller, session)

    async def get_by_user_id(self, user_id: int) -> Seller | None:
        stmt = select(Seller).where(Seller.user_id == user_id).options(selectinload(Seller.user))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_sellers(self, limit: int = 50, offset: int = 0) -> list[Seller]:
        stmt = (
            select(Seller)
            .where(Seller.status == SellerStatus.ACTIVE)
            .order_by(Seller.rating.desc(), Seller.total_sales.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_rating(self, seller_id: int) -> None:
        """Recalculate seller rating based on reviews"""
        stmt = (
            select(
                func.avg(SellerReview.rating).label("avg_rating"),
                func.count(SellerReview.id).label("total_reviews")
            )
            .where(
                SellerReview.seller_id == seller_id,
                SellerReview.status == ReviewStatus.PUBLISHED
            )
        )
        result = await self.session.execute(stmt)
        row = result.one()
        
        avg_rating = row.avg_rating or Decimal("0.00")
        total_reviews = row.total_reviews or 0
        
        await self.session.execute(
            update(Seller)
            .where(Seller.id == seller_id)
            .values(rating=avg_rating, total_reviews=total_reviews)
        )

    async def update_balance(self, seller_id: int, amount: Decimal) -> None:
        """Update seller balance"""
        stmt = (
            update(Seller)
            .where(Seller.id == seller_id)
            .values(balance=Seller.balance + amount)
        )
        await self.session.execute(stmt)

    async def increment_sales(self, seller_id: int) -> None:
        """Increment total sales counter"""
        stmt = (
            update(Seller)
            .where(Seller.id == seller_id)
            .values(total_sales=Seller.total_sales + 1)
        )
        await self.session.execute(stmt)

    async def search_sellers(
        self,
        query: str | None = None,
        min_rating: Decimal | None = None,
        verified_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> list[Seller]:
        stmt = select(Seller).where(Seller.status == SellerStatus.ACTIVE)
        
        if query:
            stmt = stmt.where(Seller.shop_name.ilike(f"%{query}%"))
        
        if min_rating:
            stmt = stmt.where(Seller.rating >= min_rating)
        
        if verified_only:
            stmt = stmt.where(Seller.is_verified == True)
        
        stmt = stmt.order_by(Seller.rating.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
