"""Test chat WebSocket endpoint implementation."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from datetime import datetime, timedelta

from api.main import app
from app.models.entities import User, Seller, Deal, DealMessage, Lot, Product, Category, Game, Order
from app.models.enums import DealStatus, SellerStatus, LotStatus, OrderStatus
from api.dependencies.auth import create_access_token


@pytest.mark.asyncio
async def test_websocket_chat_authentication(db_session):
    """Test WebSocket authentication with JWT token."""
    # Create test users
    buyer = User(
        telegram_id=123456,
        username="buyer_test",
        first_name="Buyer",
        is_blocked=False
    )
    seller_user = User(
        telegram_id=789012,
        username="seller_test",
        first_name="Seller",
        is_blocked=False
    )
    db_session.add_all([buyer, seller_user])
    await db_session.commit()
    await db_session.refresh(buyer)
    await db_session.refresh(seller_user)
    
    # Create seller
    seller = Seller(
        user_id=seller_user.id,
        status=SellerStatus.ACTIVE,
        shop_name="Test Shop"
    )
    db_session.add(seller)
    await db_session.commit()
    await db_session.refresh(seller)
    
    # Create game, category, product for lot
    game = Game(slug="test-game", title="Test Game", is_active=True)
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    
    category = Category(game_id=game.id, slug="test-cat", title="Test Category", is_active=True)
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product",
        title="Test Product",
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    
    # Create lot
    lot = Lot(
        seller_id=seller.id,
        product_id=product.id,
        title="Test Lot",
        price=100.00,
        status=LotStatus.ACTIVE
    )
    db_session.add(lot)
    await db_session.commit()
    await db_session.refresh(lot)
    
    # Create order
    order = Order(
        order_number="TEST001",
        user_id=buyer.id,
        status=OrderStatus.PAID,
        total_amount=100.00
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    
    # Create deal
    deal = Deal(
        order_id=order.id,
        buyer_id=buyer.id,
        seller_id=seller.id,
        lot_id=lot.id,
        status=DealStatus.CREATED,
        amount=100.00,
        commission_amount=10.00,
        seller_amount=90.00
    )
    db_session.add(deal)
    await db_session.commit()
    await db_session.refresh(deal)
    
    # Create access token for buyer
    token = create_access_token(buyer.telegram_id)
    
    # Test WebSocket connection
    client = TestClient(app)
    
    # Test with valid token
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={token}") as websocket:
        # Should receive connection confirmation
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert data["deal_id"] == deal.id
        assert data["user_id"] == buyer.id
        
        # Send a text message
        websocket.send_json({
            "type": "text",
            "message_text": "Hello from buyer!"
        })
        
        # Should receive message confirmation
        response = websocket.receive_json()
        assert response["type"] == "message"
        assert response["deal_id"] == deal.id
        assert response["sender_id"] == buyer.id
        assert response["message_text"] == "Hello from buyer!"
        assert response["is_read"] == False
        
        # Verify message was saved to database
        result = await db_session.execute(
            select(DealMessage).where(DealMessage.deal_id == deal.id)
        )
        messages = result.scalars().all()
        assert len(messages) == 1
        assert messages[0].message_text == "Hello from buyer!"
        assert messages[0].sender_id == buyer.id
        assert messages[0].is_read == False


@pytest.mark.asyncio
async def test_websocket_chat_unauthorized_access(db_session):
    """Test that unauthorized users cannot access deal chat."""
    # Create test users
    buyer = User(
        telegram_id=123456,
        username="buyer_test",
        first_name="Buyer",
        is_blocked=False
    )
    seller_user = User(
        telegram_id=789012,
        username="seller_test",
        first_name="Seller",
        is_blocked=False
    )
    unauthorized_user = User(
        telegram_id=999999,
        username="unauthorized",
        first_name="Unauthorized",
        is_blocked=False
    )
    db_session.add_all([buyer, seller_user, unauthorized_user])
    await db_session.commit()
    await db_session.refresh(buyer)
    await db_session.refresh(seller_user)
    await db_session.refresh(unauthorized_user)
    
    # Create seller
    seller = Seller(
        user_id=seller_user.id,
        status=SellerStatus.ACTIVE,
        shop_name="Test Shop"
    )
    db_session.add(seller)
    await db_session.commit()
    await db_session.refresh(seller)
    
    # Create game, category, product for lot
    game = Game(slug="test-game", title="Test Game", is_active=True)
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    
    category = Category(game_id=game.id, slug="test-cat", title="Test Category", is_active=True)
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    
    product = Product(
        game_id=game.id,
        category_id=category.id,
        slug="test-product",
        title="Test Product",
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    
    # Create lot
    lot = Lot(
        seller_id=seller.id,
        product_id=product.id,
        title="Test Lot",
        price=100.00,
        status=LotStatus.ACTIVE
    )
    db_session.add(lot)
    await db_session.commit()
    await db_session.refresh(lot)
    
    # Create order
    order = Order(
        order_number="TEST001",
        user_id=buyer.id,
        status=OrderStatus.PAID,
        total_amount=100.00
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    
    # Create deal
    deal = Deal(
        order_id=order.id,
        buyer_id=buyer.id,
        seller_id=seller.id,
        lot_id=lot.id,
        status=DealStatus.CREATED,
        amount=100.00,
        commission_amount=10.00,
        seller_amount=90.00
    )
    db_session.add(deal)
    await db_session.commit()
    await db_session.refresh(deal)
    
    # Create access token for unauthorized user
    token = create_access_token(unauthorized_user.telegram_id)
    
    # Test WebSocket connection - should be rejected
    client = TestClient(app)
    
    with pytest.raises(Exception):  # WebSocket should close with policy violation
        with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={token}") as websocket:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
