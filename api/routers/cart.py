"""Shopping cart router with stock reservation."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.entities import Cart, CartItem, Lot, LotStockItem, User, Product, Game, Category
from app.models.enums import LotStatus, LotStockStatus

router = APIRouter()


# Request/Response Models
class AddToCartRequest(BaseModel):
    lot_id: int
    quantity: int = 1


class UpdateCartItemRequest(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    lot_id: int
    lot_title: str
    lot_price: Decimal
    lot_image_url: str | None
    quantity: int
    subtotal: Decimal
    seller_id: int
    seller_name: str
    delivery_type: str
    stock_available: int


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    subtotal: Decimal
    total: Decimal
    items_count: int


class ValidationError(BaseModel):
    item_id: int
    lot_id: int
    error: str


class CartValidationResponse(BaseModel):
    valid: bool
    errors: List[ValidationError]


@router.get("", response_model=CartResponse)
async def get_cart(
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Get user cart with all items."""
    # Get or create cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        cart = Cart(user_id=user_id)
        session.add(cart)
        await session.commit()
        await session.refresh(cart)
    
    # Get cart items with lot details
    result = await session.execute(
        select(CartItem)
        .options(
            selectinload(CartItem.lot).selectinload(Lot.product).selectinload(Product.category).selectinload(Category.game),
            selectinload(CartItem.lot).selectinload(Lot.seller).selectinload(User)
        )
        .where(CartItem.cart_id == cart.id)
        .order_by(CartItem.created_at.desc())
    )
    cart_items = result.scalars().all()
    
    items_response = []
    subtotal = Decimal("0.00")
    
    for item in cart_items:
        lot = item.lot
        seller = lot.seller_user if hasattr(lot, 'seller_user') else None
        
        item_subtotal = lot.price * item.quantity
        subtotal += item_subtotal
        
        items_response.append(CartItemResponse(
            id=item.id,
            lot_id=lot.id,
            lot_title=lot.title,
            lot_price=lot.price,
            lot_image_url=None,  # TODO: Get from lot_images
            quantity=item.quantity,
            subtotal=item_subtotal,
            seller_id=lot.seller_id,
            seller_name=seller.username if seller else "Unknown",
            delivery_type=lot.delivery_type.value,
            stock_available=lot.stock_count - lot.reserved_count
        ))
    
    return CartResponse(
        items=items_response,
        subtotal=subtotal,
        total=subtotal,  # TODO: Apply promo code discount
        items_count=len(items_response)
    )


@router.post("/items")
async def add_to_cart(
    request: AddToCartRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Add item to cart with stock reservation."""
    # Validate lot exists and is active
    result = await session.execute(
        select(Lot).where(
            and_(
                Lot.id == request.lot_id,
                Lot.status == LotStatus.ACTIVE,
                Lot.is_deleted == False
            )
        )
    )
    lot = result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found or inactive")
    
    # Check stock availability
    available_stock = lot.stock_count - lot.reserved_count
    if available_stock < request.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {available_stock}"
        )
    
    # Get or create cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        cart = Cart(user_id=user_id)
        session.add(cart)
        await session.flush()
    
    # Check if item already in cart
    result = await session.execute(
        select(CartItem).where(
            and_(
                CartItem.cart_id == cart.id,
                CartItem.lot_id == request.lot_id
            )
        )
    )
    existing_item = result.scalar_one_or_none()
    
    if existing_item:
        # Update quantity and reservation
        new_quantity = existing_item.quantity + request.quantity
        
        # Check if new quantity exceeds available stock
        if available_stock < (new_quantity - existing_item.quantity):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for requested quantity"
            )
        
        existing_item.quantity = new_quantity
        existing_item.updated_at = datetime.utcnow()
        
        # Update stock reservation
        lot.reserved_count += request.quantity
    else:
        # Create new cart item
        cart_item = CartItem(
            cart_id=cart.id,
            lot_id=request.lot_id,
            quantity=request.quantity
        )
        session.add(cart_item)
        
        # Reserve stock
        lot.reserved_count += request.quantity
    
    await session.commit()
    
    return {"message": "Added to cart", "lot_id": request.lot_id, "quantity": request.quantity}


@router.patch("/items/{item_id}")
async def update_cart_item(
    item_id: int,
    request: UpdateCartItemRequest,
    session: AsyncSession = Depends(get_session)
):
    """Update cart item quantity with stock adjustment."""
    if request.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    
    # Get cart item with lot
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.lot))
        .where(CartItem.id == item_id)
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    lot = cart_item.lot
    old_quantity = cart_item.quantity
    quantity_diff = request.quantity - old_quantity
    
    # Check stock availability if increasing quantity
    if quantity_diff > 0:
        available_stock = lot.stock_count - lot.reserved_count
        if available_stock < quantity_diff:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {available_stock}"
            )
    
    # Update cart item
    cart_item.quantity = request.quantity
    cart_item.updated_at = datetime.utcnow()
    
    # Adjust stock reservation
    lot.reserved_count += quantity_diff
    
    await session.commit()
    
    return {"message": "Cart item updated", "item_id": item_id, "new_quantity": request.quantity}


@router.delete("/items/{item_id}")
async def remove_from_cart(
    item_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Remove item from cart and release reserved stock."""
    # Get cart item with lot
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.lot))
        .where(CartItem.id == item_id)
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    lot = cart_item.lot
    
    # Release reserved stock
    lot.reserved_count -= cart_item.quantity
    
    # Delete cart item
    await session.delete(cart_item)
    await session.commit()
    
    return {"message": "Item removed from cart", "item_id": item_id}


@router.delete("")
async def clear_cart(
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Clear all items from cart and release all reserved stock."""
    # Get cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        return {"message": "Cart is already empty"}
    
    # Get all cart items with lots
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.lot))
        .where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    # Release all reserved stock
    for item in cart_items:
        item.lot.reserved_count -= item.quantity
        await session.delete(item)
    
    await session.commit()
    
    return {"message": "Cart cleared", "items_removed": len(cart_items)}


@router.post("/validate", response_model=CartValidationResponse)
async def validate_cart(
    user_id: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """Validate cart before checkout - check stock and prices."""
    # Get cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        return CartValidationResponse(valid=True, errors=[])
    
    # Get all cart items with lots
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.lot))
        .where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    errors = []
    
    for item in cart_items:
        lot = item.lot
        
        # Check if lot is still active
        if lot.status != LotStatus.ACTIVE or lot.is_deleted:
            errors.append(ValidationError(
                item_id=item.id,
                lot_id=lot.id,
                error="Lot is no longer available"
            ))
            continue
        
        # Check stock availability
        available_stock = lot.stock_count - lot.reserved_count + item.quantity  # Add back current reservation
        if available_stock < item.quantity:
            errors.append(ValidationError(
                item_id=item.id,
                lot_id=lot.id,
                error=f"Insufficient stock. Available: {available_stock}, requested: {item.quantity}"
            ))
    
    return CartValidationResponse(
        valid=len(errors) == 0,
        errors=errors
    )
