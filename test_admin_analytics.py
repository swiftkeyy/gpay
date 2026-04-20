"""Test admin dashboard and analytics endpoints."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, Admin, Seller, Lot, Deal, Order, Game, Category, Product
from app.models.enums import DealStatus, SellerStatus, OrderStatus
from api.routers.admin import get_dashboard, get_revenue_analytics, get_top_sellers, get_top_products


@pytest.mark.asyncio
async def test_admin_dashboard_all_time(db_session: AsyncSession):
    """Test admin dashboard with all-time stats."""
    # Create admin user
    admin_user = User(
        telegram_id=999999,
        username="admin_user",
        balance=Decimal("0.00"),
        referral_code="ADMIN123"
    )
    db_session.add(admin_user)
    await db_session.flush()
    
    admin = Admin(user_id=admin_user.id, role="superadmin")
    db_session.add(admin)
    
    # Create test data
    # Create a seller
    seller_user = User(
        telegram_id=888888,
        username="test_seller",
        balance=Decimal("0.00"),
        referral_code="SELLER123"
    )
    db_session.add(seller_user)
    await db_session.flush()
    
    seller = Seller(
        user_id=seller_user.id,
        shop_name="Test Shop",
        status=SellerStatus.ACTIVE,
        balance=Decimal("1000.00")
    )
    db_session.add(seller)
    await db_session.flush()
    
    # Create game, category, product
    game = Game(name="Test Game", slug="test-game")
    db_session.add(game)
    await db_session.flush()
    
    category = Category(game_id=game.id, name="Test Category", slug="test-category")
    db_session.add(category)
    await db_session.flush()
    
    product = Product(
        game_id=game.id,
        category_id=category.id,
        name="Test Product",
        slug="test-product"
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create lot
    lot = Lot(
        seller_id=seller.id,
        product_id=product.id,
        title="Test Lot",
        description="Test description",
        price=Decimal("100.00"),
        currency_code="RUB",
        delivery_type="manual",
        status="active"
    )
    db_session.add(lot)
    await db_session.flush()
    
    # Create buyer
    buyer_user = User(
        telegram_id=777777,
        username="test_buyer",
        balance=Decimal("500.00"),
        referral_code="BUYER123"
    )
    db_session.add(buyer_user)
    await db_session.flush()
    
    # Create order
    order = Order(
        order_number="ORD001",
        user_id=buyer_user.id,
        status=OrderStatus.PAID,
        subtotal_amount=Decimal("100.00"),
        total_amount=Decimal("100.00"),
        currency_code="RUB"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create completed deal
    deal = Deal(
        order_id=order.id,
        buyer_id=buyer_user.id,
        seller_id=seller.id,
        lot_id=lot.id,
        status=DealStatus.COMPLETED,
        amount=Decimal("100.00"),
        commission_amount=Decimal("10.00"),
        seller_amount=Decimal("90.00"),
        escrow_released=True
    )
    db_session.add(deal)
    await db_session.commit()
    
    # Test dashboard function directly
    data = await get_dashboard(user_id=admin_user.id, session=db_session)
    
    # Verify structure
    assert "users" in data
    assert "lots" in data
    assert "orders" in data
    assert "deals" in data
    assert "revenue" in data
    
    # Verify counts
    assert data["users"]["total"] >= 3  # admin, seller, buyer
    assert data["users"]["sellers"] >= 1
    assert data["users"]["active_sellers"] >= 1
    assert data["lots"]["total"] >= 1
    assert data["lots"]["active"] >= 1
    assert data["orders"]["total"] >= 1
    assert data["deals"]["total"] >= 1
    assert data["deals"]["completed"] >= 1
    assert data["revenue"]["total"] >= 10.0  # commission


@pytest.mark.asyncio
async def test_revenue_analytics(db_session: AsyncSession):
    """Test revenue analytics endpoint."""
    # Create admin user
    admin_user = User(
        telegram_id=999998,
        username="admin_user2",
        balance=Decimal("0.00"),
        referral_code="ADMIN124"
    )
    db_session.add(admin_user)
    await db_session.flush()
    
    admin = Admin(user_id=admin_user.id, role="superadmin")
    db_session.add(admin)
    await db_session.commit()
    
    # Test revenue analytics function
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    data = await get_revenue_analytics(
        user_id=admin_user.id,
        group_by="day",
        start_date=start_date,
        end_date=end_date,
        session=db_session
    )
    
    # Verify structure
    assert "group_by" in data
    assert data["group_by"] == "day"
    assert "start_date" in data
    assert "end_date" in data
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_top_sellers(db_session: AsyncSession):
    """Test top sellers endpoint."""
    # Create admin user
    admin_user = User(
        telegram_id=999997,
        username="admin_user3",
        balance=Decimal("0.00"),
        referral_code="ADMIN125"
    )
    db_session.add(admin_user)
    await db_session.flush()
    
    admin = Admin(user_id=admin_user.id, role="superadmin")
    db_session.add(admin)
    await db_session.commit()
    
    # Test top sellers function
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    data = await get_top_sellers(
        user_id=admin_user.id,
        limit=10,
        start_date=start_date,
        end_date=end_date,
        rank_by="revenue",
        session=db_session
    )
    
    # Verify structure
    assert "rank_by" in data
    assert data["rank_by"] == "revenue"
    assert "start_date" in data
    assert "end_date" in data
    assert "limit" in data
    assert "sellers" in data
    assert isinstance(data["sellers"], list)


@pytest.mark.asyncio
async def test_top_products(db_session: AsyncSession):
    """Test top products endpoint."""
    # Create admin user
    admin_user = User(
        telegram_id=999996,
        username="admin_user4",
        balance=Decimal("0.00"),
        referral_code="ADMIN126"
    )
    db_session.add(admin_user)
    await db_session.flush()
    
    admin = Admin(user_id=admin_user.id, role="superadmin")
    db_session.add(admin)
    await db_session.commit()
    
    # Test top products function
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    data = await get_top_products(
        user_id=admin_user.id,
        limit=10,
        start_date=start_date,
        end_date=end_date,
        session=db_session
    )
    
    # Verify structure
    assert "start_date" in data
    assert "end_date" in data
    assert "limit" in data
    assert "products" in data
    assert isinstance(data["products"], list)


@pytest.mark.asyncio
async def test_dashboard_with_date_range(db_session: AsyncSession):
    """Test admin dashboard with date range filtering."""
    # Create admin user
    admin_user = User(
        telegram_id=999995,
        username="admin_user5",
        balance=Decimal("0.00"),
        referral_code="ADMIN127"
    )
    db_session.add(admin_user)
    await db_session.flush()
    
    admin = Admin(user_id=admin_user.id, role="superadmin")
    db_session.add(admin)
    await db_session.commit()
    
    # Test dashboard with date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    data = await get_dashboard(
        user_id=admin_user.id,
        start_date=start_date,
        end_date=end_date,
        session=db_session
    )
    
    # Verify date range is included in response
    assert "date_range" in data
    assert data["date_range"]["start_date"] is not None
    assert data["date_range"]["end_date"] is not None


@pytest.mark.asyncio
async def test_non_admin_access_denied(db_session: AsyncSession):
    """Test that non-admin users cannot access admin endpoints."""
    # Create regular user (not admin)
    regular_user = User(
        telegram_id=888887,
        username="regular_user",
        balance=Decimal("0.00"),
        referral_code="USER123"
    )
    db_session.add(regular_user)
    await db_session.commit()
    
    # Try to access dashboard - should raise HTTPException
    with pytest.raises(Exception) as exc_info:
        await get_dashboard(user_id=regular_user.id, session=db_session)
    
    assert "Admin access required" in str(exc_info.value)
    
    # Try to access revenue analytics
    with pytest.raises(Exception) as exc_info:
        await get_revenue_analytics(
            user_id=regular_user.id,
            group_by="day",
            session=db_session
        )
    
    assert "Admin access required" in str(exc_info.value)
    
    # Try to access top sellers
    with pytest.raises(Exception) as exc_info:
        await get_top_sellers(
            user_id=regular_user.id,
            limit=10,
            session=db_session
        )
    
    assert "Admin access required" in str(exc_info.value)
    
    # Try to access top products
    with pytest.raises(Exception) as exc_info:
        await get_top_products(
            user_id=regular_user.id,
            limit=10,
            session=db_session
        )
    
    assert "Admin access required" in str(exc_info.value)

