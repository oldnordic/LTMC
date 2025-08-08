"""Core Session State Manager Service for LTMC multi-agent orchestration."""

import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import uuid

from ltms.services.redis_service import RedisConnectionManager, get_redis_manager
from ltms.services.session_models import SessionInfo, SessionStatus
from ltms.services.session_cleanup import SessionCleanupManager

logger = logging.getLogger(__name__)


class SessionStateService:
    """Core service for session lifecycle and state management."""
    
    def __init__(self, redis_manager: RedisConnectionManager):
        self.redis_manager = redis_manager
        self.SESSIONS_ACTIVE_PREFIX = "ltmc:sessions:active:"
        self.SESSIONS_STATE_PREFIX = "ltmc:sessions:state:"
        self.SESSIONS_RESOURCES_PREFIX = "ltmc:sessions:resources:"
        self.SESSION_TIMEOUT = 3600
        self.MAX_SESSIONS_PER_AGENT = 10
        self._cleanup_manager = SessionCleanupManager(
            redis_manager, self.SESSIONS_ACTIVE_PREFIX
        )
        self._running = False
    
    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        await self._cleanup_manager.start_cleanup_task()
        logger.info("Session state service started")
    
    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        await self._cleanup_manager.stop_cleanup_task()
        logger.info("Session state service stopped")
    
    async def create_session(
        self,
        session_id: Optional[str] = None,
        participants: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionInfo:
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            participants_set = set(participants or [])
            timeout = timeout or self.SESSION_TIMEOUT
            now = datetime.now()
            
            for agent_id in participants_set:
                if len(await self.get_agent_sessions(agent_id)) >= self.MAX_SESSIONS_PER_AGENT:
                    raise ValueError(f"Agent {agent_id} has reached maximum session limit")
            
            session = SessionInfo(
                session_id=session_id,
                status=SessionStatus.ACTIVE,
                participants=participants_set,
                created_at=now,
                last_activity=now,
                expires_at=now + timedelta(seconds=timeout),
                persistent_state={},
                owned_resources=set(),
                metadata=metadata or {},
                checkpoints=[]
            )
            
            await self._store_session(session)
            logger.info(f"Created session {session_id} with {len(participants_set)} participants")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        try:
            key = f"{self.SESSIONS_ACTIVE_PREFIX}{session_id}"
            data = await self.redis_manager.client.get(key)
            
            if not data:
                return None
            
            return SessionInfo.from_dict(json.loads(data))
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session_state(
        self,
        session_id: str,
        state_updates: Dict[str, Any]
    ) -> bool:
        try:
            session = await self.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for state update")
                return False
            
            session.persistent_state.update(state_updates)
            session.last_activity = datetime.now()
            await self._store_session(session)
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session state {session_id}: {e}")
            return False
    
    async def add_session_participant(self, session_id: str, agent_id: str) -> bool:
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            if len(await self.get_agent_sessions(agent_id)) >= self.MAX_SESSIONS_PER_AGENT:
                raise ValueError(f"Agent {agent_id} has reached maximum session limit")
            
            session.participants.add(agent_id)
            session.last_activity = datetime.now()
            
            await self._store_session(session)
            
            logger.info(f"Added participant {agent_id} to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add participant {agent_id} to session {session_id}: {e}")
            return False
    
    async def remove_session_participant(self, session_id: str, agent_id: str) -> bool:
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            session.participants.discard(agent_id)
            session.last_activity = datetime.now()
            
            if not session.participants:
                await self.terminate_session(session_id)
                return True
            
            await self._store_session(session)
            
            logger.info(f"Removed participant {agent_id} from session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove participant {agent_id} from session {session_id}: {e}")
            return False
    
    async def terminate_session(self, session_id: str, cleanup_resources: bool = True) -> bool:
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            session.status = SessionStatus.TERMINATED
            session.last_activity = datetime.now()
            if cleanup_resources:
                await self._cleanup_manager.cleanup_session_resources(session)
            await self._store_session(session)
            import asyncio
            asyncio.create_task(self._delayed_delete_session(session_id, 60))
            
            logger.info(f"Terminated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate session {session_id}: {e}")
            return False
    
    async def get_agent_sessions(self, agent_id: str) -> List[str]:
        try:
            sessions = []
            
            async for key in self.redis_manager.client.scan_iter(
                match=f"{self.SESSIONS_ACTIVE_PREFIX}*"
            ):
                session_id = key.decode().replace(self.SESSIONS_ACTIVE_PREFIX, "")
                session = await self.get_session(session_id)
                if session and agent_id in session.participants:
                    sessions.append(session_id)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get agent sessions for {agent_id}: {e}")
            return []
    
    async def get_session_stats(self) -> Dict[str, Any]:
        try:
            active_count = 0
            total_participants = 0
            
            async for key in self.redis_manager.client.scan_iter(
                match=f"{self.SESSIONS_ACTIVE_PREFIX}*"
            ):
                active_count += 1
                session_id = key.decode().replace(self.SESSIONS_ACTIVE_PREFIX, "")
                session = await self.get_session(session_id)
                if session:
                    total_participants += len(session.participants)
            
            return {
                'active_sessions': active_count,
                'total_participants': total_participants
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
    
    async def _store_session(self, session: SessionInfo) -> None:
        key = f"{self.SESSIONS_ACTIVE_PREFIX}{session.session_id}"
        data = json.dumps(session.to_dict())
        
        ttl = int((session.expires_at - datetime.now()).total_seconds()) if session.expires_at else self.SESSION_TIMEOUT
        await self.redis_manager.client.setex(key, ttl, data)
    
    async def _delayed_delete_session(self, session_id: str, delay: int) -> None:
        import asyncio
        await asyncio.sleep(delay)
        
        keys_to_delete = [
            f"{self.SESSIONS_ACTIVE_PREFIX}{session_id}",
            f"{self.SESSIONS_STATE_PREFIX}{session_id}",
            f"{self.SESSIONS_RESOURCES_PREFIX}{session_id}"
        ]
        
        await self.redis_manager.client.delete(*keys_to_delete)


# Global service instance
_session_state_service: Optional[SessionStateService] = None


async def get_session_state_service() -> SessionStateService:
    """Get or create session state service."""
    global _session_state_service
    if not _session_state_service:
        redis_manager = await get_redis_manager()
        _session_state_service = SessionStateService(redis_manager)
        await _session_state_service.start()
    return _session_state_service


async def cleanup_session_state_service():
    """Cleanup session state service on shutdown."""
    global _session_state_service
    if _session_state_service:
        await _session_state_service.stop()
        _session_state_service = None
    logger.info("Session state service cleanup completed")