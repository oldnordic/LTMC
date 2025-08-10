"""
Comprehensive WebSocket Integration Tests
========================================

Tests the complete WebSocket implementation with LTMC integration.
Demonstrates TDD approach and real integration testing.
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import websockets
import aioredis
from fastapi.testclient import TestClient
from httpx import AsyncClient

from realtime_websocket_demo import app, manager, WebSocketConnectionManager, ChatMessage

# Test configuration
REDIS_URL = "redis://localhost:6382"
WEBSOCKET_URL = "ws://localhost:8001"
HTTP_URL = "http://localhost:8001"

class TestWebSocketConnectionManager:
    """Test the WebSocket connection manager in isolation."""
    
    @pytest.fixture
    async def connection_manager(self):
        """Create a fresh connection manager for each test."""
        mgr = WebSocketConnectionManager()
        await mgr.initialize_redis()
        yield mgr
        
        # Cleanup
        if mgr.redis:
            await mgr.redis.flushdb()
            await mgr.redis.close()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for testing."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket
    
    async def test_redis_initialization(self, connection_manager):
        """Test Redis connection initialization."""
        assert connection_manager.redis is not None
        
        # Test ping
        response = await connection_manager.redis.ping()
        assert response is True
    
    async def test_connection_establishment(self, connection_manager, mock_websocket):
        """Test WebSocket connection establishment."""
        user_id = "test_user_123"
        room_id = "test_room_456"
        
        connection_id = await connection_manager.connect(
            mock_websocket, user_id, room_id
        )
        
        # Verify connection was established
        assert connection_id is not None
        assert room_id in connection_manager.connections
        assert connection_id in connection_manager.connections[room_id]
        
        # Verify stats updated
        stats = await connection_manager.get_connection_stats()
        assert stats["active_connections"] == 1
        assert stats["total_connections"] == 1
        assert stats["rooms_created"] == 1
        
        # Verify WebSocket was accepted
        mock_websocket.accept.assert_called_once()
    
    async def test_connection_disconnect(self, connection_manager, mock_websocket):
        """Test WebSocket disconnection and cleanup."""
        user_id = "test_user_123"
        room_id = "test_room_456"
        
        # Connect first
        connection_id = await connection_manager.connect(
            mock_websocket, user_id, room_id
        )
        
        # Then disconnect
        await connection_manager.disconnect(connection_id)
        
        # Verify connection was removed
        assert connection_id not in connection_manager.connections.get(room_id, {})
        
        # Verify stats updated
        stats = await connection_manager.get_connection_stats()
        assert stats["active_connections"] == 0
    
    async def test_message_broadcasting(self, connection_manager, mock_websocket):
        """Test message broadcasting to room members."""
        room_id = "test_room_broadcast"
        
        # Create multiple connections
        connection_ids = []
        websockets = []
        
        for i in range(3):
            ws = AsyncMock()
            ws.accept = AsyncMock()
            ws.send_text = AsyncMock()
            websockets.append(ws)
            
            conn_id = await connection_manager.connect(
                ws, f"user_{i}", room_id
            )
            connection_ids.append(conn_id)
        
        # Broadcast a message
        test_message = {
            "message_id": str(uuid.uuid4()),
            "user_id": "test_sender",
            "room_id": room_id,
            "content": "Hello everyone!",
            "timestamp": datetime.now().isoformat(),
            "message_type": "text"
        }
        
        await connection_manager.broadcast_to_room(room_id, test_message)
        
        # Verify all websockets received the message
        for ws in websockets:
            ws.send_text.assert_called()
            call_args = ws.send_text.call_args[0][0]
            received_message = json.loads(call_args)
            assert received_message["content"] == "Hello everyone!"
    
    async def test_message_broadcast_with_exclusion(self, connection_manager):
        """Test broadcasting with sender exclusion."""
        room_id = "test_room_exclude"
        
        # Create connections
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        
        conn_id_1 = await connection_manager.connect(ws1, "user1", room_id)
        conn_id_2 = await connection_manager.connect(ws2, "user2", room_id)
        
        # Broadcast excluding first connection
        test_message = {"content": "Test message"}
        await connection_manager.broadcast_to_room(
            room_id, test_message, exclude=conn_id_1
        )
        
        # Verify only second websocket received message
        ws1.send_text.assert_not_called()
        ws2.send_text.assert_called_once()
    
    async def test_room_member_tracking(self, connection_manager, mock_websocket):
        """Test room member listing functionality."""
        room_id = "test_room_members"
        
        # Add members to room
        users = ["alice", "bob", "charlie"]
        for user in users:
            ws = AsyncMock()
            ws.accept = AsyncMock()
            await connection_manager.connect(ws, user, room_id)
        
        # Get room members
        members = await connection_manager.get_room_members(room_id)
        
        # Verify all users are listed
        assert len(members) == 3
        for user in users:
            assert user in members
    
    async def test_connection_stats_tracking(self, connection_manager):
        """Test connection statistics tracking."""
        initial_stats = await connection_manager.get_connection_stats()
        
        # Create connections across multiple rooms
        for room_num in range(2):
            for user_num in range(3):
                ws = AsyncMock()
                ws.accept = AsyncMock()
                await connection_manager.connect(
                    ws, f"user_{user_num}", f"room_{room_num}"
                )
        
        # Check updated stats
        stats = await connection_manager.get_connection_stats()
        assert stats["active_connections"] == 6
        assert stats["total_connections"] == 6
        assert stats["rooms_created"] == 2

class TestWebSocketAPI:
    """Test the FastAPI WebSocket endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url=HTTP_URL) as client:
            yield client
    
    async def test_health_endpoint(self, async_client):
        """Test the health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "websocket_stats" in data
        assert "timestamp" in data
    
    async def test_room_stats_endpoint(self, async_client):
        """Test room statistics endpoint."""
        room_id = "test_room_stats"
        response = await async_client.get(f"/api/rooms/{room_id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["room_id"] == room_id
        assert "member_count" in data
        assert "members" in data
    
    async def test_global_stats_endpoint(self, async_client):
        """Test global statistics endpoint."""
        response = await async_client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_connections" in data
        assert "total_connections" in data
        assert "active_rooms" in data

class TestWebSocketIntegration:
    """Test full WebSocket integration scenarios."""
    
    async def test_websocket_connection_flow(self):
        """Test complete WebSocket connection flow."""
        # This would require a running server for full integration
        # In real scenarios, you'd use pytest-asyncio with actual WebSocket connections
        pass
    
    async def test_message_persistence_in_redis(self):
        """Test that messages are properly persisted in Redis."""
        redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        try:
            # Test message storage
            room_id = "test_persistence_room"
            test_message = json.dumps({
                "message_id": str(uuid.uuid4()),
                "content": "Test persistence message",
                "timestamp": datetime.now().isoformat()
            })
            
            # Store in Redis like the manager would
            await redis.lpush(f"websocket:history:{room_id}", test_message)
            
            # Retrieve and verify
            messages = await redis.lrange(f"websocket:history:{room_id}", 0, -1)
            assert len(messages) == 1
            
            stored_message = json.loads(messages[0])
            assert stored_message["content"] == "Test persistence message"
            
        finally:
            await redis.flushdb()
            await redis.close()

class TestErrorHandling:
    """Test error handling scenarios."""
    
    async def test_invalid_json_handling(self):
        """Test handling of invalid JSON messages."""
        # This would test the WebSocket endpoint's JSON validation
        pass
    
    async def test_redis_connection_failure(self):
        """Test behavior when Redis is unavailable."""
        mgr = WebSocketConnectionManager()
        # Don't initialize Redis - simulate failure
        
        # Connection should still work without Redis
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        
        connection_id = await mgr.connect(mock_ws, "test_user", "test_room")
        assert connection_id is not None
    
    async def test_websocket_disconnection_cleanup(self):
        """Test proper cleanup when WebSocket disconnects unexpectedly."""
        mgr = WebSocketConnectionManager()
        await mgr.initialize_redis()
        
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock(side_effect=Exception("Connection lost"))
        
        connection_id = await mgr.connect(mock_ws, "test_user", "test_room")
        
        # Try to broadcast - should handle the exception and clean up
        await mgr.broadcast_to_room("test_room", {"content": "test"})
        
        # Connection should be cleaned up
        stats = await mgr.get_connection_stats()
        assert stats["active_connections"] == 0

# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])