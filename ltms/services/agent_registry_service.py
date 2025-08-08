"""Agent Registry Service for LTMC multi-agent coordination."""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from ltms.services.redis_service import RedisConnectionManager, get_redis_manager

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration."""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class AgentCapability:
    """Represents an agent capability."""
    name: str
    version: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    agent_id: str
    name: str
    status: AgentStatus
    capabilities: List[AgentCapability]
    last_heartbeat: datetime
    session_id: Optional[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': self.status.value,
            'capabilities': [asdict(cap) for cap in self.capabilities],
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'session_id': self.session_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentInfo':
        """Create from dictionary stored in Redis."""
        capabilities = [
            AgentCapability(**cap) for cap in data.get('capabilities', [])
        ]
        return cls(
            agent_id=data['agent_id'],
            name=data['name'],
            status=AgentStatus(data['status']),
            capabilities=capabilities,
            last_heartbeat=datetime.fromisoformat(data['last_heartbeat']),
            session_id=data.get('session_id'),
            metadata=data.get('metadata', {})
        )


class AgentRegistryService:
    """Service for managing agent registration and capabilities."""
    
    def __init__(self, redis_manager: RedisConnectionManager):
        """Initialize agent registry service.
        
        Args:
            redis_manager: Redis connection manager instance
        """
        self.redis_manager = redis_manager
        
        # Redis key prefixes
        self.AGENTS_PREFIX = "ltmc:agents:active:"
        self.CAPABILITIES_PREFIX = "ltmc:agents:capabilities:"
        self.SESSIONS_PREFIX = "ltmc:agents:sessions:"
        self.STATS_PREFIX = "ltmc:agents:stats"
        
        # Configuration
        self.HEARTBEAT_TIMEOUT = 60  # seconds
        self.CLEANUP_INTERVAL = 30   # seconds
        
        # Background task for cleanup
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the agent registry service."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Agent Registry Service started")
    
    async def stop(self) -> None:
        """Stop the agent registry service."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Agent Registry Service stopped")
    
    async def register_agent(
        self,
        agent_id: str,
        name: str,
        capabilities: List[AgentCapability],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register a new agent.
        
        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            capabilities: List of agent capabilities
            session_id: Optional session ID
            metadata: Additional agent metadata
            
        Returns:
            True if registered successfully
        """
        try:
            agent_info = AgentInfo(
                agent_id=agent_id,
                name=name,
                status=AgentStatus.ACTIVE,
                capabilities=capabilities,
                last_heartbeat=datetime.utcnow(),
                session_id=session_id,
                metadata=metadata or {}
            )
            
            # Store agent info
            agent_key = f"{self.AGENTS_PREFIX}{agent_id}"
            await self.redis_manager.client.setex(
                agent_key, 
                self.HEARTBEAT_TIMEOUT * 2,  # Double timeout for grace period
                json.dumps(agent_info.to_dict())
            )
            
            # Index capabilities
            for capability in capabilities:
                cap_key = f"{self.CAPABILITIES_PREFIX}{capability.name}"
                await self.redis_manager.client.sadd(cap_key, agent_id)
                await self.redis_manager.client.expire(cap_key, self.HEARTBEAT_TIMEOUT * 2)
            
            # Track session association if provided
            if session_id:
                session_key = f"{self.SESSIONS_PREFIX}{session_id}"
                await self.redis_manager.client.sadd(session_key, agent_id)
                await self.redis_manager.client.expire(session_key, 3600)  # 1 hour
            
            # Update stats
            await self._update_stats("agents_registered", 1)
            
            logger.info(f"Agent registered: {agent_id} ({name})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    async def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an agent.
        
        Args:
            agent_id: Agent identifier to deregister
            
        Returns:
            True if deregistered successfully
        """
        try:
            # Get agent info before deletion
            agent_info = await self.get_agent_info(agent_id)
            if not agent_info:
                return False
            
            # Remove from capability indices
            for capability in agent_info.capabilities:
                cap_key = f"{self.CAPABILITIES_PREFIX}{capability.name}"
                await self.redis_manager.client.srem(cap_key, agent_id)
            
            # Remove from session association
            if agent_info.session_id:
                session_key = f"{self.SESSIONS_PREFIX}{agent_info.session_id}"
                await self.redis_manager.client.srem(session_key, agent_id)
            
            # Remove agent record
            agent_key = f"{self.AGENTS_PREFIX}{agent_id}"
            await self.redis_manager.client.delete(agent_key)
            
            # Update stats
            await self._update_stats("agents_deregistered", 1)
            
            logger.info(f"Agent deregistered: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deregister agent {agent_id}: {e}")
            return False
    
    async def update_heartbeat(
        self,
        agent_id: str,
        status: Optional[AgentStatus] = None
    ) -> bool:
        """Update agent heartbeat and status.
        
        Args:
            agent_id: Agent identifier
            status: Optional new status
            
        Returns:
            True if updated successfully
        """
        try:
            agent_info = await self.get_agent_info(agent_id)
            if not agent_info:
                return False
            
            # Update heartbeat and status
            agent_info.last_heartbeat = datetime.utcnow()
            if status:
                agent_info.status = status
            
            # Store updated info
            agent_key = f"{self.AGENTS_PREFIX}{agent_id}"
            await self.redis_manager.client.setex(
                agent_key,
                self.HEARTBEAT_TIMEOUT * 2,
                json.dumps(agent_info.to_dict())
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update heartbeat for agent {agent_id}: {e}")
            return False
    
    async def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get information about a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent information or None if not found
        """
        try:
            agent_key = f"{self.AGENTS_PREFIX}{agent_id}"
            data = await self.redis_manager.client.get(agent_key)
            
            if not data:
                return None
            
            return AgentInfo.from_dict(json.loads(data))
            
        except Exception as e:
            logger.error(f"Failed to get agent info for {agent_id}: {e}")
            return None
    
    async def get_active_agents(self) -> List[AgentInfo]:
        """Get all active agents.
        
        Returns:
            List of active agent information
        """
        try:
            agents = []
            pattern = f"{self.AGENTS_PREFIX}*"
            
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                data = await self.redis_manager.client.get(key)
                if data:
                    try:
                        agent_info = AgentInfo.from_dict(json.loads(data))
                        # Check if agent is still considered active
                        if self._is_agent_active(agent_info):
                            agents.append(agent_info)
                    except Exception as e:
                        logger.warning(f"Failed to parse agent data from {key}: {e}")
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to get active agents: {e}")
            return []
    
    async def find_agents_by_capability(self, capability_name: str) -> List[AgentInfo]:
        """Find agents with specific capability.
        
        Args:
            capability_name: Name of the capability to search for
            
        Returns:
            List of agents with the capability
        """
        try:
            cap_key = f"{self.CAPABILITIES_PREFIX}{capability_name}"
            agent_ids = await self.redis_manager.client.smembers(cap_key)
            
            agents = []
            for agent_id in agent_ids:
                agent_info = await self.get_agent_info(agent_id.decode())
                if agent_info and self._is_agent_active(agent_info):
                    agents.append(agent_info)
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to find agents by capability {capability_name}: {e}")
            return []
    
    async def get_session_agents(self, session_id: str) -> List[AgentInfo]:
        """Get agents associated with a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of agents in the session
        """
        try:
            session_key = f"{self.SESSIONS_PREFIX}{session_id}"
            agent_ids = await self.redis_manager.client.smembers(session_key)
            
            agents = []
            for agent_id in agent_ids:
                agent_info = await self.get_agent_info(agent_id.decode())
                if agent_info and self._is_agent_active(agent_info):
                    agents.append(agent_info)
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to get session agents for {session_id}: {e}")
            return []
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get agent registry statistics.
        
        Returns:
            Dictionary with registry statistics
        """
        try:
            stats = {}
            
            # Count active agents
            active_agents = await self.get_active_agents()
            stats['active_agents'] = len(active_agents)
            
            # Count by status
            status_counts = {}
            for agent in active_agents:
                status = agent.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            stats['agent_status_counts'] = status_counts
            
            # Count unique capabilities
            capabilities = set()
            for agent in active_agents:
                for cap in agent.capabilities:
                    capabilities.add(cap.name)
            stats['unique_capabilities'] = len(capabilities)
            
            # Get cumulative stats
            registry_stats = await self.redis_manager.client.hgetall(self.STATS_PREFIX)
            if registry_stats:
                stats['cumulative'] = {
                    k.decode(): int(v.decode()) for k, v in registry_stats.items()
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get registry stats: {e}")
            return {"error": str(e)}
    
    def _is_agent_active(self, agent_info: AgentInfo) -> bool:
        """Check if agent is considered active based on heartbeat.
        
        Args:
            agent_info: Agent information
            
        Returns:
            True if agent is active
        """
        time_since_heartbeat = datetime.utcnow() - agent_info.last_heartbeat
        return time_since_heartbeat.total_seconds() < self.HEARTBEAT_TIMEOUT
    
    async def _update_stats(self, stat_name: str, increment: int = 1) -> None:
        """Update registry statistics.
        
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
        """Background cleanup loop for expired agents."""
        while self._running:
            try:
                await self._cleanup_expired_agents()
                await asyncio.sleep(self.CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(self.CLEANUP_INTERVAL)
    
    async def _cleanup_expired_agents(self) -> None:
        """Clean up expired agents from the registry."""
        try:
            active_agents = await self.get_active_agents()
            expired_count = 0
            
            for agent in active_agents:
                if not self._is_agent_active(agent):
                    await self.deregister_agent(agent.agent_id)
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired agents")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired agents: {e}")


# Global service instance
_agent_registry_service: Optional[AgentRegistryService] = None


async def get_agent_registry_service() -> AgentRegistryService:
    """Get or create agent registry service."""
    global _agent_registry_service
    if not _agent_registry_service:
        redis_manager = await get_redis_manager()
        _agent_registry_service = AgentRegistryService(redis_manager)
        await _agent_registry_service.start()
    return _agent_registry_service


async def cleanup_agent_registry():
    """Cleanup agent registry service."""
    global _agent_registry_service
    if _agent_registry_service:
        await _agent_registry_service.stop()
        _agent_registry_service = None