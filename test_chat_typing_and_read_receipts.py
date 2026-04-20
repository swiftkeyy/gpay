"""Test chat typing indicators and read receipts (Task 10.2)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from datetime import datetime

from api.main import app
from app.models.entities import User, Seller, Deal, DealMessage, Lot, Product, Category, Game, Order
from app.models.enums import DealStatus, SellerStatus, LotStatus, OrderStatus
from api.dependencies.auth import create_access_token


@pytest.fixture
async def setup_deal_with_users(db_session):
    """Create a complete deal setup with buyer and seller."""
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
    
    return {
        "buyer": buyer,
        "seller_user": seller_user,
        "seller": seller,
        "deal": deal
    }


@pytest.mark.asyncio
async def test_typing_indicator_broadcast(db_session, setup_deal_with_users):
    """
    Test Requirement 9.3: Handle typing indicator messages (typing start/stop).
    
    Validates:
    - Typing indicator is sent via WebSocket
    - Typing indicator is broadcast to the other party
    - Both typing start and stop are handled
    """
    data = await setup_deal_with_users
    buyer = data["buyer"]
    seller_user = data["seller_user"]
    deal = data["deal"]
    
    buyer_token = create_access_token(buyer.telegram_id)
    seller_token = create_access_token(seller_user.telegram_id)
    
    client = TestClient(app)
    
    # Connect both buyer and seller
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={buyer_token}") as buyer_ws:
        # Receive connection confirmation for buyer
        buyer_conn = buyer_ws.receive_json()
        assert buyer_conn["type"] == "connected"
        
        with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={seller_token}") as seller_ws:
            # Receive connection confirmation for seller
            seller_conn = seller_ws.receive_json()
            assert seller_conn["type"] == "connected"
            
            # Buyer starts typing
            buyer_ws.send_json({
                "type": "typing",
                "is_typing": True
            })
            
            # Seller should receive typing indicator
            typing_msg = seller_ws.receive_json()
            assert typing_msg["type"] == "typing"
            assert typing_msg["user_id"] == buyer.id
            assert typing_msg["is_typing"] == True
            
            # Buyer stops typing
            buyer_ws.send_json({
                "type": "typing",
                "is_typing": False
            })
            
            # Seller should receive stop typing indicator
            stop_typing_msg = seller_ws.receive_json()
            assert stop_typing_msg["type"] == "typing"
            assert stop_typing_msg["user_id"] == buyer.id
            assert stop_typing_msg["is_typing"] == False


@pytest.mark.asyncio
async def test_read_receipt_individual_message(db_session, setup_deal_with_users):
    """
    Test Requirements 9.4, 9.5, 9.6: Handle read receipt for individual messages.
    
    Validates:
    - Read receipt message is sent via WebSocket (9.4)
    - Message read status is updated in database (9.5)
    - Read receipt is broadcast to sender (9.6)
    """
    data = await setup_deal_with_users
    buyer = data["buyer"]
    seller_user = data["seller_user"]
    deal = data["deal"]
    
    buyer_token = create_access_token(buyer.telegram_id)
    seller_token = create_access_token(seller_user.telegram_id)
    
    client = TestClient(app)
    
    # Connect both buyer and seller
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={buyer_token}") as buyer_ws:
        buyer_ws.receive_json()  # Connection confirmation
        
        with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={seller_token}") as seller_ws:
            seller_ws.receive_json()  # Connection confirmation
            
            # Buyer sends a message
            buyer_ws.send_json({
                "type": "text",
                "message_text": "Hello seller!"
            })
            
            # Buyer receives confirmation
            buyer_msg = buyer_ws.receive_json()
            assert buyer_msg["type"] == "message"
            message_id = buyer_msg["message_id"]
            
            # Seller receives the message
            seller_msg = seller_ws.receive_json()
            assert seller_msg["type"] == "message"
            assert seller_msg["message_id"] == message_id
            assert seller_msg["is_read"] == False
            
            # Seller marks message as read (Requirement 9.4)
            seller_ws.send_json({
                "type": "read",
                "message_id": message_id
            })
            
            # Buyer should receive read receipt (Requirement 9.6)
            read_receipt = buyer_ws.receive_json()
            assert read_receipt["type"] == "read_receipt"
            assert read_receipt["message_id"] == message_id
            assert read_receipt["read_by"] == seller_user.id
            assert "read_at" in read_receipt
            
            # Verify database was updated (Requirement 9.5)
            result = await db_session.execute(
                select(DealMessage).where(DealMessage.id == message_id)
            )
            msg = result.scalar_one()
            assert msg.is_read == True
            assert msg.read_at is not None


@pytest.mark.asyncio
async def test_read_all_messages(db_session, setup_deal_with_users):
    """
    Test read_all functionality for marking multiple messages as read.
    
    Validates:
    - Multiple messages can be marked as read at once
    - Database is updated for all messages
    - Read receipt is broadcast with count
    """
    data = await setup_deal_with_users
    buyer = data["buyer"]
    seller_user = data["seller_user"]
    deal = data["deal"]
    
    buyer_token = create_access_token(buyer.telegram_id)
    seller_token = create_access_token(seller_user.telegram_id)
    
    client = TestClient(app)
    
    # Connect both buyer and seller
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={buyer_token}") as buyer_ws:
        buyer_ws.receive_json()  # Connection confirmation
        
        with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={seller_token}") as seller_ws:
            seller_ws.receive_json()  # Connection confirmation
            
            # Buyer sends multiple messages
            message_ids = []
            for i in range(3):
                buyer_ws.send_json({
                    "type": "text",
                    "message_text": f"Message {i+1}"
                })
                
                # Receive confirmations
                buyer_msg = buyer_ws.receive_json()
                message_ids.append(buyer_msg["message_id"])
                
                seller_msg = seller_ws.receive_json()
                assert seller_msg["is_read"] == False
            
            # Seller marks all messages as read
            seller_ws.send_json({
                "type": "read_all"
            })
            
            # Buyer should receive read_all receipt
            read_all_receipt = buyer_ws.receive_json()
            assert read_all_receipt["type"] == "read_all_receipt"
            assert read_all_receipt["read_by"] == seller_user.id
            assert read_all_receipt["count"] == 3
            assert "read_at" in read_all_receipt
            
            # Verify all messages are marked as read in database
            result = await db_session.execute(
                select(DealMessage).where(
                    DealMessage.id.in_(message_ids)
                )
            )
            messages = result.scalars().all()
            assert len(messages) == 3
            for msg in messages:
                assert msg.is_read == True
                assert msg.read_at is not None


@pytest.mark.asyncio
async def test_cannot_mark_own_messages_as_read(db_session, setup_deal_with_users):
    """
    Test that users cannot mark their own messages as read.
    
    Validates:
    - Only messages from other party can be marked as read
    - Own messages are ignored in read operations
    """
    data = await setup_deal_with_users
    buyer = data["buyer"]
    deal = data["deal"]
    
    buyer_token = create_access_token(buyer.telegram_id)
    
    client = TestClient(app)
    
    with client.websocket_connect(f"/api/v1/ws/chat/{deal.id}?token={buyer_token}") as buyer_ws:
        buyer_ws.receive_json()  # Connection confirmation
        
        # Buyer sends a message
        buyer_ws.send_json({
            "type": "text",
            "message_text": "My own message"
        })
        
        # Receive confirmation
        buyer_msg = buyer_ws.receive_json()
        message_id = buyer_msg["message_id"]
        
        # Buyer tries to mark their own message as read
        buyer_ws.send_json({
            "type": "read",
            "message_id": message_id
        })
        
        # Verify message is still unread in database
        result = await db_session.execute(
            select(DealMessage).where(DealMessage.id == message_id)
        )
        msg = result.scalar_one()
        assert msg.is_read == False
        assert msg.read_at is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
