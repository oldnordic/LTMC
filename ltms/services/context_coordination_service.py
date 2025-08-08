"""Context Coordination Service for LTMC multi-agent session management."""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import uuid

from ltms.services.redis_service import RedisConnectionManager, get_redis_manager

logger = logging.getLogger(__name__)


class ContextEventType(Enum):
    """Types of context events for coordination."""
    MEMORY_UPDATE = "memory_update"
    TOOL_EXECUTION = "tool_execution"
    AGENT_JOIN = "agent_join"
    AGENT_LEAVE = "agent_leave"
    RESOURCE_LOCK = "resource_lock"
    RESOURCE_UNLOCK = "resource_unlock"
    SESSION_STATE_CHANGE = "session_state_change"


@dataclass
class ContextEvent:
    """Represents a context coordination event."""
    event_id: str
    session_id: str
    agent_id: str
    event_type: ContextEventType
    timestamp: datetime
    data: Dict[str, Any]
    version: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            'event_id': self.event_id,
            'session_id': self.session_id,
            'agent_id': self.agent_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextEvent':
        """Create from dictionary stored in Redis."""
        return cls(
            event_id=data['event_id'],
            session_id=data['session_id'],
            agent_id=data['agent_id'],
            event_type=ContextEventType(data['event_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            data=data['data'],
            version=data['version']
        )


@dataclass
class SharedContext:
    """Shared context for agent coordination."""
    session_id: str
    participants: Set[str]  # Agent IDs
    shared_memory: Dict[str, Any]
    version: int
    last_updated: datetime
    created_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            'session_id': self.session_id,
            'participants': list(self.participants),
            'shared_memory': self.shared_memory,
            'version': self.version,
            'last_updated': self.last_updated.isoformat(),
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedContext':
        """Create from dictionary stored in Redis."""
        return cls(
            session_id=data['session_id'],
            participants=set(data['participants']),
            shared_memory=data['shared_memory'],
            version=data['version'],
            last_updated=datetime.fromisoformat(data['last_updated']),
            created_at=datetime.fromisoformat(data['created_at']),
            metadata=data['metadata']
        )


class ContextCoordinationService:
    """Service for coordinating shared context between agents."""
    
    def __init__(self, redis_manager: RedisConnectionManager):
        """Initialize context coordination service.
        
        Args:
            redis_manager: Redis connection manager instance
        """
        self.redis_manager = redis_manager
        
        # Redis key prefixes
        self.CONTEXT_PREFIX = "ltmc:context:session:"
        self.EVENTS_PREFIX = "ltmc:context:events:"
        self.LOCKS_PREFIX = "ltmc:context:locks:"
        self.UPDATES_PREFIX = "ltmc:context:updates:"
        self.SUBSCRIBERS_PREFIX = "ltmc:context:subscribers:"
        
        # Configuration
        self.MAX_CONTEXT_VERSIONS = 100
        self.EVENT_RETENTION_HOURS = 24
        self.LOCK_TIMEOUT = 300  # 5 minutes
        self.UPDATE_NOTIFICATION_TTL = 3600  # 1 hour
        
        # Active subscriptions for real-time updates
        self._subscriptions: Dict[str, asyncio.Task] = {}
        self._running = False
    
    async def start(self) -> None:
        """Start the context coordination service."""
        self._running = True
        logger.info("Context Coordination Service started")
    
    async def stop(self) -> None:
        """Stop the context coordination service."""
        self._running = False
        
        # Cancel all subscriptions
        for task in self._subscriptions.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._subscriptions:
            await asyncio.gather(*self._subscriptions.values(), return_exceptions=True)
        
        self._subscriptions.clear()
        logger.info("Context Coordination Service stopped")
    
    async def create_session_context(
        self,
        session_id: str,
        initial_memory: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a new session context.
        
        Args:
            session_id: Unique session identifier
            initial_memory: Initial shared memory data
            metadata: Session metadata
            
        Returns:
            True if created successfully
        """
        try:
            now = datetime.utcnow()
            context = SharedContext(
                session_id=session_id,
                participants=set(),
                shared_memory=initial_memory or {},
                version=1,
                last_updated=now,
                created_at=now,
                metadata=metadata or {}
            )
            
            # Store context
            context_key = f"{self.CONTEXT_PREFIX}{session_id}"
            await self.redis_manager.client.setex(
                context_key,
                86400,  # 24 hours
                json.dumps(context.to_dict())
            )
            
            # Initialize event stream
            events_key = f"{self.EVENTS_PREFIX}{session_id}"
            await self.redis_manager.client.expire(events_key, self.EVENT_RETENTION_HOURS * 3600)
            
            logger.info(f"Session context created: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session context {session_id}: {e}")
            return False
    
    async def join_session(self, session_id: str, agent_id: str) -> bool:
        """Add an agent to a session context.
        
        Args:
            session_id: Session identifier
            agent_id: Agent identifier
            
        Returns:
            True if joined successfully
        """
        try:
            context = await self.get_session_context(session_id)
            if not context:
                # Auto-create session if it doesn't exist
                await self.create_session_context(session_id)
                context = await self.get_session_context(session_id)
                if not context:
                    return False
            
            # Add participant
            context.participants.add(agent_id)
            context.version += 1
            context.last_updated = datetime.utcnow()
            
            # Update context
            await self._store_context(context)
            
            # Publish join event
            await self._publish_event(
                session_id=session_id,
                agent_id=agent_id,
                event_type=ContextEventType.AGENT_JOIN,
                data={'joined_at': datetime.utcnow().isoformat()}
            )
            
            logger.info(f"Agent {agent_id} joined session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to join session {session_id} for agent {agent_id}: {e}")
            return False
    
    async def leave_session(self, session_id: str, agent_id: str) -> bool:
        """Remove an agent from a session context.
        
        Args:
            session_id: Session identifier
            agent_id: Agent identifier
            
        Returns:
            True if left successfully
        """
        try:
            context = await self.get_session_context(session_id)
            if not context or agent_id not in context.participants:
                return False
            
            # Remove participant
            context.participants.discard(agent_id)
            context.version += 1
            context.last_updated = datetime.utcnow()
            
            # Update context
            await self._store_context(context)
            
            # Publish leave event
            await self._publish_event(
                session_id=session_id,
                agent_id=agent_id,
                event_type=ContextEventType.AGENT_LEAVE,
                data={'left_at': datetime.utcnow().isoformat()}
            )
            
            # Clean up if no participants remain
            if not context.participants:
                await self._cleanup_session(session_id)
            
            logger.info(f"Agent {agent_id} left session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to leave session {session_id} for agent {agent_id}: {e}")
            return False
    
    async def update_shared_memory(
        self,
        session_id: str,
        agent_id: str,
        updates: Dict[str, Any],
        merge_strategy: str = "merge"
    ) -> bool:
        """Update shared memory in session context.
        
        Args:
            session_id: Session identifier
            agent_id: Agent making the update
            updates: Data to update
            merge_strategy: How to merge updates ("merge", "replace", "append")
            
        Returns:
            True if updated successfully
        """
        try:
            # Acquire update lock
            lock_acquired = await self._acquire_update_lock(session_id, agent_id)
            if not lock_acquired:
                logger.warning(f"Failed to acquire update lock for session {session_id}")
                return False
            
            try:
                context = await self.get_session_context(session_id)
                if not context or agent_id not in context.participants:
                    return False
                
                # Apply updates based on strategy
                if merge_strategy == "replace":
                    context.shared_memory = updates
                elif merge_strategy == "merge":
                    context.shared_memory.update(updates)
                elif merge_strategy == "append":
                    for key, value in updates.items():
                        if key in context.shared_memory:
                            if isinstance(context.shared_memory[key], list):
                                if isinstance(value, list):
                                    context.shared_memory[key].extend(value)
                                else:
                                    context.shared_memory[key].append(value)
                            else:
                                context.shared_memory[key] = value
                        else:
                            context.shared_memory[key] = value
                
                # Update version and timestamp
                context.version += 1
                context.last_updated = datetime.utcnow()
                
                # Store updated context
                await self._store_context(context)
                
                # Publish memory update event
                await self._publish_event(
                    session_id=session_id,
                    agent_id=agent_id,
                    event_type=ContextEventType.MEMORY_UPDATE,
                    data={
                        'updates': updates,
                        'strategy': merge_strategy,
                        'new_version': context.version
                    }
                )
                
                return True
                
            finally:
                # Always release the lock
                await self._release_update_lock(session_id, agent_id)
            
        except Exception as e:
            logger.error(f"Failed to update shared memory for session {session_id}: {e}")
            return False
    
    async def get_session_context(self, session_id: str) -> Optional[SharedContext]:
        """Get session context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session context or None if not found
        """
        try:
            context_key = f"{self.CONTEXT_PREFIX}{session_id}"
            data = await self.redis_manager.client.get(context_key)
            
            if not data:
                return None
            
            return SharedContext.from_dict(json.loads(data))
            
        except Exception as e:
            logger.error(f"Failed to get session context {session_id}: {e}")
            return None
    
    async def get_session_events(
        self,
        session_id: str,
        since_version: Optional[int] = None,
        event_types: Optional[List[ContextEventType]] = None,
        limit: int = 100
    ) -> List[ContextEvent]:
        """Get events for a session.
        
        Args:
            session_id: Session identifier
            since_version: Only events after this version
            event_types: Filter by event types
            limit: Maximum number of events to return
            
        Returns:
            List of context events
        """
        try:
            events_key = f"{self.EVENTS_PREFIX}{session_id}"
            event_data = await self.redis_manager.client.lrange(events_key, 0, limit - 1)
            
            events = []
            for data in event_data:
                try:
                    event = ContextEvent.from_dict(json.loads(data))
                    
                    # Apply filters
                    if since_version and event.version <= since_version:
                        continue
                    
                    if event_types and event.event_type not in event_types:
                        continue
                    
                    events.append(event)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse event data: {e}")
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get session events for {session_id}: {e}")
            return []
    
    async def subscribe_to_updates(
        self,
        session_id: str,
        agent_id: str,
        callback: callable
    ) -> bool:
        """Subscribe to real-time context updates.
        
        Args:
            session_id: Session identifier
            agent_id: Subscribing agent identifier
            callback: Function to call on updates
            
        Returns:
            True if subscribed successfully
        """
        try:
            subscription_key = f"{session_id}:{agent_id}"
            
            if subscription_key in self._subscriptions:
                # Cancel existing subscription
                self._subscriptions[subscription_key].cancel()
            
            # Start new subscription task
            task = asyncio.create_task(
                self._subscription_loop(session_id, agent_id, callback)
            )
            self._subscriptions[subscription_key] = task
            
            # Add to subscriber list
            subscribers_key = f"{self.SUBSCRIBERS_PREFIX}{session_id}"
            await self.redis_manager.client.sadd(subscribers_key, agent_id)
            await self.redis_manager.client.expire(subscribers_key, self.UPDATE_NOTIFICATION_TTL)
            
            logger.info(f"Agent {agent_id} subscribed to session {session_id} updates")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe agent {agent_id} to session {session_id}: {e}")
            return False
    
    async def unsubscribe_from_updates(self, session_id: str, agent_id: str) -> bool:
        """Unsubscribe from context updates.
        
        Args:
            session_id: Session identifier
            agent_id: Agent identifier
            
        Returns:
            True if unsubscribed successfully
        """
        try:
            subscription_key = f"{session_id}:{agent_id}"
            
            if subscription_key in self._subscriptions:
                self._subscriptions[subscription_key].cancel()
                del self._subscriptions[subscription_key]
            
            # Remove from subscriber list
            subscribers_key = f"{self.SUBSCRIBERS_PREFIX}{session_id}"
            await self.redis_manager.client.srem(subscribers_key, agent_id)
            
            logger.info(f"Agent {agent_id} unsubscribed from session {session_id} updates")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe agent {agent_id} from session {session_id}: {e}")
            return False
    
    async def get_coordination_stats(self) -> Dict[str, Any]:
        """Get context coordination statistics.
        
        Returns:
            Dictionary with coordination statistics
        """
        try:
            stats = {
                'active_sessions': 0,
                'total_participants': 0,
                'active_subscriptions': len(self._subscriptions),
                'session_details': {}
            }
            
            # Count active sessions
            pattern = f"{self.CONTEXT_PREFIX}*"
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                session_id = key.decode().split(':')[-1]
                context = await self.get_session_context(session_id)
                
                if context:
                    stats['active_sessions'] += 1
                    stats['total_participants'] += len(context.participants)
                    
                    stats['session_details'][session_id] = {
                        'participants': len(context.participants),
                        'version': context.version,
                        'last_updated': context.last_updated.isoformat(),
                        'memory_keys': len(context.shared_memory)
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get coordination stats: {e}")
            return {"error": str(e)}
    
    async def _store_context(self, context: SharedContext) -> None:
        """Store context to Redis.
        
        Args:
            context: Context to store
        """
        context_key = f"{self.CONTEXT_PREFIX}{context.session_id}"
        await self.redis_manager.client.setex(
            context_key,
            86400,  # 24 hours
            json.dumps(context.to_dict())
        )
    
    async def _publish_event(
        self,
        session_id: str,
        agent_id: str,
        event_type: ContextEventType,
        data: Dict[str, Any]
    ) -> None:
        """Publish a context event.
        
        Args:
            session_id: Session identifier
            agent_id: Agent identifier
            event_type: Type of event
            data: Event data
        """
        try:
            context = await self.get_session_context(session_id)
            version = context.version if context else 1
            
            event = ContextEvent(
                event_id=str(uuid.uuid4()),
                session_id=session_id,
                agent_id=agent_id,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                data=data,
                version=version
            )
            
            # Store event in session event stream
            events_key = f"{self.EVENTS_PREFIX}{session_id}"
            await self.redis_manager.client.lpush(events_key, json.dumps(event.to_dict()))
            
            # Trim to maintain max events
            await self.redis_manager.client.ltrim(events_key, 0, self.MAX_CONTEXT_VERSIONS - 1)
            
            # Set expiration
            await self.redis_manager.client.expire(events_key, self.EVENT_RETENTION_HOURS * 3600)
            
            # Notify subscribers
            await self._notify_subscribers(session_id, event)
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
    
    async def _notify_subscribers(self, session_id: str, event: ContextEvent) -> None:
        """Notify subscribers of an event.
        
        Args:
            session_id: Session identifier
            event: Context event to notify about
        """
        try:
            # Store notification for polling subscribers
            updates_key = f"{self.UPDATES_PREFIX}{session_id}"
            await self.redis_manager.client.lpush(updates_key, json.dumps(event.to_dict()))
            await self.redis_manager.client.ltrim(updates_key, 0, 99)  # Keep last 100 updates
            await self.redis_manager.client.expire(updates_key, self.UPDATE_NOTIFICATION_TTL)
            
        except Exception as e:
            logger.error(f"Failed to notify subscribers: {e}")
    
    async def _subscription_loop(
        self,
        session_id: str,
        agent_id: str,
        callback: callable
    ) -> None:
        """Background subscription loop for real-time updates.
        
        Args:
            session_id: Session identifier
            agent_id: Agent identifier
            callback: Callback function for updates
        """
        last_processed_version = 0
        
        while self._running:
            try:
                # Get recent updates
                updates_key = f"{self.UPDATES_PREFIX}{session_id}"
                updates = await self.redis_manager.client.lrange(updates_key, 0, -1)
                
                for update_data in reversed(updates):
                    try:
                        event = ContextEvent.from_dict(json.loads(update_data))
                        
                        # Skip events from the same agent
                        if event.agent_id == agent_id:
                            continue
                        
                        # Skip already processed events
                        if event.version <= last_processed_version:
                            continue
                        
                        # Call the callback
                        await callback(event)
                        last_processed_version = event.version
                        
                    except Exception as e:
                        logger.warning(f"Failed to process update in subscription: {e}")
                
                # Sleep before next poll
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in subscription loop: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def _acquire_update_lock(self, session_id: str, agent_id: str) -> bool:
        """Acquire update lock for session.
        
        Args:
            session_id: Session identifier
            agent_id: Agent identifier
            
        Returns:
            True if lock acquired
        """
        try:
            lock_key = f"{self.LOCKS_PREFIX}{session_id}:update"
            lock_value = f"{agent_id}:{datetime.utcnow().isoformat()}"
            
            # Try to acquire lock with timeout
            acquired = await self.redis_manager.client.set(
                lock_key,
                lock_value,
                nx=True,  # Only set if doesn't exist
                ex=self.LOCK_TIMEOUT
            )
            
            return bool(acquired)
            
        except Exception as e:
            logger.error(f"Failed to acquire update lock: {e}")
            return False
    
    async def _release_update_lock(self, session_id: str, agent_id: str) -> None:
        """Release update lock for session.
        
        Args:
            session_id: Session identifier
            agent_id: Agent identifier
        """
        try:
            lock_key = f"{self.LOCKS_PREFIX}{session_id}:update"
            
            # Use Lua script to safely release only if we own the lock
            lua_script = """
            local key = KEYS[1]
            local agent_id = ARGV[1]
            local current_value = redis.call('GET', key)
            if current_value and string.sub(current_value, 1, string.len(agent_id)) == agent_id then
                return redis.call('DEL', key)
            end
            return 0
            """
            
            await self.redis_manager.client.eval(lua_script, 1, lock_key, agent_id)
            
        except Exception as e:
            logger.error(f"Failed to release update lock: {e}")
    
    async def _cleanup_session(self, session_id: str) -> None:
        """Clean up session resources.
        
        Args:
            session_id: Session identifier to clean up
        """
        try:
            # Remove context
            context_key = f"{self.CONTEXT_PREFIX}{session_id}"
            await self.redis_manager.client.delete(context_key)
            
            # Remove events (keep for historical purposes with shorter TTL)
            events_key = f"{self.EVENTS_PREFIX}{session_id}"
            await self.redis_manager.client.expire(events_key, 3600)  # 1 hour
            
            # Remove updates
            updates_key = f"{self.UPDATES_PREFIX}{session_id}"
            await self.redis_manager.client.delete(updates_key)
            
            # Remove locks
            lock_pattern = f"{self.LOCKS_PREFIX}{session_id}:*"
            async for key in self.redis_manager.client.scan_iter(match=lock_pattern):
                await self.redis_manager.client.delete(key)
            
            # Remove subscribers
            subscribers_key = f"{self.SUBSCRIBERS_PREFIX}{session_id}"
            await self.redis_manager.client.delete(subscribers_key)
            
            logger.info(f"Session {session_id} cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")


# Global service instance
_context_coordination_service: Optional[ContextCoordinationService] = None


async def get_context_coordination_service() -> ContextCoordinationService:
    """Get or create context coordination service."""
    global _context_coordination_service
    if not _context_coordination_service:
        redis_manager = await get_redis_manager()
        _context_coordination_service = ContextCoordinationService(redis_manager)
        await _context_coordination_service.start()
    return _context_coordination_service


async def cleanup_context_coordination():
    """Cleanup context coordination service."""
    global _context_coordination_service
    if _context_coordination_service:
        await _context_coordination_service.stop()
        _context_coordination_service = None