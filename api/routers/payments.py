"""Payment processing and webhook handlers."""
from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.entities import Order, Deal, Transaction, User, Seller, LotStockItem
from app.models.enums import (
    OrderStatus, DealStatus, TransactionType, TransactionStatus,
    LotDeliveryType, LotStockStatus
)
from api.services.payment_providers import get_payment_provider, WebhookResult

router = APIRouter()


# Request/Response Models
class PaymentMethodResponse(BaseModel):
    id: str
    name: str
    icon: str
    enabled: bool


@router.get("/payment-methods")
async def get_payment_methods():
    """Get available payment methods."""
    methods = [
        PaymentMethodResponse(
            id="yookassa",
            name="ЮKassa (Карты, СБП, Кошельки)",
            icon="💳",
            enabled=bool(os.getenv("YUKASSA_SHOP_ID"))
        ),
        PaymentMethodResponse(
            id="tinkoff",
            name="Tinkoff (Карты, Рассрочка)",
            icon="🏦",
            enabled=bool(os.getenv("TINKOFF_TERMINAL_KEY"))
        ),
        PaymentMethodResponse(
            id="cloudpayments",
            name="CloudPayments (Карты, Apple Pay, Google Pay)",
            icon="☁️",
            enabled=bool(os.getenv("CLOUDPAYMENTS_PUBLIC_ID"))
        ),
        PaymentMethodResponse(
            id="cryptobot",
            name="Crypto Bot (TON, USDT, BTC, ETH)",
            icon="₿",
            enabled=bool(os.getenv("CRYPTOBOT_TOKEN"))
        )
    ]
    
    return [m for m in methods if m.enabled]


@router.post("/webhooks/yookassa")
async def yookassa_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Handle ЮKassa webhook."""
    payload = await request.json()
    
    # Get provider
    provider = get_payment_provider(
        "yookassa",
        shop_id=os.getenv("YUKASSA_SHOP_ID"),
        secret_key=os.getenv("YUKASSA_SECRET_KEY")
    )
    
    # Process webhook
    result = await provider.process_webhook(payload)
    
    if result:
        await _process_payment_result(result, session)
    
    return {"status": "ok"}


@router.post("/webhooks/tinkoff")
async def tinkoff_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Handle Tinkoff webhook."""
    payload = await request.json()
    
    # Get provider
    provider = get_payment_provider(
        "tinkoff",
        terminal_key=os.getenv("TINKOFF_TERMINAL_KEY"),
        secret_key=os.getenv("TINKOFF_SECRET_KEY")
    )
    
    # Verify signature
    if not await provider.verify_webhook(payload, payload.get("Token", "")):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Process webhook
    result = await provider.process_webhook(payload)
    
    if result:
        await _process_payment_result(result, session)
    
    return {"status": "ok"}


@router.post("/webhooks/cloudpayments")
async def cloudpayments_webhook(
    request: Request,
    x_content_hmac: str = Header(None),
    session: AsyncSession = Depends(get_session)
):
    """Handle CloudPayments webhook."""
    payload = await request.json()
    
    # Get provider
    provider = get_payment_provider(
        "cloudpayments",
        public_id=os.getenv("CLOUDPAYMENTS_PUBLIC_ID"),
        api_secret=os.getenv("CLOUDPAYMENTS_API_SECRET")
    )
    
    # Verify signature
    if not await provider.verify_webhook(payload, x_content_hmac or ""):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Process webhook
    result = await provider.process_webhook(payload)
    
    if result:
        await _process_payment_result(result, session)
    
    return {"code": 0}


@router.post("/webhooks/cryptobot")
async def cryptobot_webhook(
    request: Request,
    crypto_pay_api_signature: str = Header(None),
    session: AsyncSession = Depends(get_session)
):
    """Handle Crypto Bot webhook."""
    payload = await request.json()
    
    # Get provider
    provider = get_payment_provider(
        "cryptobot",
        token=os.getenv("CRYPTOBOT_TOKEN")
    )
    
    # Verify signature
    if not await provider.verify_webhook(payload, crypto_pay_api_signature or ""):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Process webhook
    result = await provider.process_webhook(payload)
    
    if result:
        await _process_payment_result(result, session)
    
    return {"status": "ok"}


async def _process_payment_result(
    result: WebhookResult,
    session: AsyncSession
):
    """Process payment result and update order/deals."""
    if result.status != "success":
        # Payment failed or pending
        return
    
    # Get order
    query = select(Order).where(Order.id == result.order_id)
    order_result = await session.execute(query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        return
    
    if order.status != OrderStatus.PENDING:
        # Already processed
        return
    
    # Update order status
    order.status = OrderStatus.PAID
    order.updated_at = datetime.utcnow()
    
    # Get all deals for this order
    deals_result = await session.execute(
        select(Deal)
        .options(selectinload(Deal.lot))
        .where(Deal.order_id == order.id)
    )
    deals = deals_result.scalars().all()
    
    # Process each deal
    for deal in deals:
        lot = deal.lot
        
        # Update deal status
        deal.status = DealStatus.PAID
        deal.updated_at = datetime.utcnow()
        
        # Transfer funds to escrow (just mark as held)
        # Funds will be released when delivery is confirmed
        
        # Handle auto-delivery
        if lot.delivery_type == LotDeliveryType.AUTO:
            # Get stock items
            stock_result = await session.execute(
                select(LotStockItem)
                .where(
                    and_(
                        LotStockItem.lot_id == lot.id,
                        LotStockItem.status == LotStockStatus.AVAILABLE
                    )
                )
                .limit(1)  # TODO: Get quantity from deal
            )
            stock_items = stock_result.scalars().all()
            
            if stock_items:
                # Mark stock as sold
                delivery_data = []
                for item in stock_items:
                    item.status = LotStockStatus.SOLD
                    item.deal_id = deal.id
                    delivery_data.append(item.data)
                
                # Update lot counts
                lot.sold_count += len(stock_items)
                lot.reserved_count -= len(stock_items)
                
                # Auto-complete deal
                deal.status = DealStatus.COMPLETED
                deal.completed_at = datetime.utcnow()
                deal.buyer_confirmed = True
                deal.buyer_confirmed_at = datetime.utcnow()
                
                # Release escrow to seller
                await _release_escrow(deal, session)
                
                # TODO: Send delivery data to buyer via bot
        else:
            # Manual delivery - notify seller
            deal.status = DealStatus.IN_PROGRESS
            # TODO: Send notification to seller
    
    await session.commit()


async def _release_escrow(deal: Deal, session: AsyncSession):
    """Release escrow funds to seller."""
    if deal.escrow_released:
        return
    
    # Get seller
    seller_result = await session.execute(
        select(Seller).where(Seller.id == deal.seller_id)
    )
    seller = seller_result.scalar_one_or_none()
    
    if not seller:
        return
    
    # Get seller user
    user_result = await session.execute(
        select(User).where(User.id == seller.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        return
    
    # Add funds to seller balance
    old_balance = user.balance
    user.balance += deal.seller_amount
    
    # Create transaction for seller
    seller_transaction = Transaction(
        user_id=user.id,
        transaction_type=TransactionType.SALE,
        amount=deal.seller_amount,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=old_balance,
        balance_after=user.balance,
        description=f"Payment for deal #{deal.id}",
        reference_type="deal",
        reference_id=deal.id
    )
    session.add(seller_transaction)
    
    # Create transaction for commission
    commission_transaction = Transaction(
        user_id=user.id,
        transaction_type=TransactionType.COMMISSION,
        amount=-deal.commission_amount,
        currency_code="RUB",
        status=TransactionStatus.COMPLETED,
        balance_before=user.balance,
        balance_after=user.balance,  # Already deducted from seller_amount
        description=f"Commission for deal #{deal.id}",
        reference_type="deal",
        reference_id=deal.id
    )
    session.add(commission_transaction)
    
    # Mark escrow as released
    deal.escrow_released = True
    deal.escrow_released_at = datetime.utcnow()
    
    await session.flush()
