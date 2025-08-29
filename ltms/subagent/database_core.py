"""
Core Database Operations for Intelligence Tracking
Core database operations for subagent intelligence across SQLite, Neo4j, Redis, and FAISS.

File: ltms/subagent/database_core.py
Lines: ~200 (under 300 limit)
Purpose: Core database operations and session management
"""

import json
import sqlite3
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ..config.json_config_loader import get_config
from ..database.atomic_coordinator import AtomicDatabaseCoordinator

logger = logging.getLogger(__name__)


class CoreIntelligenceDBOperations:
    """
    Core database operations for subagent intelligence tracking.
    
    Handles essential database operations across SQLite (primary), Neo4j, Redis, and FAISS
    with atomic transactions and proper error handling.
    """
    
    def __init__(self):
        self.config = get_config()
        self.db_coordinator = AtomicDatabaseCoordinator()
        self._ensure_intelligence_schema()
    
    def _ensure_intelligence_schema(self):
        """Ensure intelligence tracking tables exist with proper schema."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS subagent_sessions (
                        session_id TEXT PRIMARY KEY,
                        parent_session TEXT,
                        session_type TEXT NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        metadata JSON,
                        total_tools_used INTEGER DEFAULT 0,
                        total_tokens INTEGER DEFAULT 0,
                        success_score REAL DEFAULT 0.0,
                        FOREIGN KEY (parent_session) REFERENCES subagent_sessions(session_id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS subagent_tool_invocations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        arguments JSON,
                        result JSON,
                        timestamp TIMESTAMP NOT NULL,
                        execution_time_ms INTEGER,
                        token_count INTEGER,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        patterns_detected JSON,
                        FOREIGN KEY (session_id) REFERENCES subagent_sessions(session_id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_sessions_type_time 
                    ON subagent_sessions(session_type, start_time);
                    
                    CREATE INDEX IF NOT EXISTS idx_invocations_session_tool 
                    ON subagent_tool_invocations(session_id, tool_name);
                """)
                logger.info("Core intelligence schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize intelligence schema: {e}")
            raise
    
    async def store_session_start(self, session_record: Dict[str, Any]) -> bool:
        """
        Store session start record with atomic transaction.
        
        Args:
            session_record: Complete session record with metadata
            
        Returns:
            bool: Success status
        """
        try:
            # Store in SQLite with atomic transaction
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.execute("""
                    INSERT INTO subagent_sessions 
                    (session_id, parent_session, session_type, start_time, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_record["session_id"],
                    session_record["parent_session"],
                    session_record["session_type"],
                    session_record["start_time"],
                    session_record["metadata"]
                ))
                conn.commit()
            
            # Store across multiple database systems
            await self._store_intelligence_multi_db(session_record)
            
            logger.info(f"Session {session_record['session_id']} stored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store session start: {e}")
            return False
    
    async def store_tool_invocation(self, invocation_record: Dict[str, Any]) -> bool:
        """
        Store tool invocation record with session statistics update.
        
        Args:
            invocation_record: Complete tool invocation record
            
        Returns:
            bool: Success status
        """
        try:
            # Store tool invocation in SQLite
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.execute("""
                    INSERT INTO subagent_tool_invocations 
                    (session_id, tool_name, arguments, timestamp, execution_time_ms,
                     token_count, success, error_message, patterns_detected)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invocation_record["session_id"],
                    invocation_record["tool_name"],
                    invocation_record["arguments"],
                    invocation_record["timestamp"],
                    invocation_record["execution_time_ms"],
                    invocation_record["token_count"],
                    invocation_record["success"],
                    invocation_record["error_message"],
                    invocation_record["patterns_detected"]
                ))
                
                # Update session statistics atomically
                conn.execute("""
                    UPDATE subagent_sessions 
                    SET total_tools_used = total_tools_used + 1,
                        total_tokens = total_tokens + ?
                    WHERE session_id = ?
                """, (invocation_record["token_count"], invocation_record["session_id"]))
                
                conn.commit()
            
            logger.debug(f"Tool invocation stored: {invocation_record['tool_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store tool invocation: {e}")
            return False
    
    async def update_session_end(self, session_id: str, success_score: float) -> bool:
        """
        Update session with end time and success score.
        
        Args:
            session_id: Session identifier
            success_score: Final success score (0.0-1.0)
            
        Returns:
            bool: Success status
        """
        try:
            end_time = datetime.now(timezone.utc).isoformat()
            
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.execute("""
                    UPDATE subagent_sessions 
                    SET end_time = ?, success_score = ?
                    WHERE session_id = ?
                """, (end_time, success_score, session_id))
                conn.commit()
            
            logger.info(f"Session {session_id} updated with success score {success_score}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session end: {e}")
            return False
    
    async def get_session_intelligence(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive intelligence data for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict containing complete session intelligence
        """
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get session information
                session_info = conn.execute("""
                    SELECT * FROM subagent_sessions WHERE session_id = ?
                """, (session_id,)).fetchone()
                
                if not session_info:
                    return {"error": f"Session {session_id} not found"}
                
                # Get all tool invocations
                invocations = conn.execute("""
                    SELECT * FROM subagent_tool_invocations 
                    WHERE session_id = ? ORDER BY timestamp
                """, (session_id,)).fetchall()
                
                # Calculate comprehensive session summary
                session_summary = self._calculate_session_summary(invocations)
                
                return {
                    "session": dict(session_info),
                    "tool_invocations": [dict(inv) for inv in invocations],
                    "summary": session_summary
                }
                
        except Exception as e:
            logger.error(f"Failed to get session intelligence: {e}")
            return {"error": str(e)}
    
    def _calculate_session_summary(self, invocations: List[sqlite3.Row]) -> Dict[str, Any]:
        """Calculate comprehensive session summary statistics."""
        if not invocations:
            return {
                "total_tools": 0,
                "unique_tools": 0,
                "success_rate": 0,
                "total_execution_time": 0,
                "total_tokens": 0
            }
        
        return {
            "total_tools": len(invocations),
            "unique_tools": len(set(inv['tool_name'] for inv in invocations)),
            "success_rate": sum(1 for inv in invocations if inv['success']) / len(invocations),
            "total_execution_time": sum(inv['execution_time_ms'] or 0 for inv in invocations),
            "total_tokens": sum(inv['token_count'] or 0 for inv in invocations),
            "average_execution_time": sum(inv['execution_time_ms'] or 0 for inv in invocations) / len(invocations)
        }
    
    async def _store_intelligence_multi_db(self, record: Dict[str, Any]):
        """Store intelligence record across multiple database systems."""
        try:
            # Neo4j: Store relationship mappings for session hierarchy
            await self.db_coordinator.store_neo4j_intelligence(record)
            
            # Redis: Cache active session data for real-time access
            await self.db_coordinator.cache_redis_intelligence(record)
            
            # FAISS: Create vector embeddings for similarity search
            if record.get('arguments') or record.get('metadata'):
                await self.db_coordinator.store_faiss_intelligence(record)
                
        except Exception as e:
            logger.warning(f"Multi-DB intelligence storage warning: {e}")
            # Continue operation - SQLite is the primary storage system