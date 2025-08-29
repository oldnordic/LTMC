"""
LTMC Orchestration Service

Provides agent coordination and orchestration capabilities for multi-agent workflows.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class OrchestrationMode(Enum):
    """Orchestration modes for different coordination strategies."""
    DISABLED = "disabled"
    BASIC = "basic"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PRIORITY = "priority"
    COLLABORATIVE = "collaborative"
    FULL = "full"
    DEBUG = "debug"


class AgentStatus(Enum):
    """Status of agents in orchestration."""
    IDLE = "idle"
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentContext:
    """Context information for an agent in orchestration."""
    agent_id: str
    agent_name: str
    capabilities: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class OrchestrationService:
    """Service for coordinating multi-agent workflows."""
    
    def __init__(self, mode: OrchestrationMode = OrchestrationMode.COLLABORATIVE):
        self.mode = mode
        self._agent_contexts: Dict[str, AgentContext] = {}
        self._session_agents: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        logger.info(f"OrchestrationService initialized with mode: {mode.value}")
    
    async def register_agent(
        self, 
        agent_name: str, 
        capabilities: List[str], 
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register an agent for orchestration."""
        agent_id = f"{agent_name.lower().replace(' ', '_')}_{session_id}_{len(self._agent_contexts)}"
        
        async with self._lock:
            context = AgentContext(
                agent_id=agent_id,
                agent_name=agent_name,
                capabilities=capabilities,
                session_id=session_id,
                metadata=metadata or {}
            )
            
            self._agent_contexts[agent_id] = context
            
            if session_id not in self._session_agents:
                self._session_agents[session_id] = set()
            self._session_agents[session_id].add(agent_id)
            
            logger.info(f"Registered agent {agent_name} with ID {agent_id} for session {session_id}")
            return agent_id
    
    async def get_session_context(self, agent_id: str) -> Optional[AgentContext]:
        """Get context for a specific agent."""
        return self._agent_contexts.get(agent_id)
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status."""
        async with self._lock:
            if agent_id in self._agent_contexts:
                self._agent_contexts[agent_id].status = status
                self._agent_contexts[agent_id].last_activity = datetime.now(timezone.utc)
                logger.info(f"Updated agent {agent_id} status to {status.value}")
                return True
            return False
    
    async def get_session_agents(self, session_id: str) -> List[AgentContext]:
        """Get all agents for a session."""
        if session_id not in self._session_agents:
            return []
        
        return [
            self._agent_contexts[agent_id] 
            for agent_id in self._session_agents[session_id]
            if agent_id in self._agent_contexts
        ]
    
    async def execute_tool_with_coordination(
        self, 
        agent_id: str, 
        tool_name: str, 
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool with orchestration coordination."""
        if agent_id not in self._agent_contexts:
            return {"success": False, "error": f"Agent {agent_id} not registered"}
        
        await self.update_agent_status(agent_id, AgentStatus.ACTIVE)
        
        try:
            # Simulate coordinated tool execution
            result = {
                "success": True,
                "tool_name": tool_name,
                "agent_id": agent_id,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "mode": self.mode.value,
                "coordination_metadata": {
                    "session_agents": len(self._session_agents.get(
                        self._agent_contexts[agent_id].session_id, set()
                    )),
                    "orchestration_mode": self.mode.value
                }
            }
            
            await self.update_agent_status(agent_id, AgentStatus.COMPLETED)
            logger.info(f"Agent {agent_id} executed tool {tool_name} successfully")
            return result
            
        except Exception as e:
            await self.update_agent_status(agent_id, AgentStatus.ERROR)
            logger.error(f"Agent {agent_id} failed to execute tool {tool_name}: {e}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up all agents for a session."""
        async with self._lock:
            if session_id not in self._session_agents:
                return False
            
            agent_ids = self._session_agents[session_id].copy()
            for agent_id in agent_ids:
                if agent_id in self._agent_contexts:
                    del self._agent_contexts[agent_id]
            
            del self._session_agents[session_id]
            logger.info(f"Cleaned up session {session_id} with {len(agent_ids)} agents")
            return True
    
    def is_available(self) -> bool:
        """Check if orchestration service is available."""
        return True
    
    async def get_orchestration_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics."""
        return {
            "total_agents": len(self._agent_contexts),
            "active_sessions": len(self._session_agents),
            "mode": self.mode.value,
            "agent_status_counts": {
                status.value: sum(
                    1 for ctx in self._agent_contexts.values() 
                    if ctx.status == status
                ) for status in AgentStatus
            }
        }


# Global orchestration service instance
_orchestration_service: Optional[OrchestrationService] = None


def get_orchestration_service(mode: OrchestrationMode = OrchestrationMode.COLLABORATIVE) -> OrchestrationService:
    """Get the global orchestration service instance."""
    global _orchestration_service
    
    if _orchestration_service is None:
        _orchestration_service = OrchestrationService(mode=mode)
        logger.info("Created global orchestration service instance")
    
    return _orchestration_service


def reset_orchestration_service():
    """Reset the global orchestration service (primarily for testing)."""
    global _orchestration_service
    _orchestration_service = None
    logger.info("Reset global orchestration service instance")