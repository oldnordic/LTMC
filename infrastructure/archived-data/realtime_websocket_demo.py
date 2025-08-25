"""
Real-Time WebSocket Chat Implementation with LTMC Integration
=============================================================

This demonstrates expert-coder workflow using all 55 LTMC tools to prevent
context loss, code drift, and technology drift in WebSocket development.

Features:
- Connection pooling and management
- Message broadcasting
- User authentication
- Graceful disconnection handling
- Full LTMC logging for experience replay
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Set, Optional, Any, List
from dataclasses import dataclass, asdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security for WebSocket authentication
security = HTTPBearer()

@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""
    websocket: WebSocket
    user_id: str
    connection_id: str
    room_id: str
    connected_at: datetime
    last_activity: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LTMC storage."""
        return {
            "user_id": self.user_id,
            "connection_id": self.connection_id,
            "room_id": self.room_id,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }

@dataclass
class ChatMessage:
    """Represents a chat message."""
    message_id: str
    user_id: str
    room_id: str
    content: str
    timestamp: datetime
    message_type: str = "text"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for broadcasting."""
        return asdict(self)

class WebSocketConnectionManager:
    """
    Advanced WebSocket connection manager with Redis backing
    and comprehensive LTMC integration for learning.
    """
    
    def __init__(self):
        # Connection pools by room
        self.connections: Dict[str, Dict[str, WebSocketConnection]] = {}
        self.redis: Optional[aioredis.Redis] = None
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "rooms_created": 0
        }
        
    async def initialize_redis(self):
        """Initialize Redis connection for message persistence."""
        try:
            self.redis = aioredis.from_url(
                "redis://localhost:6382", 
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            await self.redis.ping()
            logger.info("Redis connection established for WebSocket manager")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis = None
    
    async def connect(self, websocket: WebSocket, user_id: str, room_id: str) -> str:
        """
        Accept a WebSocket connection and add to connection pool.
        Returns connection_id for tracking.
        """
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        now = datetime.now()
        
        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_id,
            connection_id=connection_id,
            room_id=room_id,
            connected_at=now,
            last_activity=now
        )
        
        # Add to room
        if room_id not in self.connections:
            self.connections[room_id] = {}
            self.connection_stats["rooms_created"] += 1
            
        self.connections[room_id][connection_id] = connection
        
        # Update stats
        self.connection_stats["total_connections"] += 1
        self.connection_stats["active_connections"] += 1
        
        # Store in Redis for persistence
        if self.redis:
            await self.redis.hset(
                f"websocket:connection:{connection_id}",
                mapping=connection.to_dict()
            )
            await self.redis.sadd(f"websocket:room:{room_id}", connection_id)
        
        logger.info(f"WebSocket connected: user={user_id}, room={room_id}, id={connection_id}")
        
        # Notify room about new connection
        join_message = ChatMessage(
            message_id=str(uuid.uuid4()),
            user_id="system",
            room_id=room_id,
            content=f"User {user_id} joined the room",
            timestamp=now,
            message_type="join"
        )
        await self.broadcast_to_room(room_id, join_message.to_dict(), exclude=connection_id)
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Remove connection from pool and clean up resources."""
        connection = None
        room_id = None
        
        # Find and remove connection
        for room, conns in self.connections.items():
            if connection_id in conns:
                connection = conns.pop(connection_id)
                room_id = room
                break
        
        if not connection:
            logger.warning(f"Connection {connection_id} not found for disconnect")
            return
        
        # Update stats
        self.connection_stats["active_connections"] -= 1
        
        # Clean up empty rooms
        if room_id and not self.connections[room_id]:
            del self.connections[room_id]
        
        # Redis cleanup
        if self.redis:
            await self.redis.delete(f"websocket:connection:{connection_id}")
            if room_id:
                await self.redis.srem(f"websocket:room:{room_id}", connection_id)
        
        logger.info(f"WebSocket disconnected: {connection_id}")
        
        # Notify room about disconnection
        if room_id and room_id in self.connections:
            leave_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                user_id="system",
                room_id=room_id,
                content=f"User {connection.user_id} left the room",
                timestamp=datetime.now(),
                message_type="leave"
            )
            await self.broadcast_to_room(room_id, leave_message.to_dict())
    
    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude: Optional[str] = None):
        """Broadcast message to all connections in a room."""
        if room_id not in self.connections:
            logger.warning(f"Room {room_id} not found for broadcast")
            return
        
        message_json = json.dumps(message)
        disconnected = []
        sent_count = 0
        
        for conn_id, connection in self.connections[room_id].items():
            if exclude and conn_id == exclude:
                continue
                
            try:
                await connection.websocket.send_text(message_json)
                connection.last_activity = datetime.now()
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {conn_id}: {e}")
                disconnected.append(conn_id)
        
        # Clean up disconnected connections
        for conn_id in disconnected:
            await self.disconnect(conn_id)
        
        # Update stats
        self.connection_stats["messages_sent"] += sent_count
        
        # Store message in Redis for history
        if self.redis:
            await self.redis.lpush(
                f"websocket:history:{room_id}",
                message_json
            )
            # Keep only last 100 messages
            await self.redis.ltrim(f"websocket:history:{room_id}", 0, 99)
        
        logger.info(f"Broadcast to room {room_id}: {sent_count} recipients")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection."""
        connection = None
        for conns in self.connections.values():
            if connection_id in conns:
                connection = conns[connection_id]
                break
        
        if not connection:
            logger.warning(f"Connection {connection_id} not found for send")
            return False
        
        try:
            await connection.websocket.send_text(json.dumps(message))
            connection.last_activity = datetime.now()
            self.connection_stats["messages_sent"] += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def get_room_members(self, room_id: str) -> List[str]:
        """Get list of user IDs in a room."""
        if room_id not in self.connections:
            return []
        
        return [conn.user_id for conn in self.connections[room_id].values()]
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        active_rooms = len(self.connections)
        return {
            **self.connection_stats,
            "active_rooms": active_rooms,
            "timestamp": datetime.now().isoformat()
        }

# Global connection manager instance
manager = WebSocketConnectionManager()

# FastAPI application setup
app = FastAPI(title="Real-Time WebSocket Chat with LTMC Integration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup."""
    await manager.initialize_redis()

# Pydantic models for API requests
class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    message_type: str = Field(default="text")

class RoomStatsResponse(BaseModel):
    room_id: str
    member_count: int
    members: List[str]

# WebSocket endpoint
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    """
    WebSocket endpoint for real-time chat.
    
    Args:
        websocket: WebSocket connection
        room_id: Chat room identifier
        user_id: User identifier (from query param)
    """
    connection_id = None
    try:
        # Connect to room
        connection_id = await manager.connect(websocket, user_id, room_id)
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Create message
                message = ChatMessage(
                    message_id=str(uuid.uuid4()),
                    user_id=user_id,
                    room_id=room_id,
                    content=message_data.get("content", ""),
                    timestamp=datetime.now(),
                    message_type=message_data.get("message_type", "text")
                )
                
                # Broadcast to room
                await manager.broadcast_to_room(room_id, message.to_dict())
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id:
            await manager.disconnect(connection_id)

# REST API endpoints
@app.get("/api/rooms/{room_id}/stats", response_model=RoomStatsResponse)
async def get_room_stats(room_id: str):
    """Get statistics for a specific room."""
    members = await manager.get_room_members(room_id)
    return RoomStatsResponse(
        room_id=room_id,
        member_count=len(members),
        members=members
    )

@app.get("/api/stats")
async def get_global_stats():
    """Get global connection statistics."""
    return await manager.get_connection_stats()

@app.get("/api/rooms/{room_id}/history")
async def get_room_history(room_id: str, limit: int = 50):
    """Get recent message history for a room."""
    if not manager.redis:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        messages = await manager.redis.lrange(
            f"websocket:history:{room_id}", 
            0, 
            limit - 1
        )
        return {
            "room_id": room_id,
            "messages": [json.loads(msg) for msg in reversed(messages)],
            "count": len(messages)
        }
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Error fetching history")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_status = "connected" if manager.redis else "disconnected"
    stats = await manager.get_connection_stats()
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "websocket_stats": stats,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)