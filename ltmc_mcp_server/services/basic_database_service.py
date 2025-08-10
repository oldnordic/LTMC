"""
Basic Database Service - Core SQLite Operations
==============================================

Basic async SQLite operations preserving existing database schema.
Core operations: resources, chat messages, and vector ID management.
"""

import aiosqlite
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from config.settings import LTMCSettings
from models.database_models import Resource, ChatMessage
from models.base_models import PerformanceMetrics
from utils.performance_utils import measure_performance


class BasicDatabaseService:
    """
    Basic async SQLite database service.
    
    Handles core SQLite operations:
    - Resources and ResourceChunks
    - ChatHistory operations
    - Vector ID sequence management
    """
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.db_path = settings.db_path
        
    async def initialize(self) -> None:
        """Initialize database service."""
        self.logger.info(f"Initializing basic database service with path: {self.db_path}")
        
    @measure_performance
    async def store_resource(
        self, 
        file_name: str, 
        resource_type: str, 
        content: str
    ) -> Tuple[int, int]:
        """
        Store resource and return (resource_id, vector_id).
        
        Args:
            file_name: Name of the file/resource
            resource_type: Type of resource (document, code, note)
            content: Content to store
            
        Returns:
            Tuple[int, int]: (resource_id, vector_id)
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Insert resource
            cursor = await db.execute(
                "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
                (file_name, resource_type, datetime.utcnow().isoformat())
            )
            resource_id = cursor.lastrowid
            
            # Get next vector ID
            vector_id = await self._get_next_vector_id(db)
            
            # Insert resource chunk
            await db.execute(
                "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
                (resource_id, content, vector_id)
            )
            
            await db.commit()
            
            self.logger.debug(f"Stored resource {resource_id} with vector {vector_id}")
            return resource_id, vector_id
    
    @measure_performance
    async def get_resources_by_type(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get resources by type.
        
        Args:
            resource_type: Optional filter by resource type
            
        Returns:
            List of resource dictionaries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if resource_type:
                cursor = await db.execute(
                    "SELECT * FROM Resources WHERE type = ? ORDER BY created_at DESC",
                    (resource_type,)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM Resources ORDER BY created_at DESC"
                )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    @measure_performance
    async def log_chat_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_tool: Optional[str] = None
    ) -> int:
        """
        Log chat message to ChatHistory table.
        
        Args:
            conversation_id: Conversation identifier
            role: Message role (user, assistant, system)
            content: Message content
            agent_name: Optional agent name
            metadata: Optional metadata dict
            source_tool: Optional source tool name
            
        Returns:
            int: Message ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor = await db.execute(
                """INSERT INTO ChatHistory 
                   (conversation_id, role, content, timestamp, agent_name, metadata, source_tool) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    conversation_id, 
                    role, 
                    content,
                    datetime.utcnow().isoformat(),
                    agent_name,
                    metadata_json,
                    source_tool
                )
            )
            message_id = cursor.lastrowid
            await db.commit()
            
            self.logger.debug(f"Logged chat message {message_id} for conversation {conversation_id}")
            return message_id
    
    @measure_performance
    async def get_chat_history(
        self, 
        conversation_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum messages to return
            
        Returns:
            List of chat message dictionaries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                """SELECT * FROM ChatHistory 
                   WHERE conversation_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (conversation_id, limit)
            )
            
            rows = await cursor.fetchall()
            messages = []
            
            for row in rows:
                message = dict(row)
                # Parse metadata JSON if present
                if message.get('metadata'):
                    try:
                        message['metadata'] = json.loads(message['metadata'])
                    except json.JSONDecodeError:
                        message['metadata'] = None
                messages.append(message)
            
            return list(reversed(messages))  # Return in chronological order
    
    async def _get_next_vector_id(self, db: aiosqlite.Connection) -> int:
        """Get next available vector ID."""
        cursor = await db.execute("SELECT last_vector_id FROM VectorIdSequence WHERE id = 1")
        row = await cursor.fetchone()
        
        if row:
            next_id = row[0] + 1
        else:
            next_id = 1
        
        await db.execute(
            "UPDATE VectorIdSequence SET last_vector_id = ? WHERE id = 1",
            (next_id,)
        )
        
        return next_id