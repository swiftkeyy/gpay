"""Orders and deals router with idempotency."""
from __future__ import annotations

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
    User, Seller, Transaction, OrderStatusHistory
)
from app.models.enums import (
    OrderStatus, DealStatus, LotDeliveryType, LotStockStatus,
    TransactionType, TransactionStatus
)

router = APIRouter()


# Request/Response Models
class CreateOrderRequest(BaseModel):
    idempotency_key: str
    promo_code: str | None = None


class OrderItemResponse(BaseModel):
    id: int
    lot_id: int
    lot_title: str
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
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Create order from cart with idempotency."""
    # Check for existing order with same idempotency key
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
        # Return existing order (idempotency)
        return await _get_order_response(existing_order.id, session)
    
    # Get user cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Get cart items with lots
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.lot))
        .where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Validate all items
    for item in cart_items:
        lot = item.lot
        
        if lot.status != "active" or lot.is_deleted:
            raise HTTPException(
                status_code=400,
                detail=f"Lot '{lot.title}' is no longer available"
            )
        
        available_stock = lot.stock_count - lot.reserved_count + item.quantity
        if available_stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{lot.title}'"
            )
    
    # Calculate total
    total_amount = sum(item.lot.price * item.quantity for item in cart_items)
    
    # TODO: Apply promo code discount if provided
    
    # Create order
    order = Order(
        user_id=user_id,
        status=OrderStatus.PENDING,
        total_amount=total_amount,
        idempotency_key=request.idempotency_key,
        promo_code_id=None  # TODO: Link promo code if provided
    )
    session.add(order)
    await session.flush()
    
    # Create order items and deals
    for item in cart_items:
        lot = item.lot
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            lot_id=lot.id,
            quantity=item.quantity,
            price_per_item=lot.price,
            seller_id=lot.seller_id
        )
        session.add(order_item)
        await session.flush()
        
        # Create deal for this seller
        deal_amount = lot.price * item.quantity
        
        # Get seller to calculate commission
        result = await session.execute(
            select(Seller).where(Seller.id == lot.seller_id)
        )
        seller = result.scalar_one_or_none()
        commission_percent = seller.commission_percent if seller else Decimal("10.00")
        commission_amount = deal_amount * (commission_percent / Decimal("100"))
        seller_amount = deal_amount - commission_amount
        
        deal = Deal(
            order_id=order.id,
            buyer_id=user_id,
            seller_id=lot.seller_id,
            lot_id=lot.id,
            status=DealStatus.CREATED,
            amount=deal_amount,
            commission_amount=commission_amount,
            seller_amount=seller_amount,
            escrow_released=False,
            auto_complete_at=datetime.utcnow() + timedelta(hours=72)
        )
        session.add(deal)
    
    # Create status history
    status_history = OrderStatusHistory(
        order_id=order.id,
        status=OrderStatus.PENDING,
        comment="Order created"
    )
    session.add(status_history)
    
    # Clear cart (but keep reservations until payment)
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
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Initiate payment for order."""
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
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pay for order with status: {order.status.value}"
        )
    
    # Import payment providers
    from api.services.payment_providers import get_payment_provider
    import os
    
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
        }
    }
    
    if payment_method not in provider_configs:
        raise HTTPException(status_code=400, detail=f"Unknown payment method: {payment_method}")
    
    config = provider_configs[payment_method]
    if not all(config.values()):
        raise HTTPException(status_code=400, detail=f"Payment method {payment_method} is not configured")
    
    # Create payment
    try:
        provider = get_payment_provider(payment_method, **config)
        result = await provider.create_payment(
            order_id=order_id,
            amount=order.total_amount,
            currency="RUB",
            description=f"Order #{order_id}",
            return_url=f"https://your-miniapp.com/orders/{order_id}"
        )
        
        return {
            "payment_url": result.payment_url,
            "payment_id": result.payment_id,
            "order_id": order_id,
            "amount": float(order.total_amount),
            "currency": "RUB",
            "payment_method": payment_method
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")


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
    
    # Get order items with lots and sellers
    result = await session.execute(
        select(OrderItem)
        .options(
            selectinload(OrderItem.lot),
            selectinload(OrderItem.seller).selectinload(Seller.user)
        )
        .where(OrderItem.order_id == order_id)
    )
    order_items = result.scalars().all()
    
    items_response = []
    for item in order_items:
        lot = item.lot
        seller_user = item.seller.user if item.seller else None
        
        items_response.append(OrderItemResponse(
            id=item.id,
            lot_id=lot.id,
            lot_title=lot.title,
            quantity=item.quantity,
            price_per_item=item.price_per_item,
            subtotal=item.price_per_item * item.quantity,
            seller_id=item.seller_id,
            seller_name=seller_user.username if seller_user else "Unknown"
        ))
    
    return OrderResponse(
        id=order.id,
        status=order.status.value,
        total_amount=order.total_amount,
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at
    )
