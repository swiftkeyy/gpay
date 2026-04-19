"""Orders and deals router with idempotency."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.entities import (
    Cart, CartItem, Order, OrderItem, Deal, Lot, LotStockItem,
    User, Seller, Transaction, OrderStatusHistory, Product, Game, Price, PromoCode, PromoCodeUsage, Payment
)
from app.models.enums import (
    OrderStatus, DealStatus, LotDeliveryType, LotStockStatus,
    TransactionType, TransactionStatus, FulfillmentType, PromoType
)
from api.dependencies.auth import get_current_user
from api.services.payment_providers import get_payment_provider

router = APIRouter()

# Real game images mapping (same as catalog.py)
GAME_IMAGES = {
    "brawl-stars": "https://i.imgur.com/8QZqZ5L.png",
    "roblox": "https://i.imgur.com/xVpIvMZ.png",
    "genshin-impact": "https://i.imgur.com/yH8UqLJ.png",
    "cs2": "https://i.imgur.com/9fRaldg.png",
    "minecraft": "https://i.imgur.com/5MzQwYc.png",
    "standoff-2": "https://i.imgur.com/kF3jYvN.png",
    "fortnite": "https://i.imgur.com/TQcGHrA.png",
    "valorant": "https://i.imgur.com/X3FqJqZ.png",
    "pubg": "https://i.imgur.com/nRGzYvL.png",
    "mobile-legends": "https://i.imgur.com/8pLqZ5M.png",
}


# Request/Response Models
class CreateOrderRequest(BaseModel):
    idempotency_key: str
    promo_code: str | None = None


class OrderItemResponse(BaseModel):
    id: int
    lot_id: int
    lot_title: str
    lot_image_url: str
    quantity: int
    price_per_item: Decimal
    subtotal: Decimal
    seller_id: int
    seller_name: str


class OrderResponse(BaseModel):
    id: int
    status: str
    total_amount: Decimal
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderListItem(BaseModel):
    id: int
    status: str
    total_amount: Decimal
    items_count: int
    created_at: datetime


class OrderListResponse(BaseModel):
    items: List[OrderListItem]
    total: int
    page: int
    limit: int


@router.post("", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Create order from cart with idempotency.
    
    Validates: Requirements 7.1, 7.2, 7.8
    - 7.1: Create order record with all cart items and calculate total amount
    - 7.2: Create separate deals for each seller involved (future P2P feature)
    - 7.8: Use idempotency keys to prevent duplicate order creation
    """
    user_id = current_user.id
    
    # Check for existing order with same idempotency key (Requirement 7.8)
    result = await session.execute(
        select(Order).where(
            and_(
                Order.user_id == user_id,
                Order.idempotency_key == request.idempotency_key
            )
        )
    )
    existing_order = result.scalar_one_or_none()
    
    if existing_order:
        # Return existing order (idempotency - prevents duplicate orders)
        return await _get_order_response(existing_order.id, session)
    
    # Get user cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Get cart items with products
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Validate all items and calculate subtotal
    subtotal_amount = Decimal("0.00")
    items_data = []
    
    for item in cart_items:
        product = item.product
        
        # Validate product is active
        if not product.is_active or product.is_deleted:
            raise HTTPException(
                status_code=400,
                detail=f"Product '{product.title}' is no longer available"
            )
        
        # Get current active price
        price_result = await session.execute(
            select(Price).where(
                Price.product_id == product.id,
                Price.is_active == True
            ).limit(1)
        )
        price = price_result.scalar_one_or_none()
        
        if not price:
            raise HTTPException(
                status_code=400,
                detail=f"Price not found for product '{product.title}'"
            )
        
        # Calculate item total
        item_total = price.base_price * item.quantity
        subtotal_amount += item_total
        
        items_data.append({
            "cart_item": item,
            "product": product,
            "price": price,
            "unit_price": price.base_price,
            "total_price": item_total
        })
    
    # Apply promo code discount if provided (Requirement 7.2)
    discount_amount = Decimal("0.00")
    promo_code_id = None
    
    if request.promo_code:
        # Find and validate promo code
        result = await session.execute(
            select(PromoCode).where(
                and_(
                    PromoCode.code == request.promo_code.upper(),
                    PromoCode.is_deleted == False,
                    PromoCode.is_active == True
                )
            )
        )
        promo_code = result.scalar_one_or_none()
        
        if promo_code:
            # Check expiration dates
            now = datetime.utcnow()
            if promo_code.starts_at and promo_code.starts_at > now:
                raise HTTPException(status_code=400, detail="Promo code is not yet valid")
            
            if promo_code.ends_at and promo_code.ends_at < now:
                raise HTTPException(status_code=400, detail="Promo code has expired")
            
            # Check usage limit
            if promo_code.max_usages is not None and promo_code.used_count >= promo_code.max_usages:
                raise HTTPException(status_code=400, detail="Promo code usage limit reached")
            
            # Check if user already used this promo code
            result = await session.execute(
                select(PromoCodeUsage).where(
                    and_(
                        PromoCodeUsage.promo_code_id == promo_code.id,
                        PromoCodeUsage.user_id == user_id
                    )
                )
            )
            existing_usage = result.scalar_one_or_none()
            
            if existing_usage:
                raise HTTPException(status_code=400, detail="You have already used this promo code")
            
            # Check if only for new users
            if promo_code.only_new_users:
                result = await session.execute(
                    select(Order).where(
                        and_(
                            Order.user_id == user_id,
                            Order.status.in_([OrderStatus.COMPLETED, OrderStatus.DELIVERED])
                        )
                    ).limit(1)
                )
                has_orders = result.scalar_one_or_none()
                
                if has_orders:
                    raise HTTPException(status_code=400, detail="This promo code is only for new users")
            
            # Calculate discount based on promo type
            if promo_code.promo_type == PromoType.PERCENT:
                discount_amount = (subtotal_amount * promo_code.value) / Decimal("100")
            elif promo_code.promo_type == PromoType.FIXED:
                discount_amount = promo_code.value
            
            # Ensure discount doesn't exceed subtotal
            if discount_amount > subtotal_amount:
                discount_amount = subtotal_amount
            
            promo_code_id = promo_code.id
    
    # Calculate total amount
    total_amount = subtotal_amount - discount_amount
    
    # Ensure total is never negative
    if total_amount < Decimal("0.00"):
        total_amount = Decimal("0.00")
    
    # Generate unique order number
    order_number = f"GP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
    
    # Create order (Requirement 7.1)
    order = Order(
        order_number=order_number,
        user_id=user_id,
        status=OrderStatus.NEW,
        subtotal_amount=subtotal_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        promo_code_id=promo_code_id,
        idempotency_key=request.idempotency_key
    )
    session.add(order)
    await session.flush()
    
    # Create order items with product snapshots
    for item_data in items_data:
        product = item_data["product"]
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            title_snapshot=product.title,
            quantity=item_data["cart_item"].quantity,
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"],
            fulfillment_type=product.fulfillment_type
        )
        session.add(order_item)
    
    # Create status history for audit trail
    status_history = OrderStatusHistory(
        order_id=order.id,
        old_status=None,
        new_status=OrderStatus.NEW,
        comment="Order created from cart"
    )
    session.add(status_history)
    
    # Record promo code usage if applied
    if promo_code_id:
        promo_usage = PromoCodeUsage(
            promo_code_id=promo_code_id,
            user_id=user_id,
            order_id=order.id
        )
        session.add(promo_usage)
        
        # Increment promo code usage count
        await session.execute(
            select(PromoCode).where(PromoCode.id == promo_code_id)
        )
        promo_code_obj = (await session.execute(
            select(PromoCode).where(PromoCode.id == promo_code_id)
        )).scalar_one()
        promo_code_obj.used_count += 1
    
    # Clear cart after successful order creation
    for item in cart_items:
        await session.delete(item)
    
    await session.commit()
    
    return await _get_order_response(order.id, session)


@router.get("", response_model=OrderListResponse)
async def get_orders(
    user_id: int = 1,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session)
):
    """Get user orders with pagination."""
    if limit > 100:
        limit = 100
    
    offset = (page - 1) * limit
    
    # Build query
    query = select(Order).where(Order.user_id == user_id)
    
    if status:
        try:
            status_enum = OrderStatus(status)
            query = query.where(Order.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    
    # Get orders
    result = await session.execute(query)
    orders = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(Order.id)).where(Order.user_id == user_id)
    if status:
        count_query = count_query.where(Order.status == status_enum)
    
    result = await session.execute(count_query)
    total = result.scalar()
    
    # Build response
    items = []
    for order in orders:
        # Get items count
        result = await session.execute(
            select(func.count(OrderItem.id)).where(OrderItem.order_id == order.id)
        )
        items_count = result.scalar()
        
        items.append(OrderListItem(
            id=order.id,
            status=order.status.value,
            total_amount=order.total_amount,
            items_count=items_count,
            created_at=order.created_at
        ))
    
    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Get order details."""
    return await _get_order_response(order_id, session, user_id)


@router.post("/{order_id}/payment")
async def initiate_payment(
    order_id: int,
    payment_method: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Initiate payment for order.
    
    Validates: Requirements 7.3, 7.4, 23.1, 23.2
    - 7.3: Support payment methods including Telegram Stars, ЮKassa, Tinkoff, CloudPayments, and Crypto Bot
    - 7.4: Create payment record and return payment URL or invoice
    - 23.1: Return list of enabled providers with names and icons
    - 23.2: Generate payment URL and return it to Mini App
    """
    user_id = current_user.id
    
    # Get order
    result = await session.execute(
        select(Order).where(
            and_(
                Order.id == order_id,
                Order.user_id == user_id
            )
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check order status - must be NEW or WAITING_PAYMENT
    if order.status not in [OrderStatus.NEW, OrderStatus.WAITING_PAYMENT]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pay for order with status: {order.status.value}"
        )
    
    # Get provider config
    provider_configs = {
        "yookassa": {
            "shop_id": os.getenv("YUKASSA_SHOP_ID"),
            "secret_key": os.getenv("YUKASSA_SECRET_KEY")
        },
        "tinkoff": {
            "terminal_key": os.getenv("TINKOFF_TERMINAL_KEY"),
            "secret_key": os.getenv("TINKOFF_SECRET_KEY")
        },
        "cloudpayments": {
            "public_id": os.getenv("CLOUDPAYMENTS_PUBLIC_ID"),
            "api_secret": os.getenv("CLOUDPAYMENTS_API_SECRET")
        },
        "cryptobot": {
            "token": os.getenv("CRYPTOBOT_TOKEN")
        },
        "telegram_stars": {
            # Telegram Stars configuration (future implementation)
        }
    }
    
    if payment_method not in provider_configs:
        raise HTTPException(status_code=400, detail=f"Unknown payment method: {payment_method}")
    
    config = provider_configs[payment_method]
    
    # Check if provider is configured (skip for telegram_stars as it's future)
    if payment_method != "telegram_stars" and not all(config.values()):
        raise HTTPException(status_code=400, detail=f"Payment method {payment_method} is not configured")
    
    # Create payment record BEFORE calling provider
    payment = Payment(
        order_id=order_id,
        payment_provider=payment_method,
        amount=order.total_amount,
        currency=order.currency_code,
        status="pending"
    )
    session.add(payment)
    await session.flush()
    
    # Create payment with provider
    try:
        if payment_method == "telegram_stars":
            # Stub for Telegram Stars (future implementation)
            raise HTTPException(
                status_code=501,
                detail="Telegram Stars payment is not yet implemented"
            )
        
        provider = get_payment_provider(payment_method, **config)
        result = await provider.create_payment(
            order_id=order_id,
            amount=order.total_amount,
            currency=order.currency_code,
            description=f"Order #{order.order_number}",
            return_url=f"https://your-miniapp.com/orders/{order_id}"
        )
        
        # Update payment record with provider response
        payment.external_payment_id = result.payment_id
        payment.payment_url = result.payment_url
        
        # Update order status to WAITING_PAYMENT
        old_status = order.status
        order.status = OrderStatus.WAITING_PAYMENT
        order.updated_at = datetime.utcnow()
        
        # Create status history record
        status_history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=OrderStatus.WAITING_PAYMENT,
            comment=f"Payment initiated via {payment_method}"
        )
        session.add(status_history)
        
        await session.commit()
        
        return {
            "payment_id": payment.id,
            "payment_url": result.payment_url,
            "external_payment_id": result.payment_id,
            "order_id": order_id,
            "amount": float(order.total_amount),
            "currency": order.currency_code,
            "payment_method": payment_method,
            "status": "pending"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        await session.rollback()
        raise
    except Exception as e:
        # Handle payment provider errors
        await session.rollback()
        
        # Update payment record with error
        payment.status = "failed"
        payment.error_message = str(e)
        await session.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Payment creation failed: {str(e)}"
        )


async def _get_order_response(
    order_id: int,
    session: AsyncSession,
    user_id: int | None = None
) -> OrderResponse:
    """Helper to build order response."""
    # Get order
    query = select(Order).where(Order.id == order_id)
    if user_id:
        query = query.where(Order.user_id == user_id)
    
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get order items with products
    result = await session.execute(
        select(OrderItem)
        .options(selectinload(OrderItem.product))
        .where(OrderItem.order_id == order_id)
    )
    order_items = result.scalars().all()
    
    items_response = []
    for item in order_items:
        product = item.product
        
        # Get game info for image
        if product:
            game_result = await session.execute(
                select(Game).where(Game.id == product.game_id)
            )
            game = game_result.scalar_one_or_none()
            game_slug = game.slug if game else "default"
            image_url = GAME_IMAGES.get(game_slug, f"https://picsum.photos/seed/{game_slug}/400/400")
        else:
            image_url = f"https://picsum.photos/seed/product-{item.product_id}/400/400"
        
        items_response.append(OrderItemResponse(
            id=item.id,
            lot_id=item.product_id,  # Using product_id as lot_id for compatibility
            lot_title=item.title_snapshot,
            lot_image_url=image_url,
            quantity=item.quantity,
            price_per_item=item.unit_price,
            subtotal=item.total_price,
            seller_id=1,  # Default seller ID (Game Pay)
            seller_name="Game Pay"
        ))
    
    return OrderResponse(
        id=order.id,
        status=order.status.value,
        total_amount=order.total_amount,
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at
    )
