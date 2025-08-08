"""Memory Locking Service for LTMC concurrent access safety."""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib

from ltms.services.redis_service import RedisConnectionManager, get_redis_manager

logger = logging.getLogger(__name__)


class LockType(Enum):
    """Types of locks for different resource access patterns."""
    READ = "read"          # Shared read lock
    WRITE = "write"        # Exclusive write lock
    EXCLUSIVE = "exclusive" # Exclusive access (read + write)


class LockPriority(Enum):
    """Lock priority levels for queue management."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class LockRequest:
    """Represents a lock acquisition request."""
    request_id: str
    agent_id: str
    resource_id: str
    lock_type: LockType
    priority: LockPriority
    requested_at: datetime
    timeout: int  # seconds
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            'request_id': self.request_id,
            'agent_id': self.agent_id,
            'resource_id': self.resource_id,
            'lock_type': self.lock_type.value,
            'priority': self.priority.value,
            'requested_at': self.requested_at.isoformat(),
            'timeout': self.timeout,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LockRequest':
        """Create from dictionary stored in Redis."""
        return cls(
            request_id=data['request_id'],
            agent_id=data['agent_id'],
            resource_id=data['resource_id'],
            lock_type=LockType(data['lock_type']),
            priority=LockPriority(data['priority']),
            requested_at=datetime.fromisoformat(data['requested_at']),
            timeout=data['timeout'],
            metadata=data['metadata']
        )


@dataclass
class ActiveLock:
    """Represents an active lock on a resource."""
    lock_id: str
    agent_id: str
    resource_id: str
    lock_type: LockType
    acquired_at: datetime
    expires_at: datetime
    request_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            'lock_id': self.lock_id,
            'agent_id': self.agent_id,
            'resource_id': self.resource_id,
            'lock_type': self.lock_type.value,
            'acquired_at': self.acquired_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'request_id': self.request_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActiveLock':
        """Create from dictionary stored in Redis."""
        return cls(
            lock_id=data['lock_id'],
            agent_id=data['agent_id'],
            resource_id=data['resource_id'],
            lock_type=LockType(data['lock_type']),
            acquired_at=datetime.fromisoformat(data['acquired_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            request_id=data['request_id']
        )
    
    def is_expired(self) -> bool:
        """Check if the lock has expired."""
        return datetime.utcnow() > self.expires_at


class MemoryLockingService:
    """Service for distributed locking of memory resources."""
    
    def __init__(self, redis_manager: RedisConnectionManager):
        """Initialize memory locking service.
        
        Args:
            redis_manager: Redis connection manager instance
        """
        self.redis_manager = redis_manager
        
        # Redis key prefixes
        self.LOCKS_PREFIX = "ltmc:locks:active:"
        self.QUEUE_PREFIX = "ltmc:locks:queue:"
        self.STATS_PREFIX = "ltmc:locks:stats"
        self.DEADLOCK_PREFIX = "ltmc:locks:deadlock:"
        
        # Configuration
        self.DEFAULT_LOCK_TIMEOUT = 300  # 5 minutes
        self.MAX_LOCK_TIMEOUT = 3600     # 1 hour
        self.CLEANUP_INTERVAL = 30       # seconds
        self.DEADLOCK_CHECK_INTERVAL = 60 # seconds
        self.QUEUE_MAX_SIZE = 1000       # max requests per resource
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._deadlock_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the memory locking service."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._deadlock_task = asyncio.create_task(self._deadlock_detection_loop())
        logger.info("Memory Locking Service started")
    
    async def stop(self) -> None:
        """Stop the memory locking service."""
        self._running = False
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._deadlock_task:
            self._deadlock_task.cancel()
        
        # Wait for tasks to complete
        tasks = [t for t in [self._cleanup_task, self._deadlock_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Memory Locking Service stopped")
    
    async def acquire_lock(
        self,
        agent_id: str,
        resource_id: str,
        lock_type: LockType = LockType.WRITE,
        priority: LockPriority = LockPriority.NORMAL,
        timeout: int = None,
        wait_timeout: int = 60,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Acquire a lock on a resource.
        
        Args:
            agent_id: Agent requesting the lock
            resource_id: Resource to lock
            lock_type: Type of lock (read/write/exclusive)
            priority: Request priority
            timeout: Lock timeout in seconds
            wait_timeout: Maximum time to wait for lock
            metadata: Additional metadata
            
        Returns:
            Lock ID if acquired, None if failed
        """
        try:
            timeout = timeout or self.DEFAULT_LOCK_TIMEOUT
            timeout = min(timeout, self.MAX_LOCK_TIMEOUT)
            
            request = LockRequest(
                request_id=str(uuid.uuid4()),
                agent_id=agent_id,
                resource_id=resource_id,
                lock_type=lock_type,
                priority=priority,
                requested_at=datetime.utcnow(),
                timeout=timeout,
                metadata=metadata or {}
            )
            
            # Check if lock can be acquired immediately
            if await self._can_acquire_immediately(request):
                return await self._grant_lock(request)
            
            # Add to queue and wait
            await self._add_to_queue(request)
            
            # Wait for lock to be granted
            return await self._wait_for_lock(request, wait_timeout)
            
        except Exception as e:
            logger.error(f"Failed to acquire lock for {resource_id}: {e}")
            return None
    
    async def release_lock(self, agent_id: str, lock_id: str) -> bool:
        """Release a lock.
        
        Args:
            agent_id: Agent releasing the lock
            lock_id: Lock ID to release
            
        Returns:
            True if released successfully
        """
        try:
            # Get lock info
            active_lock = await self._get_active_lock(lock_id)
            if not active_lock:
                return False
            
            # Verify ownership
            if active_lock.agent_id != agent_id:
                logger.warning(f"Agent {agent_id} tried to release lock owned by {active_lock.agent_id}")
                return False
            
            # Remove lock
            lock_key = f"{self.LOCKS_PREFIX}{active_lock.resource_id}:{lock_id}"
            await self.redis_manager.client.delete(lock_key)
            
            # Update stats
            await self._update_stats("locks_released", 1)
            
            # Process queue for this resource
            await self._process_lock_queue(active_lock.resource_id)
            
            logger.debug(f"Lock {lock_id} released by agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release lock {lock_id}: {e}")
            return False
    
    async def check_lock_status(self, lock_id: str) -> Optional[Dict[str, Any]]:
        """Check the status of a lock.
        
        Args:
            lock_id: Lock ID to check
            
        Returns:
            Lock status information or None if not found
        """
        try:
            active_lock = await self._get_active_lock(lock_id)
            if not active_lock:
                return None
            
            return {
                'lock_id': active_lock.lock_id,
                'agent_id': active_lock.agent_id,
                'resource_id': active_lock.resource_id,
                'lock_type': active_lock.lock_type.value,
                'acquired_at': active_lock.acquired_at.isoformat(),
                'expires_at': active_lock.expires_at.isoformat(),
                'is_expired': active_lock.is_expired(),
                'time_remaining': max(0, int((active_lock.expires_at - datetime.utcnow()).total_seconds()))
            }
            
        except Exception as e:
            logger.error(f"Failed to check lock status {lock_id}: {e}")
            return None
    
    async def get_resource_locks(self, resource_id: str) -> List[Dict[str, Any]]:
        """Get all locks for a resource.
        
        Args:
            resource_id: Resource ID to check
            
        Returns:
            List of active locks on the resource
        """
        try:
            locks = []
            pattern = f"{self.LOCKS_PREFIX}{resource_id}:*"
            
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                data = await self.redis_manager.client.get(key)
                if data:
                    try:
                        active_lock = ActiveLock.from_dict(json.loads(data))
                        if not active_lock.is_expired():
                            lock_status = await self.check_lock_status(active_lock.lock_id)
                            if lock_status:
                                locks.append(lock_status)
                    except Exception as e:
                        logger.warning(f"Failed to parse lock data from {key}: {e}")
            
            return locks
            
        except Exception as e:
            logger.error(f"Failed to get resource locks for {resource_id}: {e}")
            return []
    
    async def get_agent_locks(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all locks held by an agent.
        
        Args:
            agent_id: Agent ID to check
            
        Returns:
            List of locks held by the agent
        """
        try:
            locks = []
            pattern = f"{self.LOCKS_PREFIX}*"
            
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                data = await self.redis_manager.client.get(key)
                if data:
                    try:
                        active_lock = ActiveLock.from_dict(json.loads(data))
                        if active_lock.agent_id == agent_id and not active_lock.is_expired():
                            lock_status = await self.check_lock_status(active_lock.lock_id)
                            if lock_status:
                                locks.append(lock_status)
                    except Exception as e:
                        logger.warning(f"Failed to parse lock data from {key}: {e}")
            
            return locks
            
        except Exception as e:
            logger.error(f"Failed to get agent locks for {agent_id}: {e}")
            return []
    
    async def force_release_agent_locks(self, agent_id: str) -> int:
        """Force release all locks held by an agent (emergency cleanup).
        
        Args:
            agent_id: Agent ID whose locks to release
            
        Returns:
            Number of locks released
        """
        try:
            released = 0
            agent_locks = await self.get_agent_locks(agent_id)
            
            for lock_info in agent_locks:
                if await self.release_lock(agent_id, lock_info['lock_id']):
                    released += 1
            
            if released > 0:
                logger.info(f"Force released {released} locks for agent {agent_id}")
                await self._update_stats("forced_releases", released)
            
            return released
            
        except Exception as e:
            logger.error(f"Failed to force release locks for agent {agent_id}: {e}")
            return 0
    
    async def get_locking_stats(self) -> Dict[str, Any]:
        """Get locking service statistics.
        
        Returns:
            Dictionary with locking statistics
        """
        try:
            stats = {}
            
            # Count active locks
            active_count = 0
            lock_types = {}
            pattern = f"{self.LOCKS_PREFIX}*"
            
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                data = await self.redis_manager.client.get(key)
                if data:
                    try:
                        active_lock = ActiveLock.from_dict(json.loads(data))
                        if not active_lock.is_expired():
                            active_count += 1
                            lock_type = active_lock.lock_type.value
                            lock_types[lock_type] = lock_types.get(lock_type, 0) + 1
                    except Exception:
                        pass
            
            stats['active_locks'] = active_count
            stats['locks_by_type'] = lock_types
            
            # Count queued requests
            queued_count = 0
            queue_pattern = f"{self.QUEUE_PREFIX}*"
            async for key in self.redis_manager.client.scan_iter(match=queue_pattern):
                queue_size = await self.redis_manager.client.llen(key)
                queued_count += queue_size
            
            stats['queued_requests'] = queued_count
            
            # Get cumulative stats
            cumulative_stats = await self.redis_manager.client.hgetall(self.STATS_PREFIX)
            if cumulative_stats:
                stats['cumulative'] = {
                    k.decode(): int(v.decode()) for k, v in cumulative_stats.items()
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get locking stats: {e}")
            return {"error": str(e)}
    
    async def _can_acquire_immediately(self, request: LockRequest) -> bool:
        """Check if a lock can be acquired immediately.
        
        Args:
            request: Lock request to check
            
        Returns:
            True if lock can be acquired immediately
        """
        try:
            resource_locks = await self.get_resource_locks(request.resource_id)
            
            # No existing locks - can acquire
            if not resource_locks:
                return True
            
            # Check compatibility with existing locks
            for lock_info in resource_locks:
                existing_type = LockType(lock_info['lock_type'])
                
                # Write or exclusive locks are incompatible with everything
                if request.lock_type in [LockType.WRITE, LockType.EXCLUSIVE]:
                    return False
                
                if existing_type in [LockType.WRITE, LockType.EXCLUSIVE]:
                    return False
                
                # Multiple read locks are compatible
                if request.lock_type == LockType.READ and existing_type == LockType.READ:
                    continue
                else:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check immediate acquisition: {e}")
            return False
    
    async def _grant_lock(self, request: LockRequest) -> str:
        """Grant a lock to a request.
        
        Args:
            request: Lock request to grant
            
        Returns:
            Lock ID
        """
        try:
            lock_id = str(uuid.uuid4())
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=request.timeout)
            
            active_lock = ActiveLock(
                lock_id=lock_id,
                agent_id=request.agent_id,
                resource_id=request.resource_id,
                lock_type=request.lock_type,
                acquired_at=now,
                expires_at=expires_at,
                request_id=request.request_id
            )
            
            # Store active lock
            lock_key = f"{self.LOCKS_PREFIX}{request.resource_id}:{lock_id}"
            await self.redis_manager.client.setex(
                lock_key,
                request.timeout,
                json.dumps(active_lock.to_dict())
            )
            
            # Update stats
            await self._update_stats("locks_granted", 1)
            
            logger.debug(f"Lock {lock_id} granted to agent {request.agent_id} for resource {request.resource_id}")
            return lock_id
            
        except Exception as e:
            logger.error(f"Failed to grant lock: {e}")
            raise
    
    async def _add_to_queue(self, request: LockRequest) -> None:
        """Add a request to the lock queue.
        
        Args:
            request: Lock request to queue
        """
        try:
            queue_key = f"{self.QUEUE_PREFIX}{request.resource_id}"
            
            # Check queue size
            queue_size = await self.redis_manager.client.llen(queue_key)
            if queue_size >= self.QUEUE_MAX_SIZE:
                raise RuntimeError(f"Lock queue full for resource {request.resource_id}")
            
            # Add to queue with priority-based insertion
            queue_data = await self.redis_manager.client.lrange(queue_key, 0, -1)
            
            # Find insertion point based on priority
            insert_index = 0
            for i, data in enumerate(queue_data):
                try:
                    queued_request = LockRequest.from_dict(json.loads(data))
                    if request.priority.value > queued_request.priority.value:
                        insert_index = i
                        break
                    insert_index = i + 1
                except Exception:
                    continue
            
            # Insert at the calculated position
            if insert_index == 0:
                await self.redis_manager.client.lpush(queue_key, json.dumps(request.to_dict()))
            elif insert_index >= len(queue_data):
                await self.redis_manager.client.rpush(queue_key, json.dumps(request.to_dict()))
            else:
                # Redis doesn't have a native insert operation, so we need to reconstruct
                temp_key = f"{queue_key}:temp"
                await self.redis_manager.client.delete(temp_key)
                
                # Add items before insertion point
                for i in range(insert_index):
                    await self.redis_manager.client.rpush(temp_key, queue_data[i])
                
                # Add the new request
                await self.redis_manager.client.rpush(temp_key, json.dumps(request.to_dict()))
                
                # Add remaining items
                for i in range(insert_index, len(queue_data)):
                    await self.redis_manager.client.rpush(temp_key, queue_data[i])
                
                # Replace the original queue
                await self.redis_manager.client.delete(queue_key)
                await self.redis_manager.client.rename(temp_key, queue_key)
            
            # Set expiration for the queue
            await self.redis_manager.client.expire(queue_key, 3600)  # 1 hour
            
            await self._update_stats("requests_queued", 1)
            
        except Exception as e:
            logger.error(f"Failed to add request to queue: {e}")
            raise
    
    async def _wait_for_lock(self, request: LockRequest, wait_timeout: int) -> Optional[str]:
        """Wait for a queued lock request to be granted.
        
        Args:
            request: Lock request waiting for grant
            wait_timeout: Maximum time to wait
            
        Returns:
            Lock ID if granted, None if timeout
        """
        try:
            start_time = datetime.utcnow()
            
            while (datetime.utcnow() - start_time).total_seconds() < wait_timeout:
                # Check if we can acquire the lock now
                if await self._can_acquire_immediately(request):
                    # Remove from queue
                    await self._remove_from_queue(request)
                    return await self._grant_lock(request)
                
                # Wait before next check
                await asyncio.sleep(1)
            
            # Timeout - remove from queue
            await self._remove_from_queue(request)
            await self._update_stats("wait_timeouts", 1)
            return None
            
        except Exception as e:
            logger.error(f"Failed to wait for lock: {e}")
            return None
    
    async def _remove_from_queue(self, request: LockRequest) -> None:
        """Remove a request from the lock queue.
        
        Args:
            request: Request to remove
        """
        try:
            queue_key = f"{self.QUEUE_PREFIX}{request.resource_id}"
            
            # Remove the specific request (Redis doesn't have direct remove by value with complex data)
            queue_data = await self.redis_manager.client.lrange(queue_key, 0, -1)
            
            # Find and remove the request
            temp_key = f"{queue_key}:temp"
            await self.redis_manager.client.delete(temp_key)
            
            for data in queue_data:
                try:
                    queued_request = LockRequest.from_dict(json.loads(data))
                    if queued_request.request_id != request.request_id:
                        await self.redis_manager.client.rpush(temp_key, data)
                except Exception:
                    await self.redis_manager.client.rpush(temp_key, data)
            
            # Replace the original queue
            await self.redis_manager.client.delete(queue_key)
            queue_size = await self.redis_manager.client.llen(temp_key)
            if queue_size > 0:
                await self.redis_manager.client.rename(temp_key, queue_key)
                await self.redis_manager.client.expire(queue_key, 3600)
            else:
                await self.redis_manager.client.delete(temp_key)
            
        except Exception as e:
            logger.error(f"Failed to remove from queue: {e}")
    
    async def _process_lock_queue(self, resource_id: str) -> None:
        """Process the lock queue for a resource after a lock is released.
        
        Args:
            resource_id: Resource whose queue to process
        """
        try:
            queue_key = f"{self.QUEUE_PREFIX}{resource_id}"
            
            # Get the next request in queue
            data = await self.redis_manager.client.lindex(queue_key, 0)
            if not data:
                return
            
            try:
                request = LockRequest.from_dict(json.loads(data))
                
                # Check if this request can now be granted
                if await self._can_acquire_immediately(request):
                    # Remove from queue and grant lock
                    await self.redis_manager.client.lpop(queue_key)
                    await self._grant_lock(request)
                    
                    # Continue processing queue in case multiple requests can be granted
                    await self._process_lock_queue(resource_id)
                    
            except Exception as e:
                logger.warning(f"Failed to process queued request: {e}")
                # Remove invalid request
                await self.redis_manager.client.lpop(queue_key)
            
        except Exception as e:
            logger.error(f"Failed to process lock queue for {resource_id}: {e}")
    
    async def _get_active_lock(self, lock_id: str) -> Optional[ActiveLock]:
        """Get active lock by lock ID.
        
        Args:
            lock_id: Lock ID to retrieve
            
        Returns:
            Active lock or None if not found
        """
        try:
            # Search for lock across all resources
            pattern = f"{self.LOCKS_PREFIX}*:{lock_id}"
            
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                data = await self.redis_manager.client.get(key)
                if data:
                    return ActiveLock.from_dict(json.loads(data))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get active lock {lock_id}: {e}")
            return None
    
    async def _update_stats(self, stat_name: str, increment: int = 1) -> None:
        """Update locking statistics.
        
        Args:
            stat_name: Name of the statistic
            increment: Amount to increment by
        """
        try:
            await self.redis_manager.client.hincrby(
                self.STATS_PREFIX, stat_name, increment
            )
        except Exception as e:
            logger.warning(f"Failed to update stat {stat_name}: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop for expired locks."""
        while self._running:
            try:
                await self._cleanup_expired_locks()
                await asyncio.sleep(self.CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(self.CLEANUP_INTERVAL)
    
    async def _cleanup_expired_locks(self) -> None:
        """Clean up expired locks."""
        try:
            expired_count = 0
            pattern = f"{self.LOCKS_PREFIX}*"
            
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                data = await self.redis_manager.client.get(key)
                if data:
                    try:
                        active_lock = ActiveLock.from_dict(json.loads(data))
                        if active_lock.is_expired():
                            await self.redis_manager.client.delete(key)
                            expired_count += 1
                            
                            # Process queue for this resource
                            await self._process_lock_queue(active_lock.resource_id)
                    except Exception:
                        # Remove invalid data
                        await self.redis_manager.client.delete(key)
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired locks")
                await self._update_stats("expired_cleaned", expired_count)
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired locks: {e}")
    
    async def _deadlock_detection_loop(self) -> None:
        """Background loop for deadlock detection."""
        while self._running:
            try:
                await self._detect_deadlocks()
                await asyncio.sleep(self.DEADLOCK_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in deadlock detection: {e}")
                await asyncio.sleep(self.DEADLOCK_CHECK_INTERVAL)
    
    async def _detect_deadlocks(self) -> None:
        """Detect and resolve deadlocks."""
        # This is a simplified deadlock detection
        # In a production system, you might want a more sophisticated algorithm
        try:
            # Get all agents with locks
            agent_locks = {}
            pattern = f"{self.LOCKS_PREFIX}*"
            
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                data = await self.redis_manager.client.get(key)
                if data:
                    try:
                        active_lock = ActiveLock.from_dict(json.loads(data))
                        if not active_lock.is_expired():
                            if active_lock.agent_id not in agent_locks:
                                agent_locks[active_lock.agent_id] = []
                            agent_locks[active_lock.agent_id].append(active_lock)
                    except Exception:
                        pass
            
            # Simple detection: if an agent has been holding locks for too long
            now = datetime.utcnow()
            for agent_id, locks in agent_locks.items():
                for lock in locks:
                    if (now - lock.acquired_at).total_seconds() > self.MAX_LOCK_TIMEOUT:
                        logger.warning(f"Potential deadlock: Agent {agent_id} holding lock {lock.lock_id} for too long")
                        await self._update_stats("potential_deadlocks", 1)
                        
                        # Could implement automatic resolution here
                        # For now, just log and rely on lock expiration
            
        except Exception as e:
            logger.error(f"Failed to detect deadlocks: {e}")


# Global service instance
_memory_locking_service: Optional[MemoryLockingService] = None


async def get_memory_locking_service() -> MemoryLockingService:
    """Get or create memory locking service."""
    global _memory_locking_service
    if not _memory_locking_service:
        redis_manager = await get_redis_manager()
        _memory_locking_service = MemoryLockingService(redis_manager)
        await _memory_locking_service.start()
    return _memory_locking_service


async def cleanup_memory_locking():
    """Cleanup memory locking service."""
    global _memory_locking_service
    if _memory_locking_service:
        await _memory_locking_service.stop()
        _memory_locking_service = None