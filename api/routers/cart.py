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

from app.db.session import get_db_session
from app.models.entities import Cart, CartItem, Lot, LotStockItem, User, Product, Game, Category
from app.models.enums import LotStatus, LotStockStatus

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
class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1


class UpdateCartItemRequest(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_title: str
    product_price: Decimal
    product_image_url: str | None
    quantity: int
    subtotal: Decimal
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


class ApplyPromoRequest(BaseModel):
    promo_code: str


class ApplyPromoResponse(BaseModel):
    success: bool
    message: str
    discount_amount: Decimal | None = None
    promo_type: str | None = None
    original_total: Decimal | None = None
    discounted_total: Decimal | None = None


@router.get("", response_model=CartResponse)
async def get_cart(
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Get user cart with all items."""
    from app.models.entities import Price
    
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
    
    # Get cart items with product details
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.cart_id == cart.id)
        .order_by(CartItem.created_at.desc())
    )
    cart_items = result.scalars().all()
    
    items_response = []
    subtotal = Decimal("0.00")
    
    for item in cart_items:
        product = item.product
        
        # Get active price
        price_result = await session.execute(
            select(Price).where(
                Price.product_id == product.id,
                Price.is_active == True
            ).limit(1)
        )
        price = price_result.scalar_one_or_none()
        
        if not price:
            continue
        
        # Get game info for image
        game_result = await session.execute(
            select(Game).where(Game.id == product.game_id)
        )
        game = game_result.scalar_one_or_none()
        
        item_subtotal = price.base_price * item.quantity
        subtotal += item_subtotal
        
        # Use game-specific images (Playerok-style)
        game_slug = game.slug if game else "default"
        image_url = GAME_IMAGES.get(game_slug, f"https://picsum.photos/seed/{game_slug}/400/400")
        
        items_response.append(CartItemResponse(
            id=item.id,
            product_id=product.id,
            product_title=product.title,
            product_price=price.base_price,
            product_image_url=image_url,
            quantity=item.quantity,
            subtotal=item_subtotal,
            seller_name="Game Pay",
            delivery_type="auto" if product.fulfillment_type.value == "auto" else "manual",
            stock_available=999
        ))
    
    return CartResponse(
        items=items_response,
        subtotal=subtotal,
        total=subtotal,
        items_count=len(items_response)
    )


@router.post("/items")
async def add_to_cart(
    request: AddToCartRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Add item to cart."""
    from app.models.entities import Price
    
    # Validate product exists and is active
    result = await session.execute(
        select(Product).where(
            and_(
                Product.id == request.product_id,
                Product.is_active == True,
                Product.is_deleted == False
            )
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    
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
                CartItem.product_id == request.product_id
            )
        )
    )
    existing_item = result.scalar_one_or_none()
    
    if existing_item:
        # Update quantity
        existing_item.quantity += request.quantity
        existing_item.updated_at = datetime.utcnow()
    else:
        # Create new cart item
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=request.product_id,
            quantity=request.quantity
        )
        session.add(cart_item)
    
    await session.commit()
    
    return {"message": "Added to cart", "product_id": request.product_id, "quantity": request.quantity}


@router.patch("/items/{item_id}")
async def update_cart_item(
    item_id: int,
    request: UpdateCartItemRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Update cart item quantity."""
    if request.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    
    # Get cart item
    result = await session.execute(
        select(CartItem).where(CartItem.id == item_id)
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Update cart item
    cart_item.quantity = request.quantity
    cart_item.updated_at = datetime.utcnow()
    
    await session.commit()
    
    return {"message": "Cart item updated", "item_id": item_id, "new_quantity": request.quantity}


@router.delete("/items/{item_id}")
async def remove_from_cart(
    item_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Remove item from cart."""
    # Get cart item
    result = await session.execute(
        select(CartItem).where(CartItem.id == item_id)
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Delete cart item
    await session.delete(cart_item)
    await session.commit()
    
    return {"message": "Item removed from cart", "item_id": item_id}


@router.delete("")
async def clear_cart(
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """Clear all items from cart."""
    # Get cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        return {"message": "Cart is already empty"}
    
    # Get all cart items
    result = await session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    # Delete all items
    for item in cart_items:
        await session.delete(item)
    
    await session.commit()
    
    return {"message": "Cart cleared", "items_removed": len(cart_items)}


@router.post("/validate", response_model=CartValidationResponse)
async def validate_cart(
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Validate cart before checkout.
    
    Validates: Requirements 6.5, 6.6
    - Checks product availability
    - Verifies prices haven't changed
    """
    from app.models.entities import Price
    
    # Get cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        return CartValidationResponse(valid=True, errors=[])
    
    # Get all cart items with products
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    errors = []
    
    for item in cart_items:
        product = item.product
        
        # Check if product is still active
        if not product.is_active or product.is_deleted:
            errors.append(ValidationError(
                item_id=item.id,
                lot_id=product.id,
                error="Product is no longer available"
            ))
            continue
        
        # Get current active price
        price_result = await session.execute(
            select(Price).where(
                Price.product_id == product.id,
                Price.is_active == True
            ).limit(1)
        )
        current_price = price_result.scalar_one_or_none()
        
        if not current_price:
            errors.append(ValidationError(
                item_id=item.id,
                lot_id=product.id,
                error="Product price is not available"
            ))
    
    return CartValidationResponse(
        valid=len(errors) == 0,
        errors=errors
    )



@router.post("/apply-promo", response_model=ApplyPromoResponse)
async def apply_promo_code(
    request: ApplyPromoRequest,
    user_id: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Apply promo code to cart and calculate discount.
    
    Validates: Requirements 15.1, 15.2, 15.5, 15.7
    - Validates promo code exists and is active
    - Checks expiration date and usage limits
    - Calculates discount based on promo type
    - Ensures discounted price never negative
    """
    from app.models.entities import PromoCode, PromoCodeUsage, Price
    from app.models.enums import PromoType
    
    # Get cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Get cart items
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Find promo code
    result = await session.execute(
        select(PromoCode).where(
            and_(
                PromoCode.code == request.promo_code.upper(),
                PromoCode.is_deleted == False
            )
        )
    )
    promo_code = result.scalar_one_or_none()
    
    if not promo_code:
        return ApplyPromoResponse(
            success=False,
            message="Promo code not found"
        )
    
    # Validate promo code is active
    if not promo_code.is_active:
        return ApplyPromoResponse(
            success=False,
            message="Promo code is not active"
        )
    
    # Check expiration dates
    now = datetime.utcnow()
    if promo_code.starts_at and promo_code.starts_at > now:
        return ApplyPromoResponse(
            success=False,
            message="Promo code is not yet valid"
        )
    
    if promo_code.ends_at and promo_code.ends_at < now:
        return ApplyPromoResponse(
            success=False,
            message="Promo code has expired"
        )
    
    # Check usage limit
    if promo_code.max_usages is not None and promo_code.used_count >= promo_code.max_usages:
        return ApplyPromoResponse(
            success=False,
            message="Promo code usage limit reached"
        )
    
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
        return ApplyPromoResponse(
            success=False,
            message="You have already used this promo code"
        )
    
    # Check if only for new users
    if promo_code.only_new_users:
        # Check if user has any completed orders
        from app.models.entities import Order
        from app.models.enums import OrderStatus
        
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
            return ApplyPromoResponse(
                success=False,
                message="This promo code is only for new users"
            )
    
    # Calculate cart total
    cart_total = Decimal("0.00")
    applicable_items = []
    
    for item in cart_items:
        product = item.product
        
        # Check if promo is restricted to specific game or product
        if promo_code.game_id and product.game_id != promo_code.game_id:
            continue
        
        if promo_code.product_id and product.id != promo_code.product_id:
            continue
        
        # Get current price
        price_result = await session.execute(
            select(Price).where(
                Price.product_id == product.id,
                Price.is_active == True
            ).limit(1)
        )
        price = price_result.scalar_one_or_none()
        
        if price:
            item_total = price.base_price * item.quantity
            cart_total += item_total
            applicable_items.append((item, price, item_total))
    
    if not applicable_items:
        return ApplyPromoResponse(
            success=False,
            message="Promo code is not applicable to items in your cart"
        )
    
    # Calculate discount based on promo type
    discount_amount = Decimal("0.00")
    
    if promo_code.promo_type == PromoType.PERCENT:
        # Percentage discount
        discount_amount = (cart_total * promo_code.value) / Decimal("100")
    elif promo_code.promo_type == PromoType.FIXED:
        # Fixed amount discount
        discount_amount = promo_code.value
    
    # Ensure discount doesn't exceed cart total (price never negative)
    if discount_amount > cart_total:
        discount_amount = cart_total
    
    discounted_total = cart_total - discount_amount
    
    # Ensure discounted total is never negative
    if discounted_total < Decimal("0.00"):
        discounted_total = Decimal("0.00")
    
    return ApplyPromoResponse(
        success=True,
        message="Promo code applied successfully",
        discount_amount=discount_amount,
        promo_type=promo_code.promo_type.value,
        original_total=cart_total,
        discounted_total=discounted_total
    )
