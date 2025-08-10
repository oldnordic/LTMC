"""Orchestration Service - Unified interface for LTMC multi-agent coordination."""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

from ltms.services.redis_service import get_redis_manager
from ltms.services.agent_registry_service import (
    get_agent_registry_service, 
    AgentCapability, 
    AgentStatus
)
from ltms.services.context_coordination_service import (
    get_context_coordination_service,
    ContextEventType
)
from ltms.services.memory_locking_service import (
    get_memory_locking_service,
    LockType,
    LockPriority
)
from ltms.services.enhanced_task_manager import EnhancedTaskManager, TaskAssignment
from ltms.ml.task_routing_engine import TeamMember
from ltms.orchestration.workflow_engine import WorkflowEngine, WorkflowDefinition
from ltms.orchestration.task_coordinator import TaskCoordinator, CoordinationTask, ExecutionContext

logger = logging.getLogger(__name__)


class OrchestrationMode(Enum):
    """Orchestration operation modes."""
    DISABLED = "disabled"      # No orchestration - fallback to basic operations
    BASIC = "basic"           # Basic coordination without locking
    FULL = "full"             # Full orchestration with all features
    DEBUG = "debug"           # Debug mode with extensive logging


@dataclass
class AgentContext:
    """Context for an agent in the orchestration system."""
    agent_id: str
    session_id: str
    capabilities: List[str]
    metadata: Dict[str, Any]
    orchestration_mode: OrchestrationMode
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'session_id': self.session_id,
            'capabilities': self.capabilities,
            'metadata': self.metadata,
            'orchestration_mode': self.orchestration_mode.value
        }


@dataclass
class ToolExecutionContext:
    """Context for coordinated tool execution."""
    tool_name: str
    agent_context: AgentContext
    parameters: Dict[str, Any]
    requires_memory_lock: bool
    cache_result: bool
    share_result: bool
    execution_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tool_name': self.tool_name,
            'agent_context': self.agent_context.to_dict(),
            'parameters': self.parameters,
            'requires_memory_lock': self.requires_memory_lock,
            'cache_result': self.cache_result,
            'share_result': self.share_result,
            'execution_id': self.execution_id
        }


class OrchestrationService:
    """Unified orchestration service for LTMC multi-agent coordination."""
    
    def __init__(self):
        """Initialize orchestration service."""
        self.redis_manager = None
        self.agent_registry = None
        self.context_coordination = None
        self.memory_locking = None
        self.task_manager = None
        self.workflow_engine = None
        self.task_coordinator = None
        
        # Service state
        self._initialized = False
        self._mode = OrchestrationMode.BASIC
        
        # Tool configuration - which tools require orchestration
        self.ORCHESTRATED_TOOLS = {
            'store_memory': {
                'requires_lock': True,
                'lock_type': LockType.WRITE,
                'cache_result': False,
                'share_result': True
            },
            'retrieve_memory': {
                'requires_lock': True,
                'lock_type': LockType.READ,
                'cache_result': True,
                'share_result': True
            },
            'update_memory': {
                'requires_lock': True,
                'lock_type': LockType.WRITE,
                'cache_result': False,
                'share_result': True
            },
            'delete_memory': {
                'requires_lock': True,
                'lock_type': LockType.EXCLUSIVE,
                'cache_result': False,
                'share_result': True
            },
            'search_memory': {
                'requires_lock': True,
                'lock_type': LockType.READ,
                'cache_result': True,
                'share_result': True
            },
            'log_code_attempt': {
                'requires_lock': True,
                'lock_type': LockType.WRITE,
                'cache_result': False,
                'share_result': True
            },
            'get_context_for_query': {
                'requires_lock': True,
                'lock_type': LockType.READ,
                'cache_result': True,
                'share_result': True
            }
        }
        
        # Active agent contexts
        self._agent_contexts: Dict[str, AgentContext] = {}
    
    async def initialize(
        self,
        orchestration_mode: OrchestrationMode = OrchestrationMode.BASIC
    ) -> bool:
        """Initialize the orchestration service.
        
        Args:
            orchestration_mode: Mode of orchestration to use
            
        Returns:
            True if initialized successfully
        """
        try:
            if self._initialized:
                return True
            
            self._mode = orchestration_mode
            
            # Initialize Redis connection
            self.redis_manager = await get_redis_manager()
            
            # Initialize services based on mode
            if self._mode != OrchestrationMode.DISABLED:
                self.agent_registry = await get_agent_registry_service()
                self.context_coordination = await get_context_coordination_service()
                
                if self._mode == OrchestrationMode.FULL:
                    self.memory_locking = await get_memory_locking_service()
                
                # Initialize task manager for enhanced coordination
                if self._mode in [OrchestrationMode.FULL, OrchestrationMode.BASIC]:
                    self.task_manager = EnhancedTaskManager(redis_manager=self.redis_manager)
                    await self.task_manager.initialize()
                
                # Initialize advanced orchestration components (Component 5)
                if self._mode in [OrchestrationMode.FULL, OrchestrationMode.DEBUG]:
                    self.workflow_engine = WorkflowEngine(redis_manager=self.redis_manager)
                    await self.workflow_engine.initialize()
                    
                    self.task_coordinator = TaskCoordinator(redis_manager=self.redis_manager)
                    await self.task_coordinator.initialize()
            
            self._initialized = True
            logger.info(f"Orchestration Service initialized in {self._mode.value} mode")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestration service: {e}")
            return False
    
    async def register_agent(
        self,
        agent_name: str,
        capabilities: List[str],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        orchestration_mode: Optional[OrchestrationMode] = None
    ) -> Optional[str]:
        """Register an agent with the orchestration system.
        
        Args:
            agent_name: Human-readable agent name
            capabilities: List of capability names
            session_id: Optional session ID for multi-agent coordination
            metadata: Additional agent metadata
            orchestration_mode: Agent-specific orchestration mode
            
        Returns:
            Agent ID if registered successfully
        """
        try:
            if not self._initialized or self._mode == OrchestrationMode.DISABLED:
                # Return a simple agent ID without orchestration
                agent_id = f"agent_{uuid.uuid4().hex[:8]}"
                logger.debug(f"Agent {agent_name} registered without orchestration: {agent_id}")
                return agent_id
            
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"
            session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
            orchestration_mode = orchestration_mode or self._mode
            
            # Create agent capabilities
            agent_capabilities = [
                AgentCapability(
                    name=cap,
                    version="1.0.0",
                    description=f"Capability: {cap}",
                    parameters={}
                )
                for cap in capabilities
            ]
            
            # Register with agent registry
            success = await self.agent_registry.register_agent(
                agent_id=agent_id,
                name=agent_name,
                capabilities=agent_capabilities,
                session_id=session_id,
                metadata=metadata or {}
            )
            
            if not success:
                return None
            
            # Create agent context
            agent_context = AgentContext(
                agent_id=agent_id,
                session_id=session_id,
                capabilities=capabilities,
                metadata=metadata or {},
                orchestration_mode=orchestration_mode
            )
            
            self._agent_contexts[agent_id] = agent_context
            
            # Join session context
            await self.context_coordination.join_session(session_id, agent_id)
            
            logger.info(f"Agent {agent_name} registered with orchestration: {agent_id}")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_name}: {e}")
            return None
    
    async def execute_tool_with_coordination(
        self,
        agent_id: str,
        tool_name: str,
        tool_function: Callable,
        parameters: Dict[str, Any],
        **kwargs
    ) -> Any:
        """Execute a tool with full orchestration coordination.
        
        Args:
            agent_id: Agent executing the tool
            tool_name: Name of the tool being executed
            tool_function: The actual tool function to execute
            parameters: Tool parameters
            **kwargs: Additional arguments for tool execution
            
        Returns:
            Tool execution result
        """
        try:
            # Check if agent is registered for orchestration
            agent_context = self._agent_contexts.get(agent_id)
            
            if not agent_context or agent_context.orchestration_mode == OrchestrationMode.DISABLED:
                # Execute without orchestration
                return await self._execute_tool_basic(tool_function, parameters, **kwargs)
            
            # Get tool configuration
            tool_config = self.ORCHESTRATED_TOOLS.get(tool_name, {})
            
            # Create execution context
            execution_context = ToolExecutionContext(
                tool_name=tool_name,
                agent_context=agent_context,
                parameters=parameters,
                requires_memory_lock=tool_config.get('requires_lock', False),
                cache_result=tool_config.get('cache_result', False),
                share_result=tool_config.get('share_result', False),
                execution_id=str(uuid.uuid4())
            )
            
            # Execute with coordination
            return await self._execute_tool_coordinated(
                execution_context,
                tool_function,
                tool_config,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name} with coordination: {e}")
            # Fallback to basic execution
            return await self._execute_tool_basic(tool_function, parameters, **kwargs)
    
    async def update_agent_heartbeat(
        self,
        agent_id: str,
        status: Optional[AgentStatus] = None
    ) -> bool:
        """Update agent heartbeat.
        
        Args:
            agent_id: Agent identifier
            status: Optional new status
            
        Returns:
            True if updated successfully
        """
        try:
            if not self._initialized or self._mode == OrchestrationMode.DISABLED:
                return True  # No-op in disabled mode
            
            if agent_id not in self._agent_contexts:
                return False
            
            return await self.agent_registry.update_heartbeat(agent_id, status)
            
        except Exception as e:
            logger.error(f"Failed to update heartbeat for agent {agent_id}: {e}")
            return False
    
    async def share_memory_update(
        self,
        agent_id: str,
        memory_type: str,
        operation: str,
        data: Dict[str, Any]
    ) -> bool:
        """Share a memory update with other agents in the session.
        
        Args:
            agent_id: Agent making the update
            memory_type: Type of memory being updated
            operation: Operation performed (create, update, delete)
            data: Update data
            
        Returns:
            True if shared successfully
        """
        try:
            agent_context = self._agent_contexts.get(agent_id)
            if not agent_context or self._mode == OrchestrationMode.DISABLED:
                return True
            
            await self.context_coordination.update_shared_memory(
                session_id=agent_context.session_id,
                agent_id=agent_id,
                updates={
                    'memory_update': {
                        'type': memory_type,
                        'operation': operation,
                        'data': data,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to share memory update: {e}")
            return False
    
    async def get_session_context(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get shared session context for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Session context or None if not available
        """
        try:
            agent_context = self._agent_contexts.get(agent_id)
            if not agent_context or self._mode == OrchestrationMode.DISABLED:
                return None
            
            context = await self.context_coordination.get_session_context(
                agent_context.session_id
            )
            
            return context.to_dict() if context else None
            
        except Exception as e:
            logger.error(f"Failed to get session context for agent {agent_id}: {e}")
            return None
    
    async def find_capable_agents(
        self,
        capability: str,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find agents with a specific capability.
        
        Args:
            capability: Capability name to search for
            session_id: Optional session filter
            
        Returns:
            List of matching agents
        """
        try:
            if not self._initialized or self._mode == OrchestrationMode.DISABLED:
                return []
            
            agents = await self.agent_registry.find_agents_by_capability(capability)
            
            # Filter by session if specified
            if session_id:
                agents = [
                    agent for agent in agents
                    if agent.session_id == session_id
                ]
            
            return [
                {
                    'agent_id': agent.agent_id,
                    'name': agent.name,
                    'status': agent.status.value,
                    'session_id': agent.session_id,
                    'capabilities': [cap.name for cap in agent.capabilities]
                }
                for agent in agents
            ]
            
        except Exception as e:
            logger.error(f"Failed to find capable agents: {e}")
            return []
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status.
        
        Returns:
            Status information dictionary
        """
        try:
            status = {
                'initialized': self._initialized,
                'mode': self._mode.value,
                'active_agents': len(self._agent_contexts),
                'services': {
                    'redis': self.redis_manager is not None,
                    'agent_registry': self.agent_registry is not None,
                    'context_coordination': self.context_coordination is not None,
                    'memory_locking': self.memory_locking is not None,
                    'workflow_engine': self.workflow_engine is not None,
                    'task_coordinator': self.task_coordinator is not None
                }
            }
            
            if self._initialized and self._mode != OrchestrationMode.DISABLED:
                # Add service statistics
                if self.agent_registry:
                    status['agent_stats'] = await self.agent_registry.get_registry_stats()
                
                if self.context_coordination:
                    status['coordination_stats'] = await self.context_coordination.get_coordination_stats()
                
                if self.memory_locking:
                    status['locking_stats'] = await self.memory_locking.get_locking_stats()
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get orchestration status: {e}")
            return {'error': str(e)}
    
    async def cleanup_agent(self, agent_id: str) -> bool:
        """Clean up an agent from the orchestration system.
        
        Args:
            agent_id: Agent identifier to clean up
            
        Returns:
            True if cleaned up successfully
        """
        try:
            if not self._initialized or self._mode == OrchestrationMode.DISABLED:
                return True
            
            agent_context = self._agent_contexts.get(agent_id)
            if not agent_context:
                return True
            
            # Leave session
            await self.context_coordination.leave_session(
                agent_context.session_id,
                agent_id
            )
            
            # Force release any held locks
            if self.memory_locking:
                await self.memory_locking.force_release_agent_locks(agent_id)
            
            # Deregister agent
            await self.agent_registry.deregister_agent(agent_id)
            
            # Remove from local context
            del self._agent_contexts[agent_id]
            
            logger.info(f"Agent {agent_id} cleaned up from orchestration")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup agent {agent_id}: {e}")
            return False
    
    async def _execute_tool_basic(
        self,
        tool_function: Callable,
        parameters: Dict[str, Any],
        **kwargs
    ) -> Any:
        """Execute tool without orchestration.
        
        Args:
            tool_function: Tool function to execute
            parameters: Tool parameters
            **kwargs: Additional arguments
            
        Returns:
            Tool execution result
        """
        try:
            # Simple direct execution
            if asyncio.iscoroutinefunction(tool_function):
                return await tool_function(**parameters, **kwargs)
            else:
                return tool_function(**parameters, **kwargs)
                
        except Exception as e:
            logger.error(f"Basic tool execution failed: {e}")
            raise
    
    async def _execute_tool_coordinated(
        self,
        execution_context: ToolExecutionContext,
        tool_function: Callable,
        tool_config: Dict[str, Any],
        **kwargs
    ) -> Any:
        """Execute tool with full coordination.
        
        Args:
            execution_context: Execution context
            tool_function: Tool function to execute
            tool_config: Tool configuration
            **kwargs: Additional arguments
            
        Returns:
            Tool execution result
        """
        lock_id = None
        try:
            # Acquire memory lock if required
            if (execution_context.requires_memory_lock and 
                self.memory_locking and 
                execution_context.agent_context.orchestration_mode == OrchestrationMode.FULL):
                
                resource_id = self._get_resource_id(execution_context)
                lock_type = tool_config.get('lock_type', LockType.WRITE)
                
                lock_id = await self.memory_locking.acquire_lock(
                    agent_id=execution_context.agent_context.agent_id,
                    resource_id=resource_id,
                    lock_type=lock_type,
                    priority=LockPriority.NORMAL,
                    timeout=300,  # 5 minutes
                    wait_timeout=60  # 1 minute wait
                )
                
                if not lock_id:
                    raise RuntimeError(f"Failed to acquire memory lock for {resource_id}")
            
            # Execute the tool
            if asyncio.iscoroutinefunction(tool_function):
                result = await tool_function(**execution_context.parameters, **kwargs)
            else:
                result = tool_function(**execution_context.parameters, **kwargs)
            
            # Share result with session if configured
            if execution_context.share_result:
                await self._share_tool_result(execution_context, result)
            
            # Publish tool execution event
            await self.context_coordination.update_shared_memory(
                session_id=execution_context.agent_context.session_id,
                agent_id=execution_context.agent_context.agent_id,
                updates={
                    'tool_execution': {
                        'tool_name': execution_context.tool_name,
                        'execution_id': execution_context.execution_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'success': True
                    }
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Coordinated tool execution failed: {e}")
            
            # Publish failure event
            try:
                await self.context_coordination.update_shared_memory(
                    session_id=execution_context.agent_context.session_id,
                    agent_id=execution_context.agent_context.agent_id,
                    updates={
                        'tool_execution': {
                            'tool_name': execution_context.tool_name,
                            'execution_id': execution_context.execution_id,
                            'timestamp': datetime.utcnow().isoformat(),
                            'success': False,
                            'error': str(e)
                        }
                    }
                )
            except Exception:
                pass  # Don't fail the original operation
            
            raise
            
        finally:
            # Release lock if acquired
            if lock_id and self.memory_locking:
                try:
                    await self.memory_locking.release_lock(
                        execution_context.agent_context.agent_id,
                        lock_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to release lock {lock_id}: {e}")
    
    def _get_resource_id(self, execution_context: ToolExecutionContext) -> str:
        """Generate resource ID for locking.
        
        Args:
            execution_context: Execution context
            
        Returns:
            Resource identifier
        """
        # Generate resource ID based on tool and parameters
        # This is a simplified approach - you might want more sophisticated logic
        if 'file_name' in execution_context.parameters:
            return f"memory:{execution_context.parameters['file_name']}"
        elif 'query' in execution_context.parameters:
            # Use a hash for queries to avoid conflicts
            query_hash = str(hash(execution_context.parameters['query']))
            return f"query:{query_hash}"
        else:
            return f"tool:{execution_context.tool_name}"
    
    async def _share_tool_result(
        self,
        execution_context: ToolExecutionContext,
        result: Any
    ) -> None:
        """Share tool execution result with session.
        
        Args:
            execution_context: Execution context
            result: Tool execution result
        """
        try:
            # Serialize result for sharing (careful with complex objects)
            if isinstance(result, (dict, list, str, int, float, bool)):
                shared_result = result
            else:
                # For complex objects, share metadata instead
                shared_result = {
                    'type': str(type(result)),
                    'summary': str(result)[:200] + '...' if len(str(result)) > 200 else str(result)
                }
            
            await self.context_coordination.update_shared_memory(
                session_id=execution_context.agent_context.session_id,
                agent_id=execution_context.agent_context.agent_id,
                updates={
                    'tool_results': {
                        execution_context.execution_id: {
                            'tool_name': execution_context.tool_name,
                            'result': shared_result,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to share tool result: {e}")
    
    # Task Management Integration Methods
    
    async def create_team_member_from_agent(
        self,
        agent_id: str,
        skills: List[str],
        experience_level: float,
        availability_hours: float = 8.0,
        project_id: Optional[str] = None
    ) -> Optional[TeamMember]:
        """
        Create a TeamMember instance from an agent for task assignment.
        
        Args:
            agent_id: Agent identifier
            skills: List of agent skills
            experience_level: Experience level (0.0 to 1.0)
            availability_hours: Available hours per day
            project_id: Project identifier for isolation
            
        Returns:
            TeamMember instance or None if agent not found
        """
        try:
            agent_context = self._agent_contexts.get(agent_id)
            if not agent_context:
                return None
            
            # Get current workload from agent registry if available
            current_workload = 0.0
            if self.agent_registry:
                # In a real implementation, you'd fetch actual workload
                current_workload = 0.3  # Default moderate workload
            
            team_member = TeamMember(
                member_id=agent_id,
                name=f"Agent {agent_id[:8]}",
                skills=skills,
                experience_level=experience_level,
                current_workload=current_workload,
                availability_hours=availability_hours,
                project_id=project_id or agent_context.session_id,
                metadata=agent_context.metadata
            )
            
            return team_member
            
        except Exception as e:
            logger.error(f"Error creating team member from agent: {e}")
            return None
    
    async def assign_task_to_agents(
        self,
        task_blueprint,
        available_agents: List[str],
        project_id: str,
        agent_skills: Optional[Dict[str, List[str]]] = None,
        agent_experience: Optional[Dict[str, float]] = None
    ) -> Optional[TaskAssignment]:
        """
        Assign a task to the most suitable agent using intelligent routing.
        
        Args:
            task_blueprint: TaskBlueprint to assign
            available_agents: List of available agent IDs
            project_id: Project identifier
            agent_skills: Optional mapping of agent_id -> skills
            agent_experience: Optional mapping of agent_id -> experience level
            
        Returns:
            TaskAssignment or None if no suitable agent found
        """
        try:
            if not self.task_manager:
                logger.warning("Task manager not initialized, cannot assign tasks")
                return None
            
            # Convert agents to team members
            team_members = []
            for agent_id in available_agents:
                skills = agent_skills.get(agent_id, []) if agent_skills else []
                experience = agent_experience.get(agent_id, 0.5) if agent_experience else 0.5
                
                team_member = await self.create_team_member_from_agent(
                    agent_id=agent_id,
                    skills=skills,
                    experience_level=experience,
                    project_id=project_id
                )
                
                if team_member:
                    team_members.append(team_member)
            
            if not team_members:
                logger.warning(f"No valid team members created from agents: {available_agents}")
                return None
            
            # Use task manager to route the task
            assignment = await self.task_manager.route_task(
                task_blueprint=task_blueprint,
                available_members=team_members,
                project_id=project_id
            )
            
            logger.info(
                f"Task {task_blueprint.blueprint_id} assigned to agent {assignment.assigned_member.member_id} "
                f"with {assignment.confidence_score:.2%} confidence"
            )
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error assigning task to agents: {e}")
            return None
    
    async def update_agent_task_progress(
        self,
        assignment_id: str,
        progress_percentage: float,
        status: str,
        notes: str = ""
    ) -> bool:
        """
        Update progress for an agent's task assignment.
        
        Args:
            assignment_id: Task assignment ID
            progress_percentage: Progress (0.0 to 1.0)
            status: Current status
            notes: Progress notes
            
        Returns:
            True if update successful
        """
        try:
            if not self.task_manager:
                return False
            
            await self.task_manager.update_task_progress(
                assignment_id=assignment_id,
                progress_percentage=progress_percentage,
                status=status,
                notes=notes
            )
            
            # Share progress update with session
            # Find the agent from assignment
            assignment_progress = await self.task_manager.get_task_progress(assignment_id)
            if assignment_progress:
                await self.share_memory_update(
                    agent_id=assignment_progress.get('agent_id', 'unknown'),
                    memory_type='task_progress',
                    operation='update',
                    data={
                        'assignment_id': assignment_id,
                        'progress_percentage': progress_percentage,
                        'status': status,
                        'notes': notes
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent task progress: {e}")
            return False
    
    async def get_agent_workload_overview(
        self,
        project_id: str,
        agent_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get workload overview for agents in a project.
        
        Args:
            project_id: Project identifier
            agent_ids: Optional specific agent IDs to include
            
        Returns:
            Workload overview dictionary
        """
        try:
            if not self.task_manager:
                return {'error': 'Task manager not initialized'}
            
            # Get all agents in the project
            if agent_ids is None:
                agent_ids = [
                    agent_id for agent_id, context in self._agent_contexts.items()
                    if context.session_id == project_id  # Using session_id as project proxy
                ]
            
            # Convert to team members
            team_members = []
            for agent_id in agent_ids:
                # Get agent skills from context
                agent_context = self._agent_contexts.get(agent_id)
                if agent_context:
                    team_member = TeamMember(
                        member_id=agent_id,
                        name=f"Agent {agent_id[:8]}",
                        skills=agent_context.capabilities,
                        experience_level=0.7,  # Default
                        current_workload=0.3,  # Default
                        availability_hours=8.0,
                        project_id=project_id,
                        metadata=agent_context.metadata
                    )
                    team_members.append(team_member)
            
            # Get workload overview
            overview = await self.task_manager.get_team_workload_overview(
                team_members=team_members,
                project_id=project_id
            )
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting agent workload overview: {e}")
            return {'error': str(e)}
    
    async def predict_agent_task_completion(
        self,
        assignment_id: str,
        current_progress: float
    ) -> Optional[datetime]:
        """
        Predict completion time for an agent's task.
        
        Args:
            assignment_id: Task assignment ID
            current_progress: Current progress (0.0 to 1.0)
            
        Returns:
            Predicted completion datetime or None
        """
        try:
            if not self.task_manager:
                return None
            
            # Get assignment details to find the agent
            progress_data = await self.task_manager.get_task_progress(assignment_id)
            if not progress_data:
                return None
            
            # Get agent ID from assignment (would need to be stored in progress data)
            agent_id = progress_data.get('agent_id', 'unknown')
            
            predicted_time = await self.task_manager.predict_completion_time(
                assignment_id=assignment_id,
                current_progress=current_progress,
                member_id=agent_id
            )
            
            return predicted_time
            
        except Exception as e:
            logger.error(f"Error predicting agent task completion: {e}")
            return None
    
    # Advanced Orchestration Methods (Component 5 Integration)
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        project_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute a workflow using the WorkflowEngine.
        
        Args:
            workflow_id: ID of workflow to execute
            input_data: Input data for the workflow
            project_id: Optional project identifier
            
        Returns:
            Workflow execution result or None if engine not available
        """
        try:
            if not self.workflow_engine:
                logger.warning("Workflow engine not initialized - upgrade to FULL mode")
                return None
            
            result = await self.workflow_engine.execute_workflow(
                workflow_id=workflow_id,
                input_data=input_data,
                project_id=project_id
            )
            
            return {
                'success': result.success,
                'execution_id': result.workflow_execution.execution_id,
                'state': result.workflow_execution.state.value,
                'step_results': {
                    step_id: {
                        'success': step_result.success,
                        'output': step_result.output,
                        'error': step_result.error,
                        'execution_time': step_result.execution_time_seconds
                    }
                    for step_id, step_result in result.workflow_execution.step_results.items()
                },
                'total_time': result.total_execution_time_seconds,
                'error': result.error_message
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            return None
    
    async def register_workflow_definition(
        self,
        workflow_definition: WorkflowDefinition
    ) -> bool:
        """Register a workflow definition.
        
        Args:
            workflow_definition: Workflow definition to register
            
        Returns:
            True if registered successfully
        """
        try:
            if not self.workflow_engine:
                logger.warning("Workflow engine not initialized - upgrade to FULL mode")
                return False
            
            return await self.workflow_engine.register_workflow_definition(workflow_definition)
            
        except Exception as e:
            logger.error(f"Error registering workflow definition: {e}")
            return False
    
    async def coordinate_complex_tasks(
        self,
        tasks: List[CoordinationTask],
        project_id: str,
        initiated_by: str
    ) -> Optional[Dict[str, Any]]:
        """Coordinate execution of complex tasks with dependencies.
        
        Args:
            tasks: List of coordination tasks
            project_id: Project identifier
            initiated_by: User who initiated the coordination
            
        Returns:
            Coordination result or None if coordinator not available
        """
        try:
            if not self.task_coordinator:
                logger.warning("Task coordinator not initialized - upgrade to FULL mode")
                return None
            
            execution_context = ExecutionContext(
                coordinator_id=f"orchestration_{uuid.uuid4().hex[:8]}",
                project_id=project_id,
                initiated_by=initiated_by
            )
            
            result = await self.task_coordinator.coordinate_tasks(
                tasks=tasks,
                project_id=project_id,
                execution_context=execution_context
            )
            
            return {
                'success': result.success,
                'execution_context': result.execution_context.coordinator_id,
                'tasks_completed': result.tasks_completed,
                'tasks_failed': result.tasks_failed,
                'tasks_skipped': result.tasks_skipped,
                'total_execution_time': result.total_execution_time_seconds,
                'task_results': result.task_results,
                'error': result.error_message
            }
            
        except Exception as e:
            logger.error(f"Error coordinating complex tasks: {e}")
            return None
    
    async def register_workflow_step_handler(
        self,
        action_name: str,
        handler: Callable
    ) -> bool:
        """Register a workflow step handler.
        
        Args:
            action_name: Name of the workflow action
            handler: Handler function
            
        Returns:
            True if registered successfully
        """
        try:
            if not self.workflow_engine:
                logger.warning("Workflow engine not initialized - upgrade to FULL mode")
                return False
            
            return await self.workflow_engine.register_step_handler(action_name, handler)
            
        except Exception as e:
            logger.error(f"Error registering workflow step handler: {e}")
            return False
    
    async def register_task_coordination_handler(
        self,
        action_name: str,
        handler: Callable
    ) -> bool:
        """Register a task coordination handler.
        
        Args:
            action_name: Name of the coordination action
            handler: Handler function
            
        Returns:
            True if registered successfully
        """
        try:
            if not self.task_coordinator:
                logger.warning("Task coordinator not initialized - upgrade to FULL mode")
                return False
            
            return await self.task_coordinator.register_task_handler(action_name, handler)
            
        except Exception as e:
            logger.error(f"Error registering task coordination handler: {e}")
            return False
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of active workflows.
        
        Args:
            workflow_id: Optional workflow ID to filter
            
        Returns:
            Workflow status information
        """
        try:
            if not self.workflow_engine:
                return None
            
            active_executions = await self.workflow_engine.get_active_executions()
            
            if workflow_id:
                # Filter by workflow ID
                active_executions = [
                    execution for execution in active_executions
                    if execution.workflow_id == workflow_id
                ]
            
            return {
                'active_workflows': len(active_executions),
                'executions': [
                    {
                        'execution_id': execution.execution_id,
                        'workflow_id': execution.workflow_id,
                        'state': execution.state.value,
                        'started_at': execution.started_at.isoformat(),
                        'current_step': execution.current_step,
                        'project_id': execution.project_id
                    }
                    for execution in active_executions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return None


# Global service instance
_orchestration_service: Optional[OrchestrationService] = None


async def get_orchestration_service(
    orchestration_mode: OrchestrationMode = OrchestrationMode.BASIC
) -> OrchestrationService:
    """Get or create orchestration service.
    
    Args:
        orchestration_mode: Mode of orchestration to use
        
    Returns:
        Orchestration service instance
    """
    global _orchestration_service
    if not _orchestration_service:
        _orchestration_service = OrchestrationService()
        await _orchestration_service.initialize(orchestration_mode)
    return _orchestration_service


async def cleanup_orchestration():
    """Cleanup orchestration service."""
    global _orchestration_service
    if _orchestration_service:
        # Clean up all registered agents
        for agent_id in list(_orchestration_service._agent_contexts.keys()):
            await _orchestration_service.cleanup_agent(agent_id)
        
        _orchestration_service = None
        logger.info("Orchestration service cleaned up")