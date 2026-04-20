"""Test admin promo code management endpoints."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal


@pytest.mark.asyncio
async def test_create_promo_code(client, admin_user):
    """Test creating a promo code."""
    response = await client.post(
        "/api/v1/admin/promo-codes",
        json={
            "code": "SUMMER2024",
            "promo_type": "percent",
            "value": 20.0,
            "max_usages": 100,
            "starts_at": datetime.utcnow().isoformat(),
            "ends_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "is_active": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Promo code created"
    assert data["promo_code"]["code"] == "SUMMER2024"
    assert data["promo_code"]["promo_type"] == "percent"
    assert data["promo_code"]["value"] == 20.0


@pytest.mark.asyncio
async def test_get_promo_codes(client, admin_user):
    """Test listing promo codes."""
    response = await client.get("/api/v1/admin/promo-codes")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_update_promo_code(client, admin_user, promo_code):
    """Test updating a promo code."""
    response = await client.patch(
        f"/api/v1/admin/promo-codes/{promo_code.id}",
        json={
            "value": 25.0,
            "is_active": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Promo code updated"
    assert data["promo_code"]["value"] == 25.0
    assert data["promo_code"]["is_active"] is False


@pytest.mark.asyncio
async def test_delete_promo_code(client, admin_user, promo_code):
    """Test deleting (soft delete) a promo code."""
    response = await client.delete(f"/api/v1/admin/promo-codes/{promo_code.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Promo code deleted"


@pytest.mark.asyncio
async def test_create_promo_code_validation(client, admin_user):
    """Test promo code validation."""
    # Test invalid promo type
    response = await client.post(
        "/api/v1/admin/promo-codes",
        json={
            "code": "INVALID",
            "promo_type": "invalid_type",
            "value": 20.0
        }
    )
    assert response.status_code == 400
    
    # Test percentage > 100
    response = await client.post(
        "/api/v1/admin/promo-codes",
        json={
            "code": "INVALID2",
            "promo_type": "percent",
            "value": 150.0
        }
    )
    assert response.status_code == 400
    
    # Test negative value
    response = await client.post(
        "/api/v1/admin/promo-codes",
        json={
            "code": "INVALID3",
            "promo_type": "fixed",
            "value": -10.0
        }
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_promo_code_usage_tracking(client, user, promo_code):
    """Test that promo code usage is tracked correctly."""
    # Apply promo code to cart
    response = await client.post(
        "/api/v1/cart/apply-promo",
        json={"promo_code": promo_code.code}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["discount_amount"] is not None
    
    # Create order with promo code
    response = await client.post(
        "/api/v1/orders",
        json={
            "idempotency_key": "test-order-123",
            "promo_code": promo_code.code
        }
    )
    
    assert response.status_code == 200
    
    # Check promo code usage count increased
    response = await client.get(f"/api/v1/admin/promo-codes/{promo_code.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["used_count"] > 0
