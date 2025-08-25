"""
Comprehensive TDD tests for Agent State Operations extraction.
Tests state creation and transitions with LTMC tools integration.

Following TDD methodology: Tests written FIRST before extraction.
AgentStateOperations will handle create_agent_state and transition_agent_state.
MANDATORY: Uses ALL required LTMC tools (memory_action, graph_action, logging integration).
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestAgentStateOperations:
    """Test AgentStateOperations class - to be extracted from agent_state_manager.py"""
    
    def test_agent_state_operations_creation(self):
        """Test AgentStateOperations can be instantiated"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        
        # Mock core and dependencies
        mock_core = Mock()
        mock_core.coordination_id = "ops_test"
        mock_core.conversation_id = "ops_conv"
        mock_core.agent_states = {}
        
        mock_validator = Mock()
        mock_logging = Mock()
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        
        assert hasattr(operations, 'core')
        assert hasattr(operations, 'validator')
        assert hasattr(operations, 'logging')
        assert operations.core == mock_core
    
    @patch('ltms.coordination.agent_state_operations.memory_action')
    @patch('ltms.coordination.agent_state_operations.graph_action')
    def test_create_agent_state_success(self, mock_graph, mock_memory):
        """Test successful agent state creation with LTMC tools"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup LTMC tool mocks - MANDATORY
        mock_memory.return_value = {'success': True, 'doc_id': 123}
        mock_graph.return_value = {'success': True}
        
        # Setup core and dependencies
        mock_core = Mock()
        mock_core.coordination_id = "create_test"
        mock_core.conversation_id = "create_conv"
        mock_core.agent_states = {}
        
        mock_validator = Mock()
        mock_validator.validate_state_data.return_value = (True, None)
        
        mock_logging = Mock()
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        
        # Test state creation
        state_data = {"task": "test_creation", "priority": "high"}
        result = operations.create_agent_state("test_agent", AgentStatus.INITIALIZING, state_data)
        
        # Verify success
        assert result is True
        
        # Verify validator was called
        mock_validator.validate_state_data.assert_called_once_with(state_data)
        
        # Verify state was stored in core
        assert "test_agent" in mock_core.agent_states
        stored_snapshot = mock_core.agent_states["test_agent"]
        assert stored_snapshot.agent_id == "test_agent"
        assert stored_snapshot.status == AgentStatus.INITIALIZING
        assert stored_snapshot.state_data == state_data
        
        # Verify LTMC tools were called - MANDATORY
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert f'agent_state_test_agent_' in memory_call[1]['file_name']
        assert 'agent_state' in memory_call[1]['tags']
        assert memory_call[1]['conversation_id'] == 'create_conv'
        
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['action'] == 'link'
        assert 'state_manager_create_test' == graph_call[1]['source_entity']
        assert 'agent_test_agent' == graph_call[1]['target_entity']
        assert graph_call[1]['relationship'] == 'manages_state'
    
    def test_create_agent_state_validation_failure(self):
        """Test agent state creation with validation failure"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup core and dependencies
        mock_core = Mock()
        mock_core.agent_states = {}
        
        mock_validator = Mock()
        mock_validator.validate_state_data.return_value = (False, "Invalid state structure")
        
        mock_logging = Mock()
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        
        # Test failed creation
        state_data = {"invalid": "data"}
        result = operations.create_agent_state("fail_agent", AgentStatus.ACTIVE, state_data)
        
        # Verify failure
        assert result is False
        assert "fail_agent" not in mock_core.agent_states
    
    @patch('ltms.coordination.agent_state_operations.memory_action')
    @patch('ltms.coordination.agent_state_operations.graph_action')
    def test_transition_agent_state_success(self, mock_graph, mock_memory):
        """Test successful agent state transition with LTMC tools"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateTransition, StateSnapshot
        
        # Setup LTMC tool mocks - MANDATORY
        mock_memory.return_value = {'success': True, 'doc_id': 456}
        mock_graph.return_value = {'success': True}
        
        # Setup existing state
        existing_snapshot = StateSnapshot(
            agent_id="transition_agent",
            status=AgentStatus.INITIALIZING,
            state_data={"current": "initializing"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="transition_test",
            conversation_id="transition_conv",
            metadata={"version": "1.0"}
        )
        
        mock_core = Mock()
        mock_core.coordination_id = "transition_test"
        mock_core.conversation_id = "transition_conv" 
        mock_core.agent_states = {"transition_agent": existing_snapshot}
        
        mock_validator = Mock()
        mock_validator.validate_transition.return_value = True
        
        mock_logging = Mock()
        mock_observer = Mock()
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        operations.observer = mock_observer
        
        # Test transition
        transition_data = {"state_updates": {"current": "active", "task_started": True}}
        result = operations.transition_agent_state(
            "transition_agent",
            AgentStatus.ACTIVE,
            StateTransition.ACTIVATE,
            transition_data
        )
        
        # Verify success
        assert result is True
        
        # Verify validator was called
        mock_validator.validate_transition.assert_called_once_with(
            AgentStatus.INITIALIZING, AgentStatus.ACTIVE
        )
        
        # Verify new state was stored
        new_snapshot = mock_core.agent_states["transition_agent"]
        assert new_snapshot.status == AgentStatus.ACTIVE
        assert new_snapshot.state_data["current"] == "active"
        assert new_snapshot.state_data["task_started"] is True
        
        # Verify logging was called
        mock_logging.log_transition.assert_called_once()
        log_call = mock_logging.log_transition.call_args
        assert log_call[0][0] == "transition_agent"  # agent_id
        assert log_call[0][1] == AgentStatus.INITIALIZING  # from_status
        assert log_call[0][2] == AgentStatus.ACTIVE  # to_status
        assert log_call[0][4] is True  # success
        
        # Verify observer was notified
        mock_observer.notify_observers.assert_called_once_with(
            "transition_agent", AgentStatus.INITIALIZING, AgentStatus.ACTIVE
        )
        
        # Verify LTMC tools were called - MANDATORY
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'state_transition_transition_agent_' in memory_call[1]['file_name']
        assert 'state_transition' in memory_call[1]['tags']
        
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['action'] == 'link'
        assert 'agent_transition_agent' == graph_call[1]['source_entity']
        assert 'state_active' == graph_call[1]['target_entity']
        assert graph_call[1]['relationship'] == 'transitions_to'
    
    def test_transition_agent_state_validation_failure(self):
        """Test agent state transition with validation failure"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateTransition, StateSnapshot
        
        # Setup existing state
        existing_snapshot = StateSnapshot(
            agent_id="invalid_transition_agent",
            status=AgentStatus.COMPLETED,
            state_data={"task": "completed"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="invalid_test",
            conversation_id="invalid_conv",
            metadata={}
        )
        
        mock_core = Mock()
        mock_core.agent_states = {"invalid_transition_agent": existing_snapshot}
        
        mock_validator = Mock()
        mock_validator.validate_transition.return_value = False
        
        mock_logging = Mock()
        mock_performance_metrics = {"validation_errors": 0}
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        operations.performance_metrics = mock_performance_metrics
        
        # Test invalid transition
        result = operations.transition_agent_state(
            "invalid_transition_agent",
            AgentStatus.INITIALIZING,  # Invalid: can't go from COMPLETED back to INITIALIZING
            StateTransition.ACTIVATE,
            {}
        )
        
        # Verify failure
        assert result is False
        
        # Verify error was logged
        mock_logging.log_transition.assert_called_once()
        log_call = mock_logging.log_transition.call_args
        assert log_call[0][4] is False  # success = False
        assert "Invalid transition" in log_call[0][5]  # error_message
        
        # Verify performance metrics updated
        assert mock_performance_metrics["validation_errors"] == 1
    
    def test_transition_agent_state_nonexistent_agent(self):
        """Test transition for nonexistent agent"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateTransition
        
        mock_core = Mock()
        mock_core.agent_states = {}  # Empty
        
        mock_validator = Mock()
        mock_logging = Mock()
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        
        # Test transition for nonexistent agent
        result = operations.transition_agent_state(
            "nonexistent_agent",
            AgentStatus.ACTIVE,
            StateTransition.ACTIVATE
        )
        
        # Verify failure
        assert result is False
    
    @patch('ltms.coordination.agent_state_operations.memory_action')
    @patch('ltms.coordination.agent_state_operations.graph_action')
    def test_performance_metrics_tracking(self, mock_graph, mock_memory):
        """Test performance metrics are properly tracked during transitions"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateTransition, StateSnapshot
        
        # Setup mocks
        mock_memory.return_value = {'success': True}
        mock_graph.return_value = {'success': True}
        
        existing_snapshot = StateSnapshot(
            agent_id="perf_agent",
            status=AgentStatus.WAITING,
            state_data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="perf_test",
            conversation_id="perf_conv",
            metadata={}
        )
        
        mock_core = Mock()
        mock_core.coordination_id = "perf_test"
        mock_core.conversation_id = "perf_conv"
        mock_core.agent_states = {"perf_agent": existing_snapshot}
        
        mock_validator = Mock()
        mock_validator.validate_transition.return_value = True
        
        mock_logging = Mock()
        mock_observer = Mock()
        
        performance_metrics = {
            "state_transitions": 0,
            "average_transition_time": 0.0
        }
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        operations.observer = mock_observer
        operations.performance_metrics = performance_metrics
        
        # Test transition with timing
        result = operations.transition_agent_state(
            "perf_agent",
            AgentStatus.ACTIVE,
            StateTransition.ACTIVATE
        )
        
        # Verify success and metrics updated
        assert result is True
        assert performance_metrics["state_transitions"] == 1
        assert performance_metrics["average_transition_time"] > 0.0
    
    @patch('ltms.coordination.agent_state_operations.memory_action')
    @patch('ltms.coordination.agent_state_operations.graph_action')
    def test_exception_handling_during_operations(self, mock_graph, mock_memory):
        """Test exception handling during state operations"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup memory to fail
        mock_memory.side_effect = Exception("LTMC storage failure")
        mock_graph.return_value = {'success': True}
        
        mock_core = Mock()
        mock_core.coordination_id = "exception_test"
        mock_core.agent_states = {}
        
        mock_validator = Mock()
        mock_validator.validate_state_data.return_value = (True, None)
        
        mock_logging = Mock()
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        
        # Test creation with LTMC failure
        result = operations.create_agent_state("exception_agent", AgentStatus.ACTIVE, {})
        
        # Should handle gracefully
        assert result is False
    
    @patch('ltms.coordination.agent_state_operations.memory_action')
    @patch('ltms.coordination.agent_state_operations.graph_action')
    def test_ltmc_storage_content_structure(self, mock_graph, mock_memory):
        """Test LTMC storage contains correct content structure"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_memory.return_value = {'success': True, 'doc_id': 789}
        mock_graph.return_value = {'success': True}
        
        mock_core = Mock()
        mock_core.coordination_id = "content_test"
        mock_core.conversation_id = "content_conv"
        mock_core.agent_states = {}
        
        mock_validator = Mock()
        mock_validator.validate_state_data.return_value = (True, None)
        
        mock_logging = Mock()
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        
        # Test state creation
        state_data = {"test": "content"}
        operations.create_agent_state("content_agent", AgentStatus.ACTIVE, state_data)
        
        # Verify memory content structure
        memory_call = mock_memory.call_args
        stored_content = json.loads(memory_call[1]['content'])
        
        required_fields = ['action', 'agent_id', 'snapshot']
        for field in required_fields:
            assert field in stored_content
        
        assert stored_content['action'] == 'create_agent_state'
        assert stored_content['agent_id'] == 'content_agent'
        
        snapshot = stored_content['snapshot']
        snapshot_fields = ['agent_id', 'status', 'state_data', 'timestamp', 'snapshot_id']
        for field in snapshot_fields:
            assert field in snapshot


class TestAgentStateOperationsIntegration:
    """Test AgentStateOperations integration scenarios"""
    
    @patch('ltms.coordination.agent_state_operations.memory_action')
    @patch('ltms.coordination.agent_state_operations.graph_action')
    def test_comprehensive_ltmc_tools_usage(self, mock_graph, mock_memory):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.agent_state_operations import AgentStateOperations
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_memory.return_value = {'success': True, 'doc_id': 999}
        mock_graph.return_value = {'success': True}
        
        mock_core = Mock()
        mock_core.coordination_id = "ltmc_comprehensive"
        mock_core.conversation_id = "ltmc_comprehensive_conv"
        mock_core.agent_states = {}
        
        mock_validator = Mock()
        mock_validator.validate_state_data.return_value = (True, None)
        
        mock_logging = Mock()
        
        operations = AgentStateOperations(mock_core, mock_validator, mock_logging)
        
        # Test state creation
        operations.create_agent_state("ltmc_agent", AgentStatus.INITIALIZING, {"ltmc": True})
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. memory_action - MANDATORY Tool 1
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert memory_call[1]['conversation_id'] == 'ltmc_comprehensive_conv'
        assert memory_call[1]['role'] == 'system'
        assert 'agent_state' in memory_call[1]['tags']
        assert 'ltmc_agent' in memory_call[1]['tags']
        
        # 2. graph_action - MANDATORY Tool 8
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['action'] == 'link'
        assert 'state_manager_' in graph_call[1]['source_entity']
        assert 'agent_ltmc_agent' == graph_call[1]['target_entity']
        assert graph_call[1]['relationship'] == 'manages_state'
        assert 'initial_status' in graph_call[1]['properties']


# Pytest fixtures for operations testing
@pytest.fixture
def mock_operations_dependencies():
    """Fixture providing mock dependencies for operations testing"""
    mock_core = Mock()
    mock_core.coordination_id = "fixture_ops_coord"
    mock_core.conversation_id = "fixture_ops_conv"
    mock_core.agent_states = {}
    
    mock_validator = Mock()
    mock_validator.validate_state_data.return_value = (True, None)
    mock_validator.validate_transition.return_value = True
    
    mock_logging = Mock()
    
    return {
        'core': mock_core,
        'validator': mock_validator,
        'logging': mock_logging
    }

@pytest.fixture
def agent_state_operations(mock_operations_dependencies):
    """Fixture providing AgentStateOperations instance"""
    from ltms.coordination.agent_state_operations import AgentStateOperations
    
    deps = mock_operations_dependencies
    return AgentStateOperations(deps['core'], deps['validator'], deps['logging'])

@pytest.fixture
def mock_all_ltmc_operations_tools():
    """Fixture providing mocks for all LTMC tools used in operations"""
    with patch.multiple(
        'ltms.coordination.agent_state_operations',
        memory_action=Mock(return_value={'success': True, 'doc_id': 888}),
        graph_action=Mock(return_value={'success': True})
    ) as mocks:
        yield mocks