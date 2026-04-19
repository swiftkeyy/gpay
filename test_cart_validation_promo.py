"""Test cart validation and promo code application."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from app.models.entities import (
    User, Cart, CartItem, Game, Category, Product, Price,
    PromoCode, PromoCodeUsage, Order
)
from app.models.enums import PromoType, OrderStatus


@pytest.fixture
async def test_client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def setup_cart_data(db_session: AsyncSession):
    """Set up test data for cart validation and promo tests."""
    # Create test user
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        balance=Decimal("0.00")
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create test game
    game = Game(
        slug="test-game",
        title="Test Game",
        description="A test game",
        is_active=True,
        sort_order=1
    )
    db_session.add(game)
    await db_session.flush()
    
    # Create test category
    category = Category(
        game_id=game.id,
        slug="test-category",
        title="Test Category",
        description="A test category",
        is_active=True,
        sort_order=1
    )
    db_session.add(category)
    await db_session.flush()
    
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
    db_session.add(product1)
    await db_session.flush()
    
    product2 = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product-2",
        title="Test Product 2",
        description="Another test product",
        is_active=True,
        sort_order=2
    )
    db_session.add(product2)
    await db_session.flush()
    
    # Create test prices
    price1 = Price(
        product_id=product1.id,
        base_price=Decimal("100.00"),
        currency_code="RUB",
        is_active=True
    )
    db_session.add(price1)
    
    price2 = Price(
        product_id=product2.id,
        base_price=Decimal("200.00"),
        currency_code="RUB",
        is_active=True
    )
    db_session.add(price2)
    await db_session.flush()
    
    # Create cart
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.flush()
    
    # Add items to cart
    cart_item1 = CartItem(
        cart_id=cart.id,
        product_id=product1.id,
        quantity=2
    )
    db_session.add(cart_item1)
    
    cart_item2 = CartItem(
        cart_id=cart.id,
        product_id=product2.id,
        quantity=1
    )
    db_session.add(cart_item2)
    
    # Create promo codes
    # Active percentage promo
    promo_percentage = PromoCode(
        code="SAVE20",
        promo_type=PromoType.PERCENTAGE,
        value=Decimal("20.00"),
        max_usages=100,
        used_count=0,
        starts_at=datetime.utcnow() - timedelta(days=1),
        ends_at=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    db_session.add(promo_percentage)
    
    # Active fixed amount promo
    promo_fixed = PromoCode(
        code="FIXED50",
        promo_type=PromoType.FIXED_AMOUNT,
        value=Decimal("50.00"),
        max_usages=50,
        used_count=0,
        starts_at=datetime.utcnow() - timedelta(days=1),
        ends_at=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    db_session.add(promo_fixed)
    
    # Expired promo
    promo_expired = PromoCode(
        code="EXPIRED",
        promo_type=PromoType.PERCENTAGE,
        value=Decimal("30.00"),
        max_usages=100,
        used_count=0,
        starts_at=datetime.utcnow() - timedelta(days=30),
        ends_at=datetime.utcnow() - timedelta(days=1),
        is_active=True
    )
    db_session.add(promo_expired)
    
    # Fully used promo
    promo_used = PromoCode(
        code="FULLUSED",
        promo_type=PromoType.PERCENTAGE,
        value=Decimal("25.00"),
        max_usages=10,
        used_count=10,
        starts_at=datetime.utcnow() - timedelta(days=1),
        ends_at=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    db_session.add(promo_used)
    
    # New users only promo
    promo_new_users = PromoCode(
        code="NEWUSER10",
        promo_type=PromoType.PERCENTAGE,
        value=Decimal("10.00"),
        max_usages=1000,
        used_count=0,
        starts_at=datetime.utcnow() - timedelta(days=1),
        ends_at=datetime.utcnow() + timedelta(days=30),
        only_new_users=True,
        is_active=True
    )
    db_session.add(promo_new_users)
    
    await db_session.commit()
    
    return {
        "user": user,
        "game": game,
        "category": category,
        "product1": product1,
        "product2": product2,
        "price1": price1,
        "price2": price2,
        "cart": cart,
        "cart_item1": cart_item1,
        "cart_item2": cart_item2,
        "promo_percentage": promo_percentage,
        "promo_fixed": promo_fixed,
        "promo_expired": promo_expired,
        "promo_used": promo_used,
        "promo_new_users": promo_new_users
    }


@pytest.mark.asyncio
async def test_validate_cart_success(test_client: AsyncClient, setup_cart_data):
    """Test cart validation with valid cart."""
    response = await test_client.post("/api/v1/cart/validate?user_id=1")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valid"] is True
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_validate_cart_inactive_product(test_client: AsyncClient, setup_cart_data, db_session: AsyncSession):
    """Test cart validation with inactive product."""
    # Make product inactive
    product = setup_cart_data["product1"]
    product.is_active = False
    await db_session.commit()
    
    response = await test_client.post("/api/v1/cart/validate?user_id=1")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valid"] is False
    assert len(data["errors"]) > 0
    assert "no longer available" in data["errors"][0]["error"]


@pytest.mark.asyncio
async def test_apply_promo_percentage_success(test_client: AsyncClient, setup_cart_data):
    """Test applying percentage promo code successfully."""
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "SAVE20"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["promo_type"] == "percentage"
    # Cart total: 2*100 + 1*200 = 400
    # Discount: 20% of 400 = 80
    assert data["original_total"] == "400.00"
    assert data["discount_amount"] == "80.00"
    assert data["discounted_total"] == "320.00"


@pytest.mark.asyncio
async def test_apply_promo_fixed_amount_success(test_client: AsyncClient, setup_cart_data):
    """Test applying fixed amount promo code successfully."""
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "FIXED50"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["promo_type"] == "fixed_amount"
    # Cart total: 400
    # Discount: 50
    assert data["original_total"] == "400.00"
    assert data["discount_amount"] == "50.00"
    assert data["discounted_total"] == "350.00"


@pytest.mark.asyncio
async def test_apply_promo_not_found(test_client: AsyncClient, setup_cart_data):
    """Test applying non-existent promo code."""
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "NOTEXIST"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_apply_promo_expired(test_client: AsyncClient, setup_cart_data):
    """Test applying expired promo code."""
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "EXPIRED"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert "expired" in data["message"].lower()


@pytest.mark.asyncio
async def test_apply_promo_usage_limit_reached(test_client: AsyncClient, setup_cart_data):
    """Test applying promo code with usage limit reached."""
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "FULLUSED"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert "usage limit" in data["message"].lower()


@pytest.mark.asyncio
async def test_apply_promo_already_used(test_client: AsyncClient, setup_cart_data, db_session: AsyncSession):
    """Test applying promo code that user already used."""
    # Create usage record
    promo = setup_cart_data["promo_percentage"]
    user = setup_cart_data["user"]
    
    usage = PromoCodeUsage(
        promo_code_id=promo.id,
        user_id=user.id
    )
    db_session.add(usage)
    await db_session.commit()
    
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "SAVE20"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert "already used" in data["message"].lower()


@pytest.mark.asyncio
async def test_apply_promo_new_users_only_with_existing_order(test_client: AsyncClient, setup_cart_data, db_session: AsyncSession):
    """Test applying new users only promo when user has existing orders."""
    # Create completed order for user
    user = setup_cart_data["user"]
    
    order = Order(
        order_number="TEST001",
        user_id=user.id,
        status=OrderStatus.COMPLETED,
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.commit()
    
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "NEWUSER10"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert "new users" in data["message"].lower()


@pytest.mark.asyncio
async def test_apply_promo_ensures_non_negative_price(test_client: AsyncClient, setup_cart_data, db_session: AsyncSession):
    """Test that promo code ensures discounted price never goes negative."""
    # Create a promo with very high fixed discount
    promo_huge = PromoCode(
        code="HUGE1000",
        promo_type=PromoType.FIXED_AMOUNT,
        value=Decimal("1000.00"),  # More than cart total
        max_usages=10,
        used_count=0,
        starts_at=datetime.utcnow() - timedelta(days=1),
        ends_at=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    db_session.add(promo_huge)
    await db_session.commit()
    
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "HUGE1000"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    # Cart total is 400, discount should be capped at 400
    assert Decimal(data["discount_amount"]) == Decimal("400.00")
    assert Decimal(data["discounted_total"]) == Decimal("0.00")
    # Ensure it's not negative
    assert Decimal(data["discounted_total"]) >= Decimal("0.00")


@pytest.mark.asyncio
async def test_apply_promo_empty_cart(test_client: AsyncClient, setup_cart_data, db_session: AsyncSession):
    """Test applying promo code to empty cart."""
    # Clear cart items
    cart = setup_cart_data["cart"]
    await db_session.execute(
        f"DELETE FROM cart_items WHERE cart_id = {cart.id}"
    )
    await db_session.commit()
    
    response = await test_client.post(
        "/api/v1/cart/apply-promo?user_id=1",
        json={"promo_code": "SAVE20"}
    )
    
    assert response.status_code == 400
    data = response.json()
    
    assert "empty" in data["detail"].lower()
