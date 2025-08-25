"""
Comprehensive TDD tests for Agent State Core extraction.
Tests core state management and initialization with LTMC tools integration.

Following TDD methodology: Tests written FIRST before extraction.
AgentStateCore will handle core state management with memory_action and graph_action.
MANDATORY: Uses ALL required LTMC tools.
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestAgentStateCore:
    """Test AgentStateCore class - to be extracted from agent_state_manager.py"""
    
    def test_agent_state_core_creation(self):
        """Test AgentStateCore can be instantiated"""
        from ltms.coordination.agent_state_core import AgentStateCore
        
        coordination_id = "core_test"
        conversation_id = "core_conv"
        
        core = AgentStateCore(coordination_id, conversation_id)
        
        assert hasattr(core, 'coordination_id')
        assert hasattr(core, 'conversation_id')
        assert hasattr(core, 'agent_states')
        assert core.coordination_id == coordination_id
        assert core.conversation_id == conversation_id
        assert isinstance(core.agent_states, dict)
    
    @patch('ltms.coordination.agent_state_core.memory_action')
    @patch('ltms.coordination.agent_state_core.graph_action')
    def test_initialize_state_storage_ltmc_integration(self, mock_graph, mock_memory):
        """Test initialization with LTMC tools - MANDATORY"""
        from ltms.coordination.agent_state_core import AgentStateCore
        
        # Setup LTMC tool mocks
        mock_memory.return_value = {'success': True, 'doc_id': 123}
        mock_graph.return_value = {'success': True}
        
        coordination_id = "init_test"
        conversation_id = "init_conv"
        
        core = AgentStateCore(coordination_id, conversation_id)
        
        # Verify memory_action was called - MANDATORY LTMC tool
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert f'state_manager_init_{coordination_id}.json' in memory_call[1]['file_name']
        assert 'state_management' in memory_call[1]['tags']
        assert memory_call[1]['conversation_id'] == conversation_id
        assert memory_call[1]['role'] == 'system'
        
        # Verify graph_action was called - MANDATORY LTMC tool
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['action'] == 'link'
        assert f'coordination_{coordination_id}' == graph_call[1]['source_entity']
        assert f'state_manager_{coordination_id}' == graph_call[1]['target_entity']
        assert graph_call[1]['relationship'] == 'uses_state_manager'
    
    def test_get_agent_state_empty(self):
        """Test getting agent state when none exists"""
        from ltms.coordination.agent_state_core import AgentStateCore
        
        core = AgentStateCore("empty_test", "empty_conv")
        result = core.get_agent_state("nonexistent_agent")
        
        assert result is None
    
    def test_get_all_agent_states_empty(self):
        """Test getting all agent states when none exist"""
        from ltms.coordination.agent_state_core import AgentStateCore
        
        core = AgentStateCore("all_empty_test", "all_empty_conv")
        result = core.get_all_agent_states()
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_get_agents_by_status_empty(self):
        """Test getting agents by status when none exist"""
        from ltms.coordination.agent_state_core import AgentStateCore
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        core = AgentStateCore("status_empty_test", "status_empty_conv")
        result = core.get_agents_by_status(AgentStatus.ACTIVE)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('ltms.coordination.agent_state_core.memory_action')
    @patch('ltms.coordination.agent_state_core.graph_action')
    def test_add_agent_state_direct(self, mock_graph, mock_memory):
        """Test adding agent state directly to core storage"""
        from ltms.coordination.agent_state_core import AgentStateCore
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_memory.return_value = {'success': True}
        mock_graph.return_value = {'success': True}
        
        core = AgentStateCore("add_test", "add_conv")
        
        # Create test snapshot
        snapshot = StateSnapshot(
            agent_id="test_agent",
            status=AgentStatus.ACTIVE,
            state_data={"test": "data"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="add_test",
            conversation_id="add_conv",
            metadata={"test": True}
        )
        
        # Add state directly
        core.agent_states["test_agent"] = snapshot
        
        # Test retrieval
        result = core.get_agent_state("test_agent")
        assert result == snapshot
        
        all_states = core.get_all_agent_states()
        assert "test_agent" in all_states
        assert all_states["test_agent"] == snapshot
        
        active_agents = core.get_agents_by_status(AgentStatus.ACTIVE)
        assert "test_agent" in active_agents
    
    @patch('ltms.coordination.agent_state_core.memory_action')
    @patch('ltms.coordination.agent_state_core.graph_action')
    def test_multiple_agent_states_management(self, mock_graph, mock_memory):
        """Test managing multiple agent states"""
        from ltms.coordination.agent_state_core import AgentStateCore
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_memory.return_value = {'success': True}
        mock_graph.return_value = {'success': True}
        
        core = AgentStateCore("multi_test", "multi_conv")
        
        # Create multiple snapshots
        agents = ["agent_1", "agent_2", "agent_3"]
        statuses = [AgentStatus.ACTIVE, AgentStatus.WAITING, AgentStatus.ACTIVE]
        
        for i, (agent_id, status) in enumerate(zip(agents, statuses)):
            snapshot = StateSnapshot(
                agent_id=agent_id,
                status=status,
                state_data={"index": i},
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_id="multi_test",
                conversation_id="multi_conv",
                metadata={"agent_index": i}
            )
            core.agent_states[agent_id] = snapshot
        
        # Test retrieval operations
        all_states = core.get_all_agent_states()
        assert len(all_states) == 3
        
        active_agents = core.get_agents_by_status(AgentStatus.ACTIVE)
        assert len(active_agents) == 2
        assert "agent_1" in active_agents
        assert "agent_3" in active_agents
        
        waiting_agents = core.get_agents_by_status(AgentStatus.WAITING)
        assert len(waiting_agents) == 1
        assert "agent_2" in waiting_agents
    
    @patch('ltms.coordination.agent_state_core.memory_action')
    @patch('ltms.coordination.agent_state_core.graph_action') 
    def test_initialization_error_handling(self, mock_graph, mock_memory):
        """Test error handling during initialization"""
        from ltms.coordination.agent_state_core import AgentStateCore
        
        # Setup memory to fail
        mock_memory.side_effect = Exception("LTMC memory unavailable")
        mock_graph.return_value = {'success': True}
        
        with pytest.raises(Exception) as exc_info:
            AgentStateCore("error_test", "error_conv")
        
        assert "LTMC memory unavailable" in str(exc_info.value)
    
    @patch('ltms.coordination.agent_state_core.memory_action')
    @patch('ltms.coordination.agent_state_core.graph_action')
    def test_ltmc_storage_content_validation(self, mock_graph, mock_memory):
        """Test that LTMC storage contains correct content structure"""
        from ltms.coordination.agent_state_core import AgentStateCore
        
        # Setup mocks
        mock_memory.return_value = {'success': True, 'doc_id': 456}
        mock_graph.return_value = {'success': True}
        
        coordination_id = "content_test"
        conversation_id = "content_conv"
        
        core = AgentStateCore(coordination_id, conversation_id)
        
        # Verify memory content structure
        memory_call = mock_memory.call_args
        stored_content = json.loads(memory_call[1]['content'])
        
        required_fields = ['state_management', 'coordination_id', 'conversation_id', 'initialization_time', 'framework_version']
        for field in required_fields:
            assert field in stored_content
        
        assert stored_content['state_management'] == 'initialized'
        assert stored_content['coordination_id'] == coordination_id
        assert stored_content['conversation_id'] == conversation_id
        assert stored_content['framework_version'] == '1.0.0'
    
    @patch('ltms.coordination.agent_state_core.memory_action')
    @patch('ltms.coordination.agent_state_core.graph_action')
    def test_copy_behavior_get_all_states(self, mock_graph, mock_memory):
        """Test that get_all_agent_states returns a copy, not reference"""
        from ltms.coordination.agent_state_core import AgentStateCore
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_memory.return_value = {'success': True}
        mock_graph.return_value = {'success': True}
        
        core = AgentStateCore("copy_test", "copy_conv")
        
        # Add a test state
        snapshot = StateSnapshot(
            agent_id="copy_agent",
            status=AgentStatus.COMPLETED,
            state_data={"original": True},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="copy_test",
            conversation_id="copy_conv",
            metadata={}
        )
        core.agent_states["copy_agent"] = snapshot
        
        # Get copy
        states_copy = core.get_all_agent_states()
        
        # Modify copy
        states_copy["new_agent"] = "should_not_affect_original"
        
        # Verify original unchanged
        assert "new_agent" not in core.agent_states
        assert len(core.agent_states) == 1


class TestAgentStateCoreIntegration:
    """Test AgentStateCore integration scenarios"""
    
    @patch('ltms.coordination.agent_state_core.memory_action')
    @patch('ltms.coordination.agent_state_core.graph_action')
    def test_integration_with_state_components(self, mock_graph, mock_memory):
        """Test integration with other state management components"""
        from ltms.coordination.agent_state_core import AgentStateCore
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup mocks
        mock_memory.return_value = {'success': True}
        mock_graph.return_value = {'success': True}
        
        core = AgentStateCore("integration_test", "integration_conv")
        
        # Verify core can work with StateSnapshot objects
        snapshot = StateSnapshot(
            agent_id="integration_agent",
            status=AgentStatus.INITIALIZING,
            state_data={"component": "state_core"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="integration_test", 
            conversation_id="integration_conv",
            metadata={"integration_test": True}
        )
        
        # Test integration
        core.agent_states["integration_agent"] = snapshot
        retrieved = core.get_agent_state("integration_agent")
        
        assert retrieved.agent_id == "integration_agent"
        assert retrieved.status == AgentStatus.INITIALIZING
        assert retrieved.state_data["component"] == "state_core"
    
    @patch('ltms.coordination.agent_state_core.memory_action')
    @patch('ltms.coordination.agent_state_core.graph_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_graph, mock_memory):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.agent_state_core import AgentStateCore
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_memory.return_value = {'success': True, 'doc_id': 789}
        mock_graph.return_value = {'success': True}
        
        coordination_id = "ltmc_comprehensive"
        conversation_id = "ltmc_comprehensive_conv"
        
        core = AgentStateCore(coordination_id, conversation_id)
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. memory_action - MANDATORY Tool 1
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert memory_call[1]['conversation_id'] == conversation_id
        assert memory_call[1]['role'] == 'system'
        assert 'state_management' in memory_call[1]['tags']
        assert coordination_id in memory_call[1]['tags']
        
        # 2. graph_action - MANDATORY Tool 8
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['action'] == 'link'
        assert 'coordination_' in graph_call[1]['source_entity']
        assert 'state_manager_' in graph_call[1]['target_entity'] 
        assert graph_call[1]['relationship'] == 'uses_state_manager'
        assert 'initialization_time' in graph_call[1]['properties']


# Pytest fixtures for core testing
@pytest.fixture
def mock_coordination_ids():
    """Fixture providing test coordination IDs"""
    return {
        'coordination_id': 'fixture_coord_test',
        'conversation_id': 'fixture_conv_test'
    }

@pytest.fixture
def agent_state_core(mock_coordination_ids):
    """Fixture providing AgentStateCore instance"""
    from ltms.coordination.agent_state_core import AgentStateCore
    
    with patch('ltms.coordination.agent_state_core.memory_action', return_value={'success': True}):
        with patch('ltms.coordination.agent_state_core.graph_action', return_value={'success': True}):
            return AgentStateCore(
                mock_coordination_ids['coordination_id'],
                mock_coordination_ids['conversation_id']
            )

@pytest.fixture
def sample_state_snapshot():
    """Fixture providing sample StateSnapshot for testing"""
    from ltms.coordination.agent_state_models import StateSnapshot
    from ltms.coordination.agent_coordination_models import AgentStatus
    
    return StateSnapshot(
        agent_id="fixture_agent",
        status=AgentStatus.ACTIVE,
        state_data={"fixture": True, "test_data": "sample"},
        timestamp=datetime.now(timezone.utc).isoformat(),
        task_id="fixture_coord_test",
        conversation_id="fixture_conv_test", 
        metadata={"created_by": "fixture", "version": "test"}
    )

@pytest.fixture  
def mock_all_ltmc_core_tools():
    """Fixture providing mocks for all LTMC tools used in core"""
    with patch.multiple(
        'ltms.coordination.agent_state_core',
        memory_action=Mock(return_value={'success': True, 'doc_id': 999}),
        graph_action=Mock(return_value={'success': True})
    ) as mocks:
        yield mocks