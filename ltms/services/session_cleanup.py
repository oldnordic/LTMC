"""Session cleanup utilities for LTMC session state service."""

import logging
import asyncio
from datetime import datetime
from typing import Optional

from ltms.services.redis_service import RedisConnectionManager
from ltms.services.session_models import SessionInfo, SessionStatus

logger = logging.getLogger(__name__)


class SessionCleanupManager:
    """Manages session cleanup operations."""
    
    def __init__(self, redis_manager: RedisConnectionManager, session_prefix: str):
        """Initialize cleanup manager.
        
        Args:
            redis_manager: Redis connection manager
            session_prefix: Redis key prefix for sessions
        """
        self.redis_manager = redis_manager
        self.session_prefix = session_prefix
        self.cleanup_interval = 300  # 5 minutes
        
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        logger.info("Session cleanup manager started")
    
    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if not self._running:
            return
        
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Session cleanup manager stopped")
    
    async def cleanup_session_resources(self, session: SessionInfo) -> None:
        """Cleanup resources owned by session.
        
        Args:
            session: Session to cleanup
        """
        if not session.owned_resources:
            return
        
        try:
            # Note: This would integrate with Memory Locking Service
            # For now, just log the resources that should be cleaned up
            logger.info(f"Cleaning up {len(session.owned_resources)} resources for session {session.session_id}")
            
            # Clear owned resources
            session.owned_resources.clear()
            
        except Exception as e:
            logger.error(f"Failed to cleanup resources for session {session.session_id}: {e}")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Background task to cleanup expired sessions."""
        while self._running:
            try:
                current_time = datetime.now()
                expired_sessions = []
                
                # Scan for expired sessions
                async for key in self.redis_manager.client.scan_iter(
                    match=f"{self.session_prefix}*"
                ):
                    session_id = key.decode().replace(self.session_prefix, "")
                    session = await self._get_session(session_id)
                    
                    if session and session.expires_at and session.expires_at < current_time:
                        expired_sessions.append(session_id)
                
                # Cleanup expired sessions
                for session_id in expired_sessions:
                    await self._terminate_expired_session(session_id)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
            except Exception as e:
                logger.error(f"Error in session cleanup task: {e}")
            
            await asyncio.sleep(self.cleanup_interval)
    
    async def _get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session from Redis."""
        try:
            key = f"{self.session_prefix}{session_id}"
            data = await self.redis_manager.client.get(key)
            
            if not data:
                return None
            
            import json
            return SessionInfo.from_dict(json.loads(data))
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def _terminate_expired_session(self, session_id: str) -> None:
        """Terminate an expired session."""
        try:
            session = await self._get_session(session_id)
            if not session:
                return
            
            # Update session status
            session.status = SessionStatus.TERMINATED
            session.last_activity = datetime.now()
            
            # Cleanup resources
            await self.cleanup_session_resources(session)
            
            # Store final state briefly
            import json
            key = f"{self.session_prefix}{session_id}"
            data = json.dumps(session.to_dict())
            await self.redis_manager.client.setex(key, 60, data)  # 1 minute grace period
            
            # Remove from active sessions after delay
            await asyncio.sleep(60)
            await self._delete_session(session_id)
            
            logger.info(f"Terminated expired session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to terminate expired session {session_id}: {e}")
    
    async def _delete_session(self, session_id: str) -> None:
        """Delete session from Redis."""
        keys_to_delete = [
            f"{self.session_prefix}{session_id}",
            f"{self.session_prefix.replace(':active:', ':state:')}{session_id}",
            f"{self.session_prefix.replace(':active:', ':resources:')}{session_id}"
        ]
        
        await self.redis_manager.client.delete(*keys_to_delete)