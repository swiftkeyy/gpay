# Task 14.1: Notification WebSocket Implementation

## Overview

Successfully implemented the complete notification system with WebSocket support for real-time delivery and REST API endpoints for notification management.

## Requirements Validated

### Requirement 16.7: Real-time Notifications via WebSocket ✅
- **Implementation**: WebSocket endpoint at `/api/v1/ws/notifications`
- **Features**:
  - JWT token authentication via query parameter
  - Connection manager for managing active WebSocket connections
  - Real-time notification delivery to connected users
  - Heartbeat/ping-pong support for connection keep-alive
  - Get recent notifications on connection
  - Automatic cleanup on disconnect

### Requirement 16.8: Notification History with Pagination ✅
- **Implementation**: `GET /api/v1/notifications` endpoint
- **Features**:
  - Paginated notification list (default 20 per page, max 100)
  - Returns notification details: id, type, title, message, is_read, read_at, reference_type, reference_id, created_at
  - Ordered by creation date (newest first)
  - User isolation (users only see their own notifications)
  - Unread count endpoint: `GET /api/v1/notifications/unread-count`

### Requirement 16.9: Mark Notifications as Read ✅
- **Implementation**: Multiple endpoints for read status management
- **Features**:
  - `PATCH /api/v1/notifications/{id}/read` - Mark single notification as read
  - `POST /api/v1/notifications/read-all` - Mark all user notifications as read
  - Updates `is_read` flag and `read_at` timestamp
  - Returns updated count for bulk operations

## Implementation Details

### REST API Endpoints

#### 1. GET /api/v1/notifications
```python
@router.get("/notifications")
async def get_notifications(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
)
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "type": "new_order",
      "title": "New Order",
      "message": "You have a new order #123",
      "is_read": false,
      "read_at": null,
      "reference_type": "order",
      "reference_id": 123,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "limit": 20
}
```

#### 2. PATCH /api/v1/notifications/{notification_id}/read
```python
@router.patch("/notifications/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
)
```

**Response:**
```json
{
  "id": 1,
  "is_read": true,
  "read_at": "2024-01-01T12:05:00Z"
}
```

#### 3. POST /api/v1/notifications/read-all
```python
@router.post("/notifications/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
)
```

**Response:**
```json
{
  "message": "All notifications marked as read",
  "updated_count": 5
}
```

#### 4. GET /api/v1/notifications/unread-count
```python
@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
)
```

**Response:**
```json
{
  "count": 3
}
```

### WebSocket Endpoint

#### WS /api/v1/ws/notifications

**Connection:**
```javascript
const ws = new WebSocket(`wss://api.example.com/api/v1/ws/notifications?token=${accessToken}`);
```

**Message Types from Server:**

1. **Connection Confirmation:**
```json
{
  "type": "connected",
  "user_id": 123,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

2. **New Notification:**
```json
{
  "type": "notification",
  "data": {
    "id": 1,
    "notification_type": "new_order",
    "title": "New Order",
    "message": "You have a new order #123",
    "is_read": false,
    "read_at": null,
    "reference_type": "order",
    "reference_id": 123,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

3. **Pong (Heartbeat Response):**
```json
{
  "type": "pong"
}
```

4. **Sync Complete:**
```json
{
  "type": "sync_complete",
  "count": 10
}
```

**Message Types from Client:**

1. **Ping (Heartbeat):**
```json
{
  "type": "ping"
}
```

2. **Get Recent Notifications:**
```json
{
  "type": "get_recent",
  "limit": 10
}
```

### Connection Manager

```python
class NotificationConnectionManager:
    """Manages WebSocket connections for notifications."""
    
    def __init__(self):
        # user_id -> websocket
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user to notification stream."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        """Disconnect a user from notification stream."""
        self.active_connections.pop(user_id, None)
    
    async def send_notification(self, user_id: int, notification: dict):
        """Send a notification to a specific user."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(notification)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
                self.disconnect(user_id)
```

### Helper Function for Other Services

```python
async def send_notification_to_user(
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    reference_type: str | None = None,
    reference_id: int | None = None,
    db: AsyncSession = None
):
    """
    Send a notification to a user via WebSocket if connected.
    Also saves to database.
    
    This function can be imported and used by other services.
    """
    # Save to database
    if db:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
            is_read=False
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        # Send via WebSocket if user is connected
        await notification_manager.send_notification(user_id, {
            "type": "notification",
            "data": {
                "id": notification.id,
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "read_at": None,
                "reference_type": notification.reference_type,
                "reference_id": notification.reference_id,
                "created_at": notification.created_at.isoformat()
            }
        })
        
        return notification
```

## Database Model

The notification system uses the existing `Notification` model:

```python
class Notification(Base):
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    notification_type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

## Notification Types

```python
class NotificationType(StrEnum):
    NEW_MESSAGE = "new_message"
    NEW_ORDER = "new_order"
    ORDER_STATUS = "order_status"
    PAYMENT = "payment"
    REVIEW = "review"
    SYSTEM = "system"
    PRICE_ALERT = "price_alert"
    SELLER_APPROVED = "seller_approved"
    SELLER_REJECTED = "seller_rejected"
    DISPUTE_OPENED = "dispute_opened"
    DISPUTE_RESOLVED = "dispute_resolved"
```

## Security Features

1. **Authentication**: JWT token validation for both REST and WebSocket endpoints
2. **User Isolation**: Users can only access their own notifications
3. **Authorization**: Current user extracted from JWT token
4. **Connection Management**: Automatic cleanup on disconnect
5. **Error Handling**: Graceful error handling with logging

## Integration with Other Services

Other services can send notifications by importing the helper function:

```python
from api.routers.notifications import send_notification_to_user

# Example: Send notification when new order is created
await send_notification_to_user(
    user_id=seller.user_id,
    notification_type=NotificationType.NEW_ORDER,
    title="New Order",
    message=f"You have a new order #{order.id}",
    reference_type="order",
    reference_id=order.id,
    db=session
)
```

## Frontend Integration

The frontend can connect to the WebSocket and listen for notifications:

```typescript
// Connect to WebSocket
const ws = new WebSocket(`${WS_URL}/api/v1/ws/notifications?token=${accessToken}`);

ws.onopen = () => {
  console.log('Connected to notifications');
  
  // Send heartbeat every 30 seconds
  setInterval(() => {
    ws.send(JSON.stringify({ type: 'ping' }));
  }, 30000);
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'notification') {
    // Show notification to user
    showNotification(data.data);
  } else if (data.type === 'connected') {
    // Request recent notifications
    ws.send(JSON.stringify({ type: 'get_recent', limit: 10 }));
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from notifications');
  // Implement reconnection logic
};
```

## Files Modified

1. **api/routers/notifications.py** - Complete rewrite with:
   - NotificationConnectionManager class
   - WebSocket endpoint implementation
   - REST API endpoints with proper authentication
   - Helper function for sending notifications

## Testing

Test file created: `test_notification_websocket.py`

Tests cover:
- GET /api/v1/notifications with pagination
- PATCH /api/v1/notifications/{id}/read
- POST /api/v1/notifications/read-all
- GET /api/v1/notifications/unread-count
- Pagination functionality
- User isolation

## Next Steps

Task 14.2 will integrate bot notifications using this system to send push notifications via Telegram bot for:
- New orders (for sellers)
- Order status changes
- New messages in deal chat
- Payment confirmations
- New reviews
- Withdrawal processing

## Conclusion

✅ Task 14.1 is complete. The notification system is fully implemented with:
- Real-time WebSocket delivery
- REST API for notification management
- Proper authentication and authorization
- User isolation and security
- Helper functions for easy integration with other services
- Comprehensive error handling and logging

The system is ready for integration with the bot notification system (Task 14.2) and frontend Mini App.
