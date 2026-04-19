"""Manual test script for cart validation and promo code endpoints."""
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.models.entities import (
    User, Cart, CartItem, Game, Category, Product, Price,
    PromoCode, PromoCodeUsage
)
from app.models.enums import PromoType


async def setup_test_data(session: AsyncSession):
    """Set up test data."""
    print("Setting up test data...")
    
    # Create test user
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        balance=Decimal("0.00")
    )
    session.add(user)
    await session.flush()
    print(f"Created user: {user.id}")
    
    # Create test game
    game = Game(
        slug="test-game",
        title="Test Game",
        description="A test game",
        is_active=True,
        sort_order=1
    )
    session.add(game)
    await session.flush()
    print(f"Created game: {game.id}")
    
    # Create test category
    category = Category(
        game_id=game.id,
        slug="test-category",
        title="Test Category",
        description="A test category",
        is_active=True,
        sort_order=1
    )
    session.add(category)
    await session.flush()
    print(f"Created category: {category.id}")
    
    # Create test products
    product1 = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product-1",
        title="Test Product 1",
        description="A test product",
        is_active=True,
        sort_order=1
    )
    session.add(product1)
    await session.flush()
    
    product2 = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product-2",
        title="Test Product 2",
        description="Another test product",
        is_active=True,
        sort_order=2
    )
    session.add(product2)
    await session.flush()
    print(f"Created products: {product1.id}, {product2.id}")
    
    # Create test prices
    price1 = Price(
        product_id=product1.id,
        base_price=Decimal("100.00"),
        currency_code="RUB",
        is_active=True
    )
    session.add(price1)
    
    price2 = Price(
        product_id=product2.id,
        base_price=Decimal("200.00"),
        currency_code="RUB",
        is_active=True
    )
    session.add(price2)
    await session.flush()
    print(f"Created prices: {price1.id}, {price2.id}")
    
    # Create cart
    cart = Cart(user_id=user.id)
    session.add(cart)
    await session.flush()
    print(f"Created cart: {cart.id}")
    
    # Add items to cart
    cart_item1 = CartItem(
        cart_id=cart.id,
        product_id=product1.id,
        quantity=2
    )
    session.add(cart_item1)
    
    cart_item2 = CartItem(
        cart_id=cart.id,
        product_id=product2.id,
        quantity=1
    )
    session.add(cart_item2)
    print(f"Added items to cart")
    
    # Create promo codes
    promo_percentage = PromoCode(
        code="SAVE20",
        promo_type=PromoType.PERCENT,
        value=Decimal("20.00"),
        max_usages=100,
        used_count=0,
        starts_at=datetime.utcnow() - timedelta(days=1),
        ends_at=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    session.add(promo_percentage)
    
    promo_fixed = PromoCode(
        code="FIXED50",
        promo_type=PromoType.FIXED,
        value=Decimal("50.00"),
        max_usages=50,
        used_count=0,
        starts_at=datetime.utcnow() - timedelta(days=1),
        ends_at=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    session.add(promo_fixed)
    
    promo_expired = PromoCode(
        code="EXPIRED",
        promo_type=PromoType.PERCENT,
        value=Decimal("30.00"),
        max_usages=100,
        used_count=0,
        starts_at=datetime.utcnow() - timedelta(days=30),
        ends_at=datetime.utcnow() - timedelta(days=1),
        is_active=True
    )
    session.add(promo_expired)
    
    print("Created promo codes: SAVE20, FIXED50, EXPIRED")
    
    await session.commit()
    print("Test data setup complete!\n")
    
    return {
        "user": user,
        "cart": cart,
        "product1": product1,
        "product2": product2,
        "promo_percentage": promo_percentage,
        "promo_fixed": promo_fixed,
        "promo_expired": promo_expired
    }


async def test_cart_validation(session: AsyncSession, user_id: int):
    """Test cart validation endpoint logic."""
    print("=" * 60)
    print("Testing Cart Validation")
    print("=" * 60)
    
    # Get cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        print("❌ Cart not found")
        return
    
    # Get cart items
    result = await session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    print(f"✓ Found cart with {len(cart_items)} items")
    
    # Validate each item
    errors = []
    for item in cart_items:
        result = await session.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product or not product.is_active or product.is_deleted:
            errors.append(f"Product {item.product_id} is not available")
        else:
            result = await session.execute(
                select(Price).where(
                    Price.product_id == product.id,
                    Price.is_active == True
                ).limit(1)
            )
            price = result.scalar_one_or_none()
            
            if not price:
                errors.append(f"Product {item.product_id} has no active price")
            else:
                print(f"  ✓ Item {item.id}: {product.title} x{item.quantity} @ {price.base_price} RUB")
    
    if errors:
        print(f"\n❌ Validation failed with {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ Cart validation passed!")
    
    print()


async def test_promo_code_application(session: AsyncSession, user_id: int, promo_code: str):
    """Test promo code application logic."""
    print("=" * 60)
    print(f"Testing Promo Code: {promo_code}")
    print("=" * 60)
    
    # Get cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()
    
    if not cart:
        print("❌ Cart not found")
        return
    
    # Get cart items with products
    result = await session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    
    if not cart_items:
        print("❌ Cart is empty")
        return
    
    # Find promo code
    result = await session.execute(
        select(PromoCode).where(
            PromoCode.code == promo_code.upper(),
            PromoCode.is_deleted == False
        )
    )
    promo = result.scalar_one_or_none()
    
    if not promo:
        print(f"❌ Promo code '{promo_code}' not found")
        return
    
    print(f"✓ Found promo code: {promo.code}")
    print(f"  Type: {promo.promo_type.value}")
    print(f"  Value: {promo.value}")
    print(f"  Active: {promo.is_active}")
    
    # Check expiration
    now = datetime.utcnow()
    if promo.starts_at and promo.starts_at > now:
        print(f"❌ Promo code not yet valid (starts at {promo.starts_at})")
        return
    
    if promo.ends_at and promo.ends_at < now:
        print(f"❌ Promo code expired (ended at {promo.ends_at})")
        return
    
    # Check usage limit
    if promo.max_usages is not None and promo.used_count >= promo.max_usages:
        print(f"❌ Promo code usage limit reached ({promo.used_count}/{promo.max_usages})")
        return
    
    # Calculate cart total
    cart_total = Decimal("0.00")
    for item in cart_items:
        result = await session.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = result.scalar_one_or_none()
        
        if product:
            result = await session.execute(
                select(Price).where(
                    Price.product_id == product.id,
                    Price.is_active == True
                ).limit(1)
            )
            price = result.scalar_one_or_none()
            
            if price:
                item_total = price.base_price * item.quantity
                cart_total += item_total
                print(f"  Item: {product.title} x{item.quantity} = {item_total} RUB")
    
    print(f"\n  Cart Total: {cart_total} RUB")
    
    # Calculate discount
    discount_amount = Decimal("0.00")
    
    if promo.promo_type == PromoType.PERCENT:
        discount_amount = (cart_total * promo.value) / Decimal("100")
        print(f"  Discount ({promo.value}%): {discount_amount} RUB")
    elif promo.promo_type == PromoType.FIXED:
        discount_amount = promo.value
        print(f"  Discount (fixed): {discount_amount} RUB")
    
    # Ensure discount doesn't exceed cart total
    if discount_amount > cart_total:
        discount_amount = cart_total
        print(f"  ⚠ Discount capped at cart total")
    
    discounted_total = cart_total - discount_amount
    
    # Ensure discounted total is never negative
    if discounted_total < Decimal("0.00"):
        discounted_total = Decimal("0.00")
        print(f"  ⚠ Discounted total capped at 0.00")
    
    print(f"\n✓ Promo code applied successfully!")
    print(f"  Original Total: {cart_total} RUB")
    print(f"  Discount: -{discount_amount} RUB")
    print(f"  Final Total: {discounted_total} RUB")
    print()


async def main():
    """Run manual tests."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Setup test data
        test_data = await setup_test_data(session)
        user_id = test_data["user"].id
        
        # Test cart validation
        await test_cart_validation(session, user_id)
        
        # Test promo codes
        await test_promo_code_application(session, user_id, "SAVE20")
        await test_promo_code_application(session, user_id, "FIXED50")
        await test_promo_code_application(session, user_id, "EXPIRED")
        await test_promo_code_application(session, user_id, "NOTEXIST")
    
    await engine.dispose()
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
