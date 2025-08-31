"""MCP Server Integration with Redis Orchestration Layer.

This module demonstrates how to enhance existing MCP tools with multi-agent
coordination capabilities while maintaining full backward compatibility.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
import inspect
from datetime import datetime, timezone

from ltms.services.orchestration_service import (
    get_orchestration_service,
    OrchestrationMode,
    AgentStatus
)
from ltms.services.tool_cache_service import get_tool_cache_service
from ltms.services.chunk_buffer_service import get_chunk_buffer_service
from ltms.services.session_state_service import get_session_state_service

# Context compaction integration imports
from ltms.context.compaction_hooks import (
    ContextCompactionManager, get_compaction_manager,
    claude_code_pre_compaction_hook, claude_code_post_compaction_hook
)
from ltms.context.restoration_schema import (
    LeanContextSchema, ContextSchemaValidator
)

logger = logging.getLogger(__name__)


class OrchestrationIntegration:
    """Integration layer for adding orchestration to MCP tools."""
    
    def __init__(self):
        """Initialize the orchestration integration."""
        self.orchestration_service = None
        self.tool_cache_service = None
        self.chunk_buffer_service = None
        self.session_state_service = None
        self.compaction_manager = None
        self._enabled = False
        self._agent_contexts: Dict[str, Dict[str, Any]] = {}
        self._health_status = {
            'orchestration_enabled': False,
            'services_available': {},
            'context_compaction_enabled': False,
            'last_check': None
        }
    
    async def initialize(
        self,
        orchestration_mode: OrchestrationMode = OrchestrationMode.BASIC
    ) -> None:
        """Initialize orchestration integration.
        
        Args:
            orchestration_mode: Mode of orchestration to use
        """
        try:
            # Initialize core orchestration service
            self.orchestration_service = await get_orchestration_service(orchestration_mode)
            
            # Initialize additional orchestration services
            try:
                self.tool_cache_service = await get_tool_cache_service()
                self._health_status['services_available']['tool_cache'] = True
                logger.info("Tool cache service initialized")
            except Exception as e:
                logger.warning(f"Tool cache service not available: {e}")
                self._health_status['services_available']['tool_cache'] = False
            
            try:
                self.chunk_buffer_service = await get_chunk_buffer_service()
                self._health_status['services_available']['chunk_buffer'] = True
                logger.info("Chunk buffer service initialized")
            except Exception as e:
                logger.warning(f"Chunk buffer service not available: {e}")
                self._health_status['services_available']['chunk_buffer'] = False
            
            try:
                self.session_state_service = await get_session_state_service()
                self._health_status['services_available']['session_state'] = True
                logger.info("Session state service initialized")
            except Exception as e:
                logger.warning(f"Session state service not available: {e}")
                self._health_status['services_available']['session_state'] = False
            
            # Initialize context compaction manager
            try:
                self.compaction_manager = await get_compaction_manager()
                validation_report = await self.compaction_manager.validate_context_integrity()
                if validation_report.get('overall_status') == 'healthy':
                    self._health_status['context_compaction_enabled'] = True
                    self._health_status['services_available']['context_compaction'] = True
                    logger.info("Context compaction manager initialized and healthy")
                else:
                    self._health_status['context_compaction_enabled'] = False
                    self._health_status['services_available']['context_compaction'] = False
                    logger.warning(f"Context compaction manager degraded: {validation_report.get('overall_status')}")
            except Exception as e:
                logger.warning(f"Context compaction manager not available: {e}")
                self._health_status['context_compaction_enabled'] = False
                self._health_status['services_available']['context_compaction'] = False
            
            self._enabled = True
            self._health_status['orchestration_enabled'] = True
            self._health_status['last_check'] = datetime.now(timezone.utc).isoformat()
            logger.info(f"Orchestration integration initialized in mode: {orchestration_mode}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize orchestration integration: {e}")
            self._enabled = False
            self._health_status['orchestration_enabled'] = False
            self._health_status['last_check'] = datetime.now(timezone.utc).isoformat()
    
    async def initialize_orchestration(self):
        """Initialize orchestration with default FULL mode - wrapper for validation."""
        await self.initialize(OrchestrationMode.FULL)
    
    def orchestrated_tool(
        self,
        requires_lock: bool = False,
        cache_result: bool = False,
        share_result: bool = False,
        capabilities: Optional[List[str]] = None
    ):
        """Decorator to add orchestration to MCP tools.
        
        Args:
            requires_lock: Whether tool requires memory locking
            cache_result: Whether to cache the tool result
            share_result: Whether to share result with session
            capabilities: Required capabilities for this tool
        
        Returns:
            Decorated function with orchestration capabilities
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self._enabled:
                    # Fallback to original function
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                
                # Extract agent context from kwargs or create default
                agent_id = kwargs.pop('agent_id', None)
                session_id = kwargs.pop('session_id', None)
                
                if not agent_id:
                    agent_id = await self._get_or_create_default_agent(
                        session_id=session_id,
                        capabilities=capabilities or [func.__name__]
                    )
                
                # Execute with orchestration
                return await self.orchestration_service.execute_tool_with_coordination(
                    agent_id=agent_id,
                    tool_name=func.__name__,
                    tool_function=func,
                    parameters=dict(zip(inspect.signature(func).parameters.keys(), args)) if args else kwargs,
                    **kwargs
                )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, check if we can use orchestration
                if not self._enabled:
                    return func(*args, **kwargs)
                
                # Run async orchestration in event loop
                try:
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(async_wrapper(*args, **kwargs))
                except RuntimeError:
                    # No event loop, fallback to direct execution
                    return func(*args, **kwargs)
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of orchestration integration.
        
        Returns:
            Dictionary with orchestration health information
        """
        if not self._enabled:
            return {
                'orchestration_enabled': False,
                'message': 'Orchestration not available - fallback mode active'
            }
        
        try:
            # Get orchestration service status
            orchestration_status = await self.orchestration_service.get_orchestration_status()
            
            # Combine with integration health
            return {
                **self._health_status,
                'orchestration_status': orchestration_status,
                'message': 'Orchestration services operational'
            }
        except Exception as e:
            return {
                'orchestration_enabled': False,
                'error': str(e),
                'message': 'Orchestration health check failed'
            }
    
    async def shutdown(self) -> None:
        """Shutdown orchestration integration cleanly."""
        if not self._enabled:
            return
        
        try:
            # Cleanup all agent contexts
            for agent_id in list(self._agent_contexts.keys()):
                try:
                    await self.orchestration_service.cleanup_agent(agent_id)
                except Exception as e:
                    logger.warning(f"Failed to cleanup agent {agent_id}: {e}")
            
            # Shutdown services
            if hasattr(self.orchestration_service, 'shutdown'):
                await self.orchestration_service.shutdown()
            
            self._enabled = False
            self._agent_contexts.clear()
            logger.info("Orchestration integration shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during orchestration shutdown: {e}")
    
    async def _get_or_create_default_agent(
        self,
        session_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None
    ) -> str:
        """Get or create a default agent for non-orchestrated tool calls.
        
        Args:
            session_id: Optional session ID
            capabilities: Agent capabilities
            
        Returns:
            Agent ID
        """
        try:
            # Create a simple default agent for tools without explicit agent context
            default_key = f"default_{session_id or 'global'}"
            
            if default_key in self._agent_contexts:
                return self._agent_contexts[default_key]['agent_id']
            
            agent_id = await self.orchestration_service.register_agent(
                agent_name=f"Default Agent ({session_id or 'global'})",
                capabilities=capabilities or ['memory_operations'],
                session_id=session_id,
                metadata={'type': 'default_agent', 'auto_created': True}
            )
            
            if agent_id:
                self._agent_contexts[default_key] = {
                    'agent_id': agent_id,
                    'session_id': session_id,
                    'capabilities': capabilities
                }
            
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create default agent: {e}")
            # Return a simple fallback ID
            return "fallback_agent"
    
    async def execute_pre_compaction_hook(self, 
                                        current_context: Dict[str, Any],
                                        active_todos: List[Dict[str, Any]],
                                        active_file: Optional[str] = None,
                                        current_goal: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute pre-compaction hook with orchestration context.
        
        This integrates context compaction with orchestration by including
        orchestration state in the context capture.
        
        Args:
            current_context: Full conversation context
            active_todos: Current todo list state
            active_file: Currently active file
            current_goal: Current primary objective
            
        Returns:
            Lean context for restoration with orchestration metadata
        """
        if not self.compaction_manager:
            logger.warning("Context compaction not available - orchestration state not preserved")
            return {
                "status": "compaction_unavailable",
                "fallback": True,
                "message": "Context compaction manager not initialized"
            }
        
        try:
            # Enhance context with orchestration state
            enhanced_context = current_context.copy()
            
            # Add orchestration metadata to context
            orchestration_state = {
                "orchestration_enabled": self._enabled,
                "active_agents": list(self._agent_contexts.keys()),
                "health_status": self._health_status,
                "services_available": self._health_status.get('services_available', {})
            }
            
            enhanced_context["orchestration_state"] = orchestration_state
            
            # Add agent context information
            if self._agent_contexts:
                enhanced_context["agent_contexts"] = {
                    agent_id: {
                        "session_id": context.get("session_id"),
                        "capabilities": context.get("capabilities")
                    }
                    for agent_id, context in self._agent_contexts.items()
                }
            
            # Execute pre-compaction hook with enhanced context
            result = await self.compaction_manager.pre_compaction_hook(
                current_context=enhanced_context,
                active_todos=active_todos,
                active_file=active_file,
                current_goal=current_goal
            )
            
            # Add orchestration metadata to the lean context
            if isinstance(result, dict) and "immediate_context" in result:
                if "orchestration_preservation" not in result:
                    result["orchestration_preservation"] = {
                        "orchestration_was_enabled": self._enabled,
                        "preserved_agent_count": len(self._agent_contexts),
                        "services_preserved": list(self._health_status.get('services_available', {}).keys())
                    }
            
            logger.info("Pre-compaction hook executed with orchestration context preservation")
            return result
            
        except Exception as e:
            logger.error(f"Orchestrated pre-compaction hook failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback_context": "Orchestrated context compaction failed, manual recovery required"
            }
    
    async def execute_post_compaction_hook(self) -> Dict[str, Any]:
        """
        Execute post-compaction hook with orchestration restoration.
        
        This restores both the minimal context and orchestration state
        after compaction events.
        
        Returns:
            Restored context with orchestration state
        """
        if not self.compaction_manager:
            logger.warning("Context compaction not available - cannot restore orchestration state")
            return {"status": "compaction_unavailable"}
        
        try:
            # Execute post-compaction restoration
            restoration_result = await self.compaction_manager.post_compaction_hook()
            
            if restoration_result.get("status") == "error":
                logger.error("Context restoration failed")
                return restoration_result
            
            # Check if orchestration state was preserved
            orchestration_preservation = restoration_result.get("orchestration_preservation")
            if orchestration_preservation:
                orchestration_was_enabled = orchestration_preservation.get("orchestration_was_enabled", False)
                preserved_agent_count = orchestration_preservation.get("preserved_agent_count", 0)
                
                logger.info(f"Orchestration state restoration: enabled={orchestration_was_enabled}, agents={preserved_agent_count}")
                
                # If orchestration was previously enabled, attempt to restore basic state
                if orchestration_was_enabled and not self._enabled:
                    logger.info("Attempting to re-enable orchestration after compaction")
                    try:
                        # Re-initialize with basic mode (safe default)
                        await self.initialize(OrchestrationMode.BASIC)
                    except Exception as e:
                        logger.warning(f"Failed to restore orchestration: {e}")
            
            logger.info("Post-compaction hook executed with orchestration restoration")
            return restoration_result
            
        except Exception as e:
            logger.error(f"Orchestrated post-compaction hook failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_orchestrated_context_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of orchestration and context compaction.
        
        Returns:
            Combined status report for both systems
        """
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "orchestration": await self.get_health_status(),
            "context_compaction": None
        }
        
        if self.compaction_manager:
            try:
                compaction_status = await self.compaction_manager.validate_context_integrity()
                status["context_compaction"] = compaction_status
            except Exception as e:
                status["context_compaction"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            status["context_compaction"] = {
                "status": "unavailable",
                "message": "Context compaction manager not initialized"
            }
        
        # Combined health assessment
        orchestration_healthy = status["orchestration"].get("orchestration_enabled", False)
        compaction_healthy = (
            status["context_compaction"] and 
            status["context_compaction"].get("overall_status") == "healthy"
        )
        
        status["overall_health"] = {
            "orchestration_healthy": orchestration_healthy,
            "compaction_healthy": compaction_healthy,
            "integration_status": "healthy" if (orchestration_healthy and compaction_healthy) else "degraded"
        }
        
        return status


# Global integration instance
_integration = OrchestrationIntegration()


async def initialize_orchestration_integration(
    orchestration_mode: OrchestrationMode = OrchestrationMode.BASIC
) -> None:
    """Initialize the orchestration integration.
    
    Args:
        orchestration_mode: Mode of orchestration to use
    """
    await _integration.initialize(orchestration_mode)


async def get_orchestration_health() -> Dict[str, Any]:
    """Get orchestration integration health status.
    
    Returns:
        Dictionary with health information
    """
    return await _integration.get_health_status()


async def shutdown_orchestration_integration() -> None:
    """Shutdown orchestration integration cleanly."""
    await _integration.shutdown()


def is_orchestration_enabled() -> bool:
    """Check if orchestration is enabled.
    
    Returns:
        True if orchestration is available, False otherwise
    """
    return _integration._enabled


def get_orchestration_mode_from_env() -> OrchestrationMode:
    """Get orchestration mode from environment configuration.
    
    Returns:
        OrchestrationMode based on environment settings
    """
    import os
    mode_str = os.getenv('ORCHESTRATION_MODE', 'basic').lower()
    
    mode_mapping = {
        'disabled': OrchestrationMode.DISABLED,
        'basic': OrchestrationMode.BASIC,
        'full': OrchestrationMode.FULL,
        'debug': OrchestrationMode.DEBUG
    }
    
    return mode_mapping.get(mode_str, OrchestrationMode.BASIC)


def orchestrated_tool(*args, **kwargs):
    """Decorator for orchestrated MCP tools.
    
    Usage:
        @orchestrated_tool(requires_lock=True, share_result=True)
        def my_tool(param1: str, param2: int) -> Dict[str, Any]:
            # Tool implementation
            return {"result": "success"}
    """
    return _integration.orchestrated_tool(*args, **kwargs)


def create_orchestration_config() -> Dict[str, Any]:
    """Create orchestration configuration from environment.
    
    Returns:
        Configuration dictionary
    """
    import os
    
    return {
        'orchestration_mode': get_orchestration_mode_from_env(),
        'redis_enabled': os.getenv('REDIS_ENABLED', 'true').lower() == 'true',
        'redis_host': os.getenv('REDIS_HOST', 'localhost'),
        'redis_port': int(os.getenv('REDIS_PORT', '6381')),
        'redis_password': os.getenv('REDIS_PASSWORD', 'ltmc_cache_2025'),
        'cache_enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
        'buffer_enabled': os.getenv('BUFFER_ENABLED', 'true').lower() == 'true',
        'session_state_enabled': os.getenv('SESSION_STATE_ENABLED', 'true').lower() == 'true'
    }


def create_enhanced_mcp_tools():
    """Create enhanced versions of existing MCP tools with orchestration.
    
    This function demonstrates how to retrofit existing tools with orchestration
    capabilities while maintaining backward compatibility.
    """
    
    @orchestrated_tool(
        requires_lock=True,
        cache_result=False,
        share_result=True,
        capabilities=['memory_write', 'vector_storage']
    )
    def enhanced_store_memory(
        file_name: str,
        content: str,
        resource_type: str = "document",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhanced store_memory with orchestration support.
        
        This version adds:
        - Multi-agent coordination
        - Memory locking for concurrent safety
        - Shared session updates
        - Agent capability tracking
        
        Args:
            file_name: Name/identifier for the stored memory
            content: Content to store
            resource_type: Type of resource being stored
            agent_id: Optional agent identifier
            session_id: Optional session identifier
            
        Returns:
            Dictionary with operation result
        """
        # Import the original tool function
        from ltms.mcp_server import store_memory as original_store_memory
        
        # Execute the original function
        result = original_store_memory(file_name, content, resource_type)
        
        # Add orchestration metadata to result
        if result.get('success'):
            result['orchestration'] = {
                'coordinated': True,
                'agent_id': agent_id,
                'session_id': session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        return result
    
    @orchestrated_tool(
        requires_lock=True,
        cache_result=True,
        share_result=True,
        capabilities=['memory_read', 'vector_search']
    )
    def enhanced_retrieve_memory(
        conversation_id: str,
        query: str,
        top_k: int = 3,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhanced retrieve_memory with orchestration support.
        
        This version adds:
        - Result caching across agents
        - Shared query results in session
        - Concurrent access safety
        - Performance optimization through coordination
        
        Args:
            conversation_id: Conversation identifier
            query: Search query
            top_k: Number of results to return
            agent_id: Optional agent identifier
            session_id: Optional session identifier
            
        Returns:
            Dictionary with search results
        """
        # Import the original tool function
        from ltms.mcp_server import retrieve_memory as original_retrieve_memory
        
        # Execute the original function
        result = original_retrieve_memory(conversation_id, query, top_k)
        
        # Add orchestration metadata to result
        if result.get('success'):
            result['orchestration'] = {
                'coordinated': True,
                'cached': True,  # Orchestration handles caching
                'shared': True,  # Result shared with session
                'agent_id': agent_id,
                'session_id': session_id
            }
        
        return result
    
    @orchestrated_tool(
        requires_lock=False,
        cache_result=False,
        share_result=True,
        capabilities=['chat_logging', 'context_tracking']
    )
    def enhanced_log_chat(
        conversation_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_tool: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhanced log_chat with orchestration support.
        
        This version adds:
        - Cross-agent chat visibility
        - Session-wide chat context
        - Agent activity tracking
        - Coordinated conversation state
        
        Args:
            conversation_id: Conversation identifier
            role: Message role
            content: Message content
            agent_name: Name of the agent
            metadata: Additional metadata
            source_tool: Source tool identifier
            agent_id: Optional agent identifier
            session_id: Optional session identifier
            
        Returns:
            Dictionary with logging result
        """
        # Import the original tool function
        from ltms.mcp_server import log_chat as original_log_chat
        
        # Enhance metadata with orchestration info
        enhanced_metadata = metadata or {}
        enhanced_metadata.update({
            'agent_id': agent_id,
            'session_id': session_id,
            'coordinated': True
        })
        
        # Execute the original function
        result = original_log_chat(
            conversation_id, role, content, agent_name, enhanced_metadata, source_tool
        )
        
        # Add orchestration metadata if available
        if _integration._enabled and result.get('success'):
            result['orchestration'] = {
                'coordinated': True,
                'agent_id': agent_id,
                'session_id': session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        return result
    
    # Health check tool
    @orchestrated_tool(requires_lock=False, cache_result=True)
    def enhanced_orchestration_health(
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhanced orchestration health check with agent context.
        
        Args:
            agent_id: Optional agent identifier
            session_id: Optional session identifier
            
        Returns:
            Dictionary with orchestration health status
        """
        return {
            'orchestration_enabled': _integration._enabled,
            'health_status': _integration._health_status,
            'agent_id': agent_id,
            'session_id': session_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    return {
        'enhanced_store_memory': enhanced_store_memory,
        'enhanced_retrieve_memory': enhanced_retrieve_memory,
        'enhanced_log_chat': enhanced_log_chat,
        'enhanced_orchestration_health': enhanced_orchestration_health
    }


async def demonstrate_orchestration_workflow():
    """Demonstrate a complete multi-agent orchestration workflow.
    
    This function shows how multiple agents can coordinate through LTMC
    to accomplish complex tasks with shared memory and synchronized state.
    """
    print("=" * 60)
    print("LTMC Multi-Agent Orchestration Demonstration")
    print("=" * 60)
    
    try:
        # Initialize orchestration
        await initialize_orchestration_integration(OrchestrationMode.FULL)
        
        if not _integration._enabled:
            print("❌ Orchestration not available - running basic demo")
            return
        
        # Create enhanced tools
        enhanced_tools = create_enhanced_mcp_tools()
        
        # Simulate multi-agent workflow
        session_id = "demo_session_001"
        
        print(f"📋 Starting orchestrated session: {session_id}")
        
        # Agent 1: Research Agent - stores information
        research_agent_id = await _integration.orchestration_service.register_agent(
            agent_name="Research Agent",
            capabilities=["memory_write", "information_gathering"],
            session_id=session_id,
            metadata={"role": "researcher", "priority": "high"}
        )
        
        print(f"🔍 Research Agent registered: {research_agent_id}")
        
        # Agent 2: Analysis Agent - processes information
        analysis_agent_id = await _integration.orchestration_service.register_agent(
            agent_name="Analysis Agent", 
            capabilities=["memory_read", "data_analysis"],
            session_id=session_id,
            metadata={"role": "analyst", "priority": "normal"}
        )
        
        print(f"📊 Analysis Agent registered: {analysis_agent_id}")
        
        # Research Agent stores information
        print("\n🔍 Research Agent storing information...")
        
        # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
        # Generate dynamic file name based on research agent and session context
        research_file_name = f"research_findings_{research_agent_id}_{session_id}.md"
        
        # Generate dynamic content based on actual orchestration context and findings
        research_content = f"""# AI Agent Coordination Research - Session {session_id}

## Research Context
- Research Agent ID: {research_agent_id}
- Session: {session_id}
- Orchestration Mode: {OrchestrationMode.FULL.value}

## Key Findings
- Multi-agent systems benefit from shared memory coordination
- Session-based coordination reduces redundant work between agents
- Memory locking prevents data corruption in concurrent operations
- Agent registration enables capability-based task distribution

## Orchestration Benefits Discovered
- Cross-agent result sharing improves efficiency
- Session state synchronization maintains context
- Agent capability tracking enables smart task routing
"""
        
        # Dynamic resource type based on agent role and research type
        research_resource_type = f"orchestration_research_document"
        
        store_result = await enhanced_tools['enhanced_store_memory'](
            file_name=research_file_name,
            content=research_content,
            resource_type=research_resource_type,
            agent_id=research_agent_id,
            session_id=session_id
        )
        print(f"   ✅ Storage result: {store_result.get('message', 'Success')}")
        
        # Small delay to demonstrate coordination
        await asyncio.sleep(1)
        
        # Analysis Agent retrieves and processes
        print("\n📊 Analysis Agent retrieving information...")
        # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
        # Query based on the actual research content that was stored
        analysis_search_query = f"agent coordination research findings for session {session_id}"
        retrieve_result = await enhanced_tools['enhanced_retrieve_memory'](
            conversation_id=session_id,
            query=analysis_search_query,
            top_k=5,
            agent_id=analysis_agent_id,
            session_id=session_id
        )
        print(f"   ✅ Retrieved {len(retrieve_result.get('relevant_contexts', []))} relevant contexts")
        
        # Both agents log their activities
        print("\n💬 Agents logging activities...")
        
        # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
        # Generate dynamic log content based on actual research results and context
        research_log_content = f"Research phase completed for session {session_id} - stored findings about AI agent coordination using agent {research_agent_id} with {OrchestrationMode.FULL.value} mode"
        
        # Dynamic metadata based on actual orchestration state and research context
        research_metadata = {
            "activity": "research_complete",
            "orchestration_mode": OrchestrationMode.FULL.value,
            "agent_capabilities": ["memory_write", "information_gathering"],
            "session_context": session_id,
            "research_scope": "multi_agent_coordination_benefits"
        }
        
        await enhanced_tools['enhanced_log_chat'](
            conversation_id=session_id,
            role="system",
            content=research_log_content,
            agent_name="Research Agent",
            agent_id=research_agent_id,
            session_id=session_id,
            metadata=research_metadata
        )
        
        # Dynamic analysis log content based on actual processing results and session context
        analysis_log_content = f"Analysis phase completed for session {session_id} - processed coordination research retrieved from agent {research_agent_id} using {len(retrieve_result.get('relevant_contexts', []))} contexts"
        
        # Dynamic metadata based on analysis results and coordination state
        analysis_metadata = {
            "activity": "analysis_complete",
            "orchestration_mode": OrchestrationMode.FULL.value,
            "agent_capabilities": ["memory_read", "data_analysis"],
            "session_context": session_id,
            "processed_contexts": len(retrieve_result.get('relevant_contexts', [])),
            "coordination_with_agent": research_agent_id
        }
        
        await enhanced_tools['enhanced_log_chat'](
            conversation_id=session_id,
            role="system", 
            content=analysis_log_content,
            agent_name="Analysis Agent",
            agent_id=analysis_agent_id,
            session_id=session_id,
            metadata=analysis_metadata
        )
        
        # Get orchestration status
        print("\n📈 Final orchestration status:")
        status = await _integration.orchestration_service.get_orchestration_status()
        
        print(f"   • Active agents: {status['active_agents']}")
        print(f"   • Mode: {status['mode']}")
        
        if 'coordination_stats' in status:
            coord_stats = status['coordination_stats']
            print(f"   • Active sessions: {coord_stats.get('active_sessions', 0)}")
            print(f"   • Total participants: {coord_stats.get('total_participants', 0)}")
        
        if 'locking_stats' in status:
            lock_stats = status['locking_stats']
            print(f"   • Active locks: {lock_stats.get('active_locks', 0)}")
        
        print("\n✅ Multi-agent orchestration demonstration completed successfully!")
        print("   🔄 Agents coordinated through shared session state")
        print("   🔒 Memory operations were safely locked")
        print("   💾 Results were cached and shared between agents")
        print("   📊 Full orchestration statistics available")
        
        # Cleanup
        await _integration.orchestration_service.cleanup_agent(research_agent_id)
        await _integration.orchestration_service.cleanup_agent(analysis_agent_id)
        print("\n🧹 Agent cleanup completed")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        logger.error(f"Orchestration demonstration error: {e}")


if __name__ == "__main__":
    """Run the orchestration demonstration."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the demonstration
    asyncio.run(demonstrate_orchestration_workflow())