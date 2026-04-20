"""Test WebSocket reconnection and message queuing functionality."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from datetime import datetime

from api.main import app
from app.models.entities import User, Seller, Deal, DealMessage, Lot, Product, Category, Game, Order
from app.models.enums import DealStatus, SellerStatus, LotStatus, OrderStatus
from api.dependencies.auth import create_access_token


@pytest.mark.asyncio
async def test_websocket_missed_messages_sync(db_session):
    """Test that client can request and receive missed messages on reconnection."""
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
    
    # Pre-populate some messages (simulating messages sent while client was disconnected)
    messages_data = [
        {"text": "Message 1", "sender": seller_user},
        {"text": "Message 2", "sender": buyer},
        {"text": "Message 3", "sender": seller_user},
        {"text": "Message 4", "sender": buyer},
        {"text": "Message 5", "sender": seller_user},
    ]
    
    created_messages = []
    for msg_data in messages_data:
        msg = DealMessage(
            deal_id=deal.id,
            sender_id=msg_data["sender"].id,
            message_text=msg_data["text"],
            is_read=False
        )
        db_session.add(msg)
        created_messages.append(msg)
    
    await db_session.commit()
    for msg in created_messages:
        await db_session.refresh(msg)
    
    # Create access token for buyer
    token = create_access_token(buyer.telegram_id)
    
    # Test WebSocket connection
    client = TestClient(app)
    
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={token}") as websocket:
        # Should receive connection confirmation with last_message_id
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert data["deal_id"] == deal.id
        assert data["user_id"] == buyer.id
        assert "last_message_id" in data
        assert data["last_message_id"] == created_messages[-1].id
        
        # Client requests missed messages (simulating reconnection after message 2)
        websocket.send_json({
            "type": "get_missed_messages",
            "last_message_id": created_messages[1].id  # Request messages after message 2
        })
        
        # Should receive missed messages (messages 3, 4, 5)
        received_messages = []
        for _ in range(3):  # Expecting 3 missed messages
            msg = websocket.receive_json()
            if msg["type"] == "message":
                received_messages.append(msg)
        
        # Should receive sync_complete
        sync_msg = websocket.receive_json()
        assert sync_msg["type"] == "sync_complete"
        assert sync_msg["count"] == 3
        
        # Verify received messages
        assert len(received_messages) == 3
        assert received_messages[0]["message_text"] == "Message 3"
        assert received_messages[1]["message_text"] == "Message 4"
        assert received_messages[2]["message_text"] == "Message 5"


@pytest.mark.asyncio
async def test_websocket_connection_confirmation_includes_last_message_id(db_session):
    """Test that connection confirmation includes last_message_id for sync."""
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
    
    # Test 1: No messages - should return None for last_message_id
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={token}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert data["last_message_id"] is None
    
    # Add a message
    msg = DealMessage(
        deal_id=deal.id,
        sender_id=seller_user.id,
        message_text="Test message",
        is_read=False
    )
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    
    # Test 2: With messages - should return last message ID
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={token}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert data["last_message_id"] == msg.id


@pytest.mark.asyncio
async def test_websocket_get_missed_messages_without_last_id(db_session):
    """Test requesting missed messages without providing last_message_id returns recent messages."""
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
    
    # Add some messages
    for i in range(10):
        msg = DealMessage(
            deal_id=deal.id,
            sender_id=seller_user.id if i % 2 == 0 else buyer.id,
            message_text=f"Message {i+1}",
            is_read=False
        )
        db_session.add(msg)
    
    await db_session.commit()
    
    # Create access token for buyer
    token = create_access_token(buyer.telegram_id)
    
    # Test WebSocket connection
    client = TestClient(app)
    
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={token}") as websocket:
        # Receive connection confirmation
        data = websocket.receive_json()
        assert data["type"] == "connected"
        
        # Request missed messages without last_message_id (should return recent 50)
        websocket.send_json({
            "type": "get_missed_messages"
        })
        
        # Should receive all 10 messages (less than 50 limit)
        received_messages = []
        while True:
            msg = websocket.receive_json()
            if msg["type"] == "sync_complete":
                break
            if msg["type"] == "message":
                received_messages.append(msg)
        
        # Verify we got all messages
        assert len(received_messages) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
