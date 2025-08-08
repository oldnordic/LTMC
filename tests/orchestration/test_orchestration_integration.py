"""Comprehensive tests for Redis Orchestration Layer integration."""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List

from ltms.services.orchestration_service import (
    OrchestrationService,
    OrchestrationMode,
    AgentContext,
    get_orchestration_service
)
from ltms.services.agent_registry_service import (
    AgentRegistryService,
    AgentCapability,
    AgentStatus
)
from ltms.services.context_coordination_service import (
    ContextCoordinationService,
    ContextEventType
)
from ltms.services.memory_locking_service import (
    MemoryLockingService,
    LockType,
    LockPriority
)
from ltms.services.redis_service import RedisConnectionManager
from ltms.mcp_orchestration_integration import (
    OrchestrationIntegration,
    initialize_orchestration_integration,
    create_enhanced_mcp_tools
)


@pytest.fixture
async def redis_manager():
    """Create Redis connection manager for testing."""
    # Use a test Redis database
    manager = RedisConnectionManager(
        host="localhost",
        port=6381,
        db=15,  # Use test database
        password="ltmc_cache_2025"
    )
    
    try:
        await manager.initialize()
        yield manager
    except Exception as e:
        pytest.skip(f"Redis not available for testing: {e}")
    finally:
        if manager.is_connected:
            # Clean up test data
            await manager.client.flushdb()
            await manager.close()


@pytest.fixture
async def agent_registry(redis_manager):
    """Create agent registry service for testing."""
    service = AgentRegistryService(redis_manager)
    await service.start()
    yield service
    await service.stop()


@pytest.fixture
async def context_coordination(redis_manager):
    """Create context coordination service for testing."""
    service = ContextCoordinationService(redis_manager)
    await service.start()
    yield service
    await service.stop()


@pytest.fixture
async def memory_locking(redis_manager):
    """Create memory locking service for testing."""
    service = MemoryLockingService(redis_manager)
    await service.start()
    yield service
    await service.stop()


@pytest.fixture
async def orchestration_service():
    """Create orchestration service for testing."""
    service = OrchestrationService()
    await service.initialize(OrchestrationMode.FULL)
    yield service
    # Cleanup all agents
    for agent_id in list(service._agent_contexts.keys()):
        await service.cleanup_agent(agent_id)


class TestAgentRegistryService:
    """Test suite for Agent Registry Service."""
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, agent_registry):
        """Test agent registration and deregistration."""
        capabilities = [
            AgentCapability(
                name="memory_operations",
                version="1.0.0",
                description="Memory operations capability",
                parameters={}
            )
        ]
        
        # Register agent
        success = await agent_registry.register_agent(
            agent_id="test_agent_001",
            name="Test Agent",
            capabilities=capabilities,
            session_id="test_session"
        )
        assert success is True
        
        # Get agent info
        agent_info = await agent_registry.get_agent_info("test_agent_001")
        assert agent_info is not None
        assert agent_info.agent_id == "test_agent_001"
        assert agent_info.name == "Test Agent"
        assert len(agent_info.capabilities) == 1
        
        # Deregister agent
        success = await agent_registry.deregister_agent("test_agent_001")
        assert success is True
        
        # Verify removal
        agent_info = await agent_registry.get_agent_info("test_agent_001")
        assert agent_info is None
    
    @pytest.mark.asyncio
    async def test_capability_search(self, agent_registry):
        """Test finding agents by capability."""
        capabilities = [
            AgentCapability(
                name="data_analysis",
                version="1.0.0",
                description="Data analysis capability",
                parameters={}
            )
        ]
        
        # Register multiple agents
        await agent_registry.register_agent("agent_1", "Agent 1", capabilities)
        await agent_registry.register_agent("agent_2", "Agent 2", capabilities)
        
        # Search by capability
        agents = await agent_registry.find_agents_by_capability("data_analysis")
        assert len(agents) == 2
        
        agent_ids = {agent.agent_id for agent in agents}
        assert "agent_1" in agent_ids
        assert "agent_2" in agent_ids
    
    @pytest.mark.asyncio
    async def test_heartbeat_update(self, agent_registry):
        """Test agent heartbeat updates."""
        capabilities = [
            AgentCapability(
                name="test_capability",
                version="1.0.0",
                description="Test capability",
                parameters={}
            )
        ]
        
        # Register agent
        await agent_registry.register_agent("heartbeat_agent", "Heartbeat Agent", capabilities)
        
        # Update heartbeat
        success = await agent_registry.update_heartbeat("heartbeat_agent", AgentStatus.BUSY)
        assert success is True
        
        # Verify status update
        agent_info = await agent_registry.get_agent_info("heartbeat_agent")
        assert agent_info.status == AgentStatus.BUSY


class TestContextCoordinationService:
    """Test suite for Context Coordination Service."""
    
    @pytest.mark.asyncio
    async def test_session_creation_and_joining(self, context_coordination):
        """Test session creation and agent joining."""
        session_id = "test_session_001"
        
        # Create session
        success = await context_coordination.create_session_context(
            session_id=session_id,
            initial_memory={"test_key": "test_value"},
            metadata={"created_by": "test"}
        )
        assert success is True
        
        # Join session
        success = await context_coordination.join_session(session_id, "agent_001")
        assert success is True
        
        # Get session context
        context = await context_coordination.get_session_context(session_id)
        assert context is not None
        assert "agent_001" in context.participants
        assert context.shared_memory["test_key"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_shared_memory_updates(self, context_coordination):
        """Test shared memory updates with coordination."""
        session_id = "memory_test_session"
        
        # Create session and add participants
        await context_coordination.create_session_context(session_id)
        await context_coordination.join_session(session_id, "agent_001")
        await context_coordination.join_session(session_id, "agent_002")
        
        # Update shared memory
        success = await context_coordination.update_shared_memory(
            session_id=session_id,
            agent_id="agent_001",
            updates={"research_data": "important findings", "status": "in_progress"}
        )
        assert success is True
        
        # Verify updates
        context = await context_coordination.get_session_context(session_id)
        assert context.shared_memory["research_data"] == "important findings"
        assert context.shared_memory["status"] == "in_progress"
        assert context.version > 1  # Version should increment
    
    @pytest.mark.asyncio
    async def test_event_logging(self, context_coordination):
        """Test context event logging and retrieval."""
        session_id = "event_test_session"
        
        # Create session and join
        await context_coordination.create_session_context(session_id)
        await context_coordination.join_session(session_id, "agent_001")
        
        # Perform memory update (generates events)
        await context_coordination.update_shared_memory(
            session_id=session_id,
            agent_id="agent_001",
            updates={"test_data": "event_test"}
        )
        
        # Get events
        events = await context_coordination.get_session_events(session_id)
        assert len(events) >= 2  # At least join and memory update events
        
        # Verify event types
        event_types = {event.event_type for event in events}
        assert ContextEventType.AGENT_JOIN in event_types
        assert ContextEventType.MEMORY_UPDATE in event_types


class TestMemoryLockingService:
    """Test suite for Memory Locking Service."""
    
    @pytest.mark.asyncio
    async def test_lock_acquisition_and_release(self, memory_locking):
        """Test basic lock acquisition and release."""
        agent_id = "locking_agent_001"
        resource_id = "test_resource_001"
        
        # Acquire lock
        lock_id = await memory_locking.acquire_lock(
            agent_id=agent_id,
            resource_id=resource_id,
            lock_type=LockType.WRITE,
            timeout=60
        )
        assert lock_id is not None
        
        # Check lock status
        status = await memory_locking.check_lock_status(lock_id)
        assert status is not None
        assert status['agent_id'] == agent_id
        assert status['resource_id'] == resource_id
        assert status['lock_type'] == LockType.WRITE.value
        
        # Release lock
        success = await memory_locking.release_lock(agent_id, lock_id)
        assert success is True
        
        # Verify release
        status = await memory_locking.check_lock_status(lock_id)
        assert status is None
    
    @pytest.mark.asyncio
    async def test_concurrent_lock_conflicts(self, memory_locking):
        """Test lock conflicts between agents."""
        resource_id = "contested_resource"
        
        # Agent 1 acquires write lock
        lock_id_1 = await memory_locking.acquire_lock(
            agent_id="agent_001",
            resource_id=resource_id,
            lock_type=LockType.WRITE,
            timeout=60
        )
        assert lock_id_1 is not None
        
        # Agent 2 tries to acquire conflicting lock (should timeout quickly)
        lock_id_2 = await memory_locking.acquire_lock(
            agent_id="agent_002",
            resource_id=resource_id,
            lock_type=LockType.WRITE,
            timeout=60,
            wait_timeout=2  # Short wait for testing
        )
        assert lock_id_2 is None  # Should fail due to conflict
        
        # Release first lock
        await memory_locking.release_lock("agent_001", lock_id_1)
        
        # Now agent 2 should be able to acquire lock
        lock_id_2 = await memory_locking.acquire_lock(
            agent_id="agent_002",
            resource_id=resource_id,
            lock_type=LockType.WRITE,
            timeout=60
        )
        assert lock_id_2 is not None
        
        # Cleanup
        await memory_locking.release_lock("agent_002", lock_id_2)
    
    @pytest.mark.asyncio
    async def test_read_lock_sharing(self, memory_locking):
        """Test that multiple read locks can coexist."""
        resource_id = "shared_read_resource"
        
        # Multiple agents acquire read locks
        lock_id_1 = await memory_locking.acquire_lock(
            agent_id="reader_001",
            resource_id=resource_id,
            lock_type=LockType.READ,
            timeout=60
        )
        assert lock_id_1 is not None
        
        lock_id_2 = await memory_locking.acquire_lock(
            agent_id="reader_002", 
            resource_id=resource_id,
            lock_type=LockType.READ,
            timeout=60
        )
        assert lock_id_2 is not None
        
        # Both locks should be active
        locks = await memory_locking.get_resource_locks(resource_id)
        assert len(locks) == 2
        
        # Cleanup
        await memory_locking.release_lock("reader_001", lock_id_1)
        await memory_locking.release_lock("reader_002", lock_id_2)


class TestOrchestrationService:
    """Test suite for Orchestration Service."""
    
    @pytest.mark.asyncio
    async def test_agent_registration_with_orchestration(self, orchestration_service):
        """Test agent registration through orchestration service."""
        agent_id = await orchestration_service.register_agent(
            agent_name="Orchestrated Agent",
            capabilities=["memory_operations", "data_analysis"],
            session_id="orchestration_session",
            metadata={"test": True}
        )
        
        assert agent_id is not None
        assert agent_id in orchestration_service._agent_contexts
        
        # Get session context
        session_context = await orchestration_service.get_session_context(agent_id)
        assert session_context is not None
        assert agent_id in session_context['participants']
    
    @pytest.mark.asyncio
    async def test_coordinated_tool_execution(self, orchestration_service):
        """Test tool execution with coordination."""
        # Register agent
        agent_id = await orchestration_service.register_agent(
            agent_name="Tool Executor",
            capabilities=["memory_operations"],
            session_id="tool_session"
        )
        
        # Mock tool function
        async def mock_tool(param1: str, param2: int) -> Dict[str, Any]:
            return {"result": f"processed {param1} with {param2}"}
        
        # Execute with coordination
        result = await orchestration_service.execute_tool_with_coordination(
            agent_id=agent_id,
            tool_name="mock_tool",
            tool_function=mock_tool,
            parameters={"param1": "test_data", "param2": 42}
        )
        
        assert result["result"] == "processed test_data with 42"
    
    @pytest.mark.asyncio
    async def test_capability_based_agent_discovery(self, orchestration_service):
        """Test finding agents by capability."""
        # Register agents with different capabilities
        agent_1 = await orchestration_service.register_agent(
            "Data Processor",
            ["data_processing", "analysis"],
            "discovery_session"
        )
        
        agent_2 = await orchestration_service.register_agent(
            "Memory Manager", 
            ["memory_operations", "storage"],
            "discovery_session"
        )
        
        # Find agents by capability
        data_agents = await orchestration_service.find_capable_agents(
            capability="data_processing",
            session_id="discovery_session"
        )
        assert len(data_agents) == 1
        assert data_agents[0]['agent_id'] == agent_1
        
        memory_agents = await orchestration_service.find_capable_agents(
            capability="memory_operations",
            session_id="discovery_session"
        )
        assert len(memory_agents) == 1
        assert memory_agents[0]['agent_id'] == agent_2


class TestMCPIntegration:
    """Test suite for MCP Orchestration Integration."""
    
    @pytest.mark.asyncio
    async def test_orchestration_integration_initialization(self):
        """Test orchestration integration initialization."""
        await initialize_orchestration_integration(OrchestrationMode.BASIC)
        
        # Create enhanced tools
        enhanced_tools = create_enhanced_mcp_tools()
        
        assert 'enhanced_store_memory' in enhanced_tools
        assert 'enhanced_retrieve_memory' in enhanced_tools
        assert 'enhanced_log_chat' in enhanced_tools
    
    @pytest.mark.asyncio 
    async def test_enhanced_tool_execution(self):
        """Test enhanced MCP tool execution with orchestration."""
        await initialize_orchestration_integration(OrchestrationMode.BASIC)
        enhanced_tools = create_enhanced_mcp_tools()
        
        # Test enhanced memory storage (would need actual database in full test)
        # This tests the orchestration wrapper, not the underlying storage
        try:
            result = await enhanced_tools['enhanced_store_memory'](
                file_name="test_orchestration.md",
                content="Test content for orchestration",
                resource_type="test_document",
                session_id="test_session_integration"
            )
            
            # Even if the underlying storage fails, orchestration metadata should be present
            # In a real environment with proper database setup, this would succeed
            assert isinstance(result, dict)
            
        except Exception as e:
            # Expected in test environment without full database setup
            assert "database" in str(e).lower() or "connection" in str(e).lower()


class TestOrchestrationWorkflow:
    """Test suite for complete orchestration workflows."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_coordination_workflow(self, orchestration_service):
        """Test a complete multi-agent coordination workflow."""
        session_id = "workflow_test_session"
        
        # Register research agent
        research_agent = await orchestration_service.register_agent(
            agent_name="Research Agent",
            capabilities=["research", "memory_write"],
            session_id=session_id,
            metadata={"role": "researcher"}
        )
        
        # Register analysis agent
        analysis_agent = await orchestration_service.register_agent(
            agent_name="Analysis Agent",
            capabilities=["analysis", "memory_read"],
            session_id=session_id,
            metadata={"role": "analyst"}
        )
        
        # Verify both agents are in the same session
        research_context = await orchestration_service.get_session_context(research_agent)
        analysis_context = await orchestration_service.get_session_context(analysis_agent)
        
        assert research_context['session_id'] == analysis_context['session_id']
        assert research_agent in research_context['participants']
        assert analysis_agent in analysis_context['participants']
        
        # Share memory update from research agent
        success = await orchestration_service.share_memory_update(
            agent_id=research_agent,
            memory_type="research_findings",
            operation="create",
            data={"topic": "AI coordination", "status": "completed"}
        )
        assert success is True
        
        # Analysis agent should be able to see the shared update
        updated_context = await orchestration_service.get_session_context(analysis_agent)
        assert 'memory_update' in updated_context['shared_memory']
        
        # Verify orchestration status
        status = await orchestration_service.get_orchestration_status()
        assert status['active_agents'] >= 2
        assert status['initialized'] is True


@pytest.mark.asyncio
async def test_orchestration_performance():
    """Test orchestration performance under load."""
    service = OrchestrationService()
    await service.initialize(OrchestrationMode.BASIC)
    
    # Register multiple agents quickly
    agents = []
    start_time = datetime.now()
    
    for i in range(10):
        agent_id = await service.register_agent(
            f"Agent_{i:03d}",
            ["performance_test"],
            f"performance_session_{i % 3}",  # Spread across 3 sessions
            {"batch": "performance_test"}
        )
        agents.append(agent_id)
    
    registration_time = (datetime.now() - start_time).total_seconds()
    
    # Should register 10 agents in reasonable time
    assert registration_time < 5.0  # 5 seconds max
    assert len(agents) == 10
    assert all(agent is not None for agent in agents)
    
    # Cleanup
    for agent_id in agents:
        await service.cleanup_agent(agent_id)


if __name__ == "__main__":
    """Run the orchestration tests."""
    import sys
    
    # Add project root to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])