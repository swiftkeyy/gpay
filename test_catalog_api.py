"""Test catalog API endpoints with Redis caching."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from app.db.session import get_db_session
from app.models import Game, Category, Product, Price
from api.services.cache import get_cache_service


@pytest.fixture
async def test_client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def setup_test_data(db_session: AsyncSession):
    """Set up test data for catalog tests."""
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
    
    # Create test product
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product",
        title="Test Product",
        description="A test product",
        is_active=True,
        sort_order=1
    )
    db_session.add(product)
    await db_session.flush()
    
    # Create test price
    price = Price(
        product_id=product.id,
        base_price=100.00,
        currency_code="RUB",
        is_active=True
    )
    db_session.add(price)
    
    await db_session.commit()
    
    return {
        "game": game,
        "category": category,
        "product": product,
        "price": price
    }


@pytest.mark.asyncio
async def test_get_games_with_pagination(test_client: AsyncClient, setup_test_data):
    """Test GET /api/v1/games with pagination."""
    response = await test_client.get("/api/v1/games?page=1&limit=20")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "pages" in data
    
    assert data["page"] == 1
    assert data["limit"] == 20
    assert len(data["items"]) > 0
    
    # Check game structure
    game = data["items"][0]
    assert "id" in game
    assert "name" in game
    assert "slug" in game
    assert "image_url" in game


@pytest.mark.asyncio
async def test_get_games_with_search(test_client: AsyncClient, setup_test_data):
    """Test GET /api/v1/games with search."""
    response = await test_client.get("/api/v1/games?search=Test")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert len(data["items"]) > 0
    
    # All games should match search
    for game in data["items"]:
        assert "test" in game["name"].lower()


@pytest.mark.asyncio
async def test_get_games_caching(test_client: AsyncClient, setup_test_data):
    """Test that games endpoint uses Redis caching."""
    cache = get_cache_service()
    
    # Clear cache
    await cache.delete_pattern("games:*")
    
    # First request - should be cache miss
    response1 = await test_client.get("/api/v1/games?page=1&limit=20")
    assert response1.status_code == 200
    
    # Second request - should be cache hit
    response2 = await test_client.get("/api/v1/games?page=1&limit=20")
    assert response2.status_code == 200
    
    # Responses should be identical
    assert response1.json() == response2.json()


@pytest.mark.asyncio
async def test_get_categories(test_client: AsyncClient, setup_test_data):
    """Test GET /api/v1/categories."""
    test_data = setup_test_data
    game_id = test_data["game"].id
    
    response = await test_client.get(f"/api/v1/categories?game_id={game_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0
    
    # Check category structure
    category = data["items"][0]
    assert "id" in category
    assert "name" in category
    assert "slug" in category
    assert "game_id" in category
    assert category["game_id"] == game_id


@pytest.mark.asyncio
async def test_get_categories_caching(test_client: AsyncClient, setup_test_data):
    """Test that categories endpoint uses Redis caching."""
    cache = get_cache_service()
    test_data = setup_test_data
    game_id = test_data["game"].id
    
    # Clear cache
    await cache.delete_pattern("categories:*")
    
    # First request - should be cache miss
    response1 = await test_client.get(f"/api/v1/categories?game_id={game_id}")
    assert response1.status_code == 200
    
    # Second request - should be cache hit
    response2 = await test_client.get(f"/api/v1/categories?game_id={game_id}")
    assert response2.status_code == 200
    
    # Responses should be identical
    assert response1.json() == response2.json()


@pytest.mark.asyncio
async def test_get_products_with_filters(test_client: AsyncClient, setup_test_data):
    """Test GET /api/v1/products with filters."""
    test_data = setup_test_data
    game_id = test_data["game"].id
    category_id = test_data["category"].id
    
    # Test with game_id filter
    response = await test_client.get(f"/api/v1/products?game_id={game_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    # Test with category_id filter
    response = await test_client.get(f"/api/v1/products?category_id={category_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    # Check product structure
    product = data[0]
    assert "id" in product
    assert "title" in product
    assert "category_id" in product
    assert product["category_id"] == category_id


@pytest.mark.asyncio
async def test_get_products_caching(test_client: AsyncClient, setup_test_data):
    """Test that products endpoint uses Redis caching."""
    cache = get_cache_service()
    test_data = setup_test_data
    game_id = test_data["game"].id
    
    # Clear cache
    await cache.delete_pattern("products:*")
    
    # First request - should be cache miss
    response1 = await test_client.get(f"/api/v1/products?game_id={game_id}")
    assert response1.status_code == 200
    
    # Second request - should be cache hit
    response2 = await test_client.get(f"/api/v1/products?game_id={game_id}")
    assert response2.status_code == 200
    
    # Responses should be identical
    assert response1.json() == response2.json()


@pytest.mark.asyncio
async def test_cache_ttl(test_client: AsyncClient, setup_test_data):
    """Test that cache has 5-minute TTL."""
    import asyncio
    
    cache = get_cache_service()
    
    # Set a test value with 2-second TTL
    await cache.set("test:ttl", {"test": "data"}, ttl=2)
    
    # Should exist immediately
    value = await cache.get("test:ttl")
    assert value is not None
    assert value["test"] == "data"
    
    # Wait 3 seconds
    await asyncio.sleep(3)
    
    # Should be expired
    value = await cache.get("test:ttl")
    assert value is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
