from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Seller, User
from app.models.enums import SellerStatus, TransactionType
from app.repositories.sellers import SellerRepository
from app.repositories.transactions import TransactionRepository


class SellerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.seller_repo = SellerRepository(session)
        self.transaction_repo = TransactionRepository(session)

    async def create_seller(
        self,
        user_id: int,
        shop_name: str,
        description: str | None = None
    ) -> Seller:
        """Create new seller profile"""
        seller = Seller(
            user_id=user_id,
            shop_name=shop_name,
            description=description,
            status=SellerStatus.PENDING
        )
        self.session.add(seller)
        await self.session.flush()
        return seller

    async def get_seller_by_user_id(self, user_id: int) -> Seller | None:
        return await self.seller_repo.get_by_user_id(user_id)

    async def activate_seller(self, seller_id: int) -> None:
        """Activate seller after verification"""
        seller = await self.seller_repo.get_by_id(seller_id)
        if seller:
            seller.status = SellerStatus.ACTIVE
            await self.session.flush()

    async def verify_seller(self, seller_id: int) -> None:
        """Mark seller as verified"""
        seller = await self.seller_repo.get_by_id(seller_id)
        if seller:
            seller.is_verified = True
            seller.verified_at = datetime.utcnow()
            await self.session.flush()

    async def suspend_seller(self, seller_id: int, reason: str | None = None) -> None:
        """Suspend seller account"""
        seller = await self.seller_repo.get_by_id(seller_id)
        if seller:
            seller.status = SellerStatus.SUSPENDED
            await self.session.flush()

    async def add_funds(
        self,
        seller_id: int,
        amount: Decimal,
        description: str
    ) -> None:
        """Add funds to seller balance"""
        seller = await self.seller_repo.get_by_id(seller_id)
        if not seller:
            raise ValueError("Seller not found")
        
        # Update seller balance
        await self.seller_repo.update_balance(seller_id, amount)
        
        # Create transaction
        await self.transaction_repo.create_transaction(
            user_id=seller.user_id,
            transaction_type=TransactionType.SALE,
            amount=amount,
            description=description,
            reference_type="seller",
            reference_id=seller_id
        )
        
        await self.session.flush()

    async def deduct_funds(
        self,
        seller_id: int,
        amount: Decimal,
        description: str
    ) -> None:
        """Deduct funds from seller balance"""
        seller = await self.seller_repo.get_by_id(seller_id)
        if not seller:
            raise ValueError("Seller not found")
        
        if seller.balance < amount:
            raise ValueError("Insufficient balance")
        
        # Update seller balance
        await self.seller_repo.update_balance(seller_id, -amount)
        
        # Create transaction
        await self.transaction_repo.create_transaction(
            user_id=seller.user_id,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=amount,
            description=description,
            reference_type="seller",
            reference_id=seller_id
        )
        
        await self.session.flush()

    async def calculate_commission(
        self,
        seller_id: int,
        amount: Decimal
    ) -> Decimal:
        """Calculate commission for seller"""
        seller = await self.seller_repo.get_by_id(seller_id)
        if not seller:
            return Decimal("0.00")
        
        commission = (amount * seller.commission_percent) / Decimal("100")
        return commission.quantize(Decimal("0.01"))

    async def update_rating(self, seller_id: int) -> None:
        """Recalculate seller rating"""
        await self.seller_repo.update_rating(seller_id)
        await self.session.flush()

    async def increment_sales(self, seller_id: int) -> None:
        """Increment total sales counter"""
        await self.seller_repo.increment_sales(seller_id)
        await self.session.flush()

    async def search_sellers(
        self,
        query: str | None = None,
        min_rating: Decimal | None = None,
        verified_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> list[Seller]:
        return await self.seller_repo.search_sellers(
            query=query,
            min_rating=min_rating,
            verified_only=verified_only,
            limit=limit,
            offset=offset
        )

    async def get_seller_stats(self, seller_id: int) -> dict:
        """Get seller statistics"""
        from datetime import timedelta
        
        seller = await self.seller_repo.get_by_id(seller_id)
        if not seller:
            return {}
        
        # Get sales for last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        monthly_sales = await self.transaction_repo.get_total_by_type(
            user_id=seller.user_id,
            transaction_type=TransactionType.SALE,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "total_sales": seller.total_sales,
            "rating": float(seller.rating),
            "total_reviews": seller.total_reviews,
            "balance": float(seller.balance),
            "monthly_sales": float(monthly_sales),
            "is_verified": seller.is_verified,
            "status": seller.status.value
        }
