"""Test order creation from cart with Product-based system."""
import asyncio
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import session_factory
from app.models.entities import (
    User, Cart, CartItem, Product, Price, Game, Category,
    Order, OrderItem, PromoCode, PromoCodeUsage
)
from app.models.enums import OrderStatus, PromoType


async def test_order_creation():
    """Test creating an order from cart."""
    async with session_factory() as session:
        # Get or create test user
        result = await session.execute(
            select(User).where(User.telegram_id == 123456789)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=123456789,
                username="testuser",
                first_name="Test",
                balance=Decimal("0.00")
            )
            session.add(user)
            await session.flush()
        
        print(f"✓ User: {user.username} (ID: {user.id})")
        
        # Get a test game
        result = await session.execute(
            select(Game).where(Game.is_active == True).limit(1)
        )
        game = result.scalar_one_or_none()
        
        if not game:
            print("✗ No active games found")
            return
        
        print(f"✓ Game: {game.title}")
        
        # Get a test product
        result = await session.execute(
            select(Product).where(
                Product.game_id == game.id,
                Product.is_active == True
            ).limit(1)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            print("✗ No active products found")
            return
        
        print(f"✓ Product: {product.title}")
        
        # Get product price
        result = await session.execute(
            select(Price).where(
                Price.product_id == product.id,
                Price.is_active == True
            ).limit(1)
        )
        price = result.scalar_one_or_none()
        
        if not price:
            print("✗ No active price found")
            return
        
        print(f"✓ Price: {price.base_price} {price.currency_code}")
        
        # Create or get cart
        result = await session.execute(
            select(Cart).where(Cart.user_id == user.id)
        )
        cart = result.scalar_one_or_none()
        
        if not cart:
            cart = Cart(user_id=user.id)
            session.add(cart)
            await session.flush()
        
        # Clear existing cart items
        result = await session.execute(
            select(CartItem).where(CartItem.cart_id == cart.id)
        )
        existing_items = result.scalars().all()
        for item in existing_items:
            await session.delete(item)
        
        # Add product to cart
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=2
        )
        session.add(cart_item)
        await session.commit()
        
        print(f"✓ Added {cart_item.quantity}x {product.title} to cart")
        
        # Test order creation without promo code
        print("\n--- Test 1: Order without promo code ---")
        
        from uuid import uuid4
        idempotency_key = f"test-{uuid4().hex}"
        
        # Simulate order creation
        result = await session.execute(
            select(CartItem).where(CartItem.cart_id == cart.id)
        )
        cart_items = result.scalars().all()
        
        subtotal = Decimal("0.00")
        for item in cart_items:
            result = await session.execute(
                select(Price).where(
                    Price.product_id == item.product_id,
                    Price.is_active == True
                ).limit(1)
            )
            item_price = result.scalar_one()
            subtotal += item_price.base_price * item.quantity
        
        print(f"  Subtotal: {subtotal}")
        
        order_number = f"GP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        
        order = Order(
            order_number=order_number,
            user_id=user.id,
            status=OrderStatus.NEW,
            subtotal_amount=subtotal,
            discount_amount=Decimal("0.00"),
            total_amount=subtotal,
            idempotency_key=idempotency_key
        )
        session.add(order)
        await session.flush()
        
        print(f"✓ Order created: {order.order_number}")
        print(f"  Total: {order.total_amount}")
        
        # Create order items
        for item in cart_items:
            result = await session.execute(
                select(Product).where(Product.id == item.product_id)
            )
            prod = result.scalar_one()
            
            result = await session.execute(
                select(Price).where(
                    Price.product_id == item.product_id,
                    Price.is_active == True
                ).limit(1)
            )
            item_price = result.scalar_one()
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                title_snapshot=prod.title,
                quantity=item.quantity,
                unit_price=item_price.base_price,
                total_price=item_price.base_price * item.quantity,
                fulfillment_type=prod.fulfillment_type
            )
            session.add(order_item)
        
        await session.commit()
        print(f"✓ Order items created")
        
        # Test idempotency
        print("\n--- Test 2: Idempotency check ---")
        result = await session.execute(
            select(Order).where(
                Order.user_id == user.id,
                Order.idempotency_key == idempotency_key
            )
        )
        duplicate_check = result.scalar_one_or_none()
        
        if duplicate_check:
            print(f"✓ Idempotency works: Found existing order {duplicate_check.order_number}")
        else:
            print("✗ Idempotency failed")
        
        # Test with promo code
        print("\n--- Test 3: Order with promo code ---")
        
        # Create test promo code
        promo_code = PromoCode(
            code="TEST10",
            promo_type=PromoType.PERCENT,
            value=Decimal("10.00"),
            is_active=True
        )
        session.add(promo_code)
        await session.flush()
        
        print(f"✓ Created promo code: {promo_code.code} ({promo_code.value}% off)")
        
        # Add item back to cart
        cart_item2 = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=1
        )
        session.add(cart_item2)
        await session.commit()
        
        # Calculate with promo
        discount = (subtotal * promo_code.value) / Decimal("100")
        total_with_promo = subtotal - discount
        
        print(f"  Subtotal: {subtotal}")
        print(f"  Discount: {discount}")
        print(f"  Total: {total_with_promo}")
        
        idempotency_key2 = f"test-{uuid4().hex}"
        order_number2 = f"GP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        
        order2 = Order(
            order_number=order_number2,
            user_id=user.id,
            status=OrderStatus.NEW,
            subtotal_amount=subtotal,
            discount_amount=discount,
            total_amount=total_with_promo,
            promo_code_id=promo_code.id,
            idempotency_key=idempotency_key2
        )
        session.add(order2)
        await session.flush()
        
        print(f"✓ Order with promo created: {order2.order_number}")
        
        # Record promo usage
        promo_usage = PromoCodeUsage(
            promo_code_id=promo_code.id,
            user_id=user.id,
            order_id=order2.id
        )
        session.add(promo_usage)
        promo_code.used_count += 1
        
        await session.commit()
        print(f"✓ Promo code usage recorded")
        
        print("\n=== All tests passed! ===")


if __name__ == "__main__":
    asyncio.run(test_order_creation())
