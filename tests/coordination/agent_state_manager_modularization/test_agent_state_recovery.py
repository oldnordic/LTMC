"""
Comprehensive TDD tests for Agent State Recovery extraction.
Tests recovery operations and performance monitoring with LTMC tools integration.

Following TDD methodology: Tests written FIRST before extraction.
AgentStateRecovery will handle recover_agent_state and performance metrics.
MANDATORY: Uses ALL required LTMC tools (chat_action, todo_action for recovery coordination).
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Callable
from unittest.mock import Mock, patch, MagicMock


class TestAgentStateRecovery:
    """Test AgentStateRecovery class - to be extracted from agent_state_manager.py"""
    
    def test_agent_state_recovery_creation(self):
        """Test AgentStateRecovery can be instantiated"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        
        # Mock dependencies
        mock_core = Mock()
        mock_operations = Mock()
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        assert hasattr(recovery, 'core')
        assert hasattr(recovery, 'operations')
        assert hasattr(recovery, 'observer')
        assert hasattr(recovery, 'performance_metrics')
        assert recovery.core == mock_core
    
    @patch('ltms.coordination.agent_state_recovery.chat_action')
    @patch('ltms.coordination.agent_state_recovery.todo_action')
    def test_recover_agent_state_success(self, mock_todo, mock_chat):
        """Test successful agent recovery with LTMC tools integration"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot, StateTransition
        
        # Setup LTMC tool mocks - MANDATORY
        mock_chat.return_value = {'success': True}
        mock_todo.return_value = {'success': True, 'task_id': 'recovery_task_123'}
        
        # Setup error state snapshot
        error_snapshot = StateSnapshot(
            agent_id="error_agent",
            status=AgentStatus.ERROR,
            state_data={"task": "failed"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="recovery_test",
            conversation_id="recovery_conv",
            metadata={"error_message": "Process failed", "error_time": "2025-08-24T10:30:00Z"}
        )
        
        # Setup core
        mock_core = Mock()
        mock_core.coordination_id = "recovery_test"
        mock_core.conversation_id = "recovery_conv"
        mock_core.agent_states = {"error_agent": error_snapshot}
        
        # Setup operations
        mock_operations = Mock()
        mock_operations.transition_agent_state.return_value = True
        
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test recovery
        result = recovery.recover_agent_state("error_agent")
        
        # Verify success
        assert result is True
        
        # Verify operations was called for transition
        mock_operations.transition_agent_state.assert_called_once()
        transition_call = mock_operations.transition_agent_state.call_args
        assert transition_call[0][0] == "error_agent"  # agent_id
        assert transition_call[0][1] == AgentStatus.INITIALIZING  # target status
        assert transition_call[0][2] == StateTransition.RETRY  # transition type
        
        # Verify recovery data structure
        transition_data = transition_call[0][3]
        assert "state_updates" in transition_data
        state_updates = transition_data["state_updates"]
        assert state_updates["recovery_attempt"] is True
        assert "Process failed" in state_updates["original_error"]
        assert "recovery_time" in state_updates
        
        # Verify performance metrics updated
        assert recovery.performance_metrics["recovery_attempts"] == 1
        
        # Verify LTMC tools were called - MANDATORY
        # chat_action for recovery logging
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert 'Agent recovery initiated' in chat_call[1]['message']
        assert chat_call[1]['conversation_id'] == 'recovery_conv'
        assert chat_call[1]['role'] == 'system'
        
        # todo_action for recovery task tracking
        mock_todo.assert_called_once()
        todo_call = mock_todo.call_args
        assert todo_call[1]['action'] == 'add'
        assert 'Recovery: error_agent' in todo_call[1]['task']
        assert 'agent_recovery' in todo_call[1]['tags']
    
    def test_recover_agent_state_not_found(self):
        """Test recovery attempt for nonexistent agent"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        
        mock_core = Mock()
        mock_core.agent_states = {}  # Empty
        
        mock_operations = Mock()
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test recovery for nonexistent agent
        result = recovery.recover_agent_state("nonexistent_agent")
        
        # Verify failure
        assert result is False
    
    def test_recover_agent_state_not_in_error(self):
        """Test recovery attempt for agent not in error state"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup active state snapshot
        active_snapshot = StateSnapshot(
            agent_id="active_agent",
            status=AgentStatus.ACTIVE,
            state_data={"task": "running"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="recovery_test",
            conversation_id="recovery_conv",
            metadata={}
        )
        
        mock_core = Mock()
        mock_core.agent_states = {"active_agent": active_snapshot}
        
        mock_operations = Mock()
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test recovery for non-error agent
        result = recovery.recover_agent_state("active_agent")
        
        # Should return True (no recovery needed)
        assert result is True
        
        # Operations should not be called
        mock_operations.transition_agent_state.assert_not_called()
    
    @patch('ltms.coordination.agent_state_recovery.chat_action')
    @patch('ltms.coordination.agent_state_recovery.todo_action')
    def test_recover_agent_state_transition_failure(self, mock_todo, mock_chat):
        """Test recovery when transition fails"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup LTMC tool mocks
        mock_chat.return_value = {'success': True}
        mock_todo.return_value = {'success': True}
        
        # Setup error state
        error_snapshot = StateSnapshot(
            agent_id="failed_recovery_agent",
            status=AgentStatus.ERROR,
            state_data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="failed_recovery_test",
            conversation_id="failed_recovery_conv",
            metadata={"error_message": "Critical failure"}
        )
        
        mock_core = Mock()
        mock_core.coordination_id = "failed_recovery_test"
        mock_core.conversation_id = "failed_recovery_conv"
        mock_core.agent_states = {"failed_recovery_agent": error_snapshot}
        
        # Setup operations to fail transition
        mock_operations = Mock()
        mock_operations.transition_agent_state.return_value = False
        
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test failed recovery
        result = recovery.recover_agent_state("failed_recovery_agent")
        
        # Verify failure
        assert result is False
        
        # Performance metrics should not be updated on failure
        assert recovery.performance_metrics["recovery_attempts"] == 0
    
    def test_register_state_observer(self):
        """Test observer registration functionality"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        
        mock_core = Mock()
        mock_operations = Mock()
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test observer registration
        test_callback = Mock()
        recovery.register_state_observer("test_agent", test_callback)
        
        # Verify observer was called
        mock_observer.register_observer.assert_called_once_with("test_agent", test_callback)
    
    def test_register_state_observer_wildcard(self):
        """Test observer registration with wildcard"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        
        mock_core = Mock()
        mock_operations = Mock()
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test wildcard observer registration
        def wildcard_callback(agent_id, from_status, to_status):
            pass
        
        recovery.register_state_observer("*", wildcard_callback)
        
        # Verify observer was called with wildcard
        mock_observer.register_observer.assert_called_once_with("*", wildcard_callback)
    
    def test_get_performance_metrics(self):
        """Test performance metrics retrieval"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        
        mock_core = Mock()
        mock_operations = Mock()
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Set some test metrics
        recovery.performance_metrics.update({
            "recovery_attempts": 5,
            "successful_recoveries": 4,
            "failed_recoveries": 1,
            "average_recovery_time": 1.23
        })
        
        # Test metrics retrieval
        metrics = recovery.get_performance_metrics()
        
        # Verify it's a copy
        assert metrics is not recovery.performance_metrics
        
        # Verify content
        assert metrics["recovery_attempts"] == 5
        assert metrics["successful_recoveries"] == 4
        assert metrics["failed_recoveries"] == 1
        assert metrics["average_recovery_time"] == 1.23
    
    @patch('ltms.coordination.agent_state_recovery.chat_action')
    @patch('ltms.coordination.agent_state_recovery.todo_action')
    def test_exception_handling_during_recovery(self, mock_todo, mock_chat):
        """Test exception handling during recovery operations"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup LTMC tools
        mock_chat.return_value = {'success': True}
        mock_todo.side_effect = Exception("Todo service unavailable")
        
        # Setup error state
        error_snapshot = StateSnapshot(
            agent_id="exception_agent",
            status=AgentStatus.ERROR,
            state_data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="exception_test",
            conversation_id="exception_conv",
            metadata={"error_message": "Test error"}
        )
        
        mock_core = Mock()
        mock_core.coordination_id = "exception_test"
        mock_core.conversation_id = "exception_conv"
        mock_core.agent_states = {"exception_agent": error_snapshot}
        
        mock_operations = Mock()
        mock_operations.transition_agent_state.return_value = True
        
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test recovery with exception
        result = recovery.recover_agent_state("exception_agent")
        
        # Should handle gracefully and still return False
        assert result is False
    
    @patch('ltms.coordination.agent_state_recovery.chat_action')
    @patch('ltms.coordination.agent_state_recovery.todo_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_todo, mock_chat):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_chat.return_value = {'success': True}
        mock_todo.return_value = {'success': True, 'task_id': 'ltmc_recovery_task'}
        
        # Setup error state
        error_snapshot = StateSnapshot(
            agent_id="ltmc_agent",
            status=AgentStatus.ERROR,
            state_data={"ltmc_test": True},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="ltmc_comprehensive",
            conversation_id="ltmc_comprehensive_conv",
            metadata={"error_message": "LTMC test error"}
        )
        
        mock_core = Mock()
        mock_core.coordination_id = "ltmc_comprehensive"
        mock_core.conversation_id = "ltmc_comprehensive_conv"
        mock_core.agent_states = {"ltmc_agent": error_snapshot}
        
        mock_operations = Mock()
        mock_operations.transition_agent_state.return_value = True
        
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test comprehensive recovery
        result = recovery.recover_agent_state("ltmc_agent")
        
        # Verify success
        assert result is True
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. chat_action - MANDATORY Tool 3
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert chat_call[1]['conversation_id'] == 'ltmc_comprehensive_conv'
        assert chat_call[1]['role'] == 'system'
        assert 'Agent recovery initiated' in chat_call[1]['message']
        assert 'ltmc_agent' in chat_call[1]['message']
        
        # 2. todo_action - MANDATORY Tool 2
        mock_todo.assert_called_once()
        todo_call = mock_todo.call_args
        assert todo_call[1]['action'] == 'add'
        assert todo_call[1]['conversation_id'] == 'ltmc_comprehensive_conv'
        assert todo_call[1]['role'] == 'system'
        assert 'Recovery: ltmc_agent' in todo_call[1]['task']
        assert 'agent_recovery' in todo_call[1]['tags']
        assert 'ltmc_comprehensive' in todo_call[1]['tags']


class TestAgentStateRecoveryIntegration:
    """Test AgentStateRecovery integration scenarios"""
    
    def test_integration_with_operations_and_observer(self):
        """Test integration with operations and observer components"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        
        mock_core = Mock()
        mock_operations = Mock()
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test that all components are properly integrated
        assert recovery.core == mock_core
        assert recovery.operations == mock_operations
        assert recovery.observer == mock_observer
        
        # Test observer delegation
        test_callback = lambda a, f, t: None
        recovery.register_state_observer("integration_agent", test_callback)
        
        mock_observer.register_observer.assert_called_once_with("integration_agent", test_callback)
    
    @patch('ltms.coordination.agent_state_recovery.chat_action')
    @patch('ltms.coordination.agent_state_recovery.todo_action')
    def test_performance_tracking_comprehensive(self, mock_todo, mock_chat):
        """Test comprehensive performance tracking during recovery operations"""
        from ltms.coordination.agent_state_recovery import AgentStateRecovery
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup mocks
        mock_chat.return_value = {'success': True}
        mock_todo.return_value = {'success': True}
        
        # Setup multiple error states
        error_snapshot_1 = StateSnapshot(
            agent_id="perf_agent_1",
            status=AgentStatus.ERROR,
            state_data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="perf_test",
            conversation_id="perf_conv",
            metadata={"error_message": "Error 1"}
        )
        
        error_snapshot_2 = StateSnapshot(
            agent_id="perf_agent_2", 
            status=AgentStatus.ERROR,
            state_data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="perf_test",
            conversation_id="perf_conv",
            metadata={"error_message": "Error 2"}
        )
        
        mock_core = Mock()
        mock_core.coordination_id = "perf_test"
        mock_core.conversation_id = "perf_conv"
        mock_core.agent_states = {
            "perf_agent_1": error_snapshot_1,
            "perf_agent_2": error_snapshot_2
        }
        
        mock_operations = Mock()
        mock_operations.transition_agent_state.return_value = True
        
        mock_observer = Mock()
        
        recovery = AgentStateRecovery(mock_core, mock_operations, mock_observer)
        
        # Test multiple recoveries
        result_1 = recovery.recover_agent_state("perf_agent_1")
        result_2 = recovery.recover_agent_state("perf_agent_2")
        
        # Verify both succeeded
        assert result_1 is True
        assert result_2 is True
        
        # Verify performance metrics
        metrics = recovery.get_performance_metrics()
        assert metrics["recovery_attempts"] == 2
        assert metrics["successful_recoveries"] == 2
        assert metrics["failed_recoveries"] == 0


# Pytest fixtures for recovery testing
@pytest.fixture
def mock_recovery_dependencies():
    """Fixture providing mock dependencies for recovery testing"""
    mock_core = Mock()
    mock_core.coordination_id = "fixture_recovery_coord"
    mock_core.conversation_id = "fixture_recovery_conv"
    mock_core.agent_states = {}
    
    mock_operations = Mock()
    mock_operations.transition_agent_state.return_value = True
    
    mock_observer = Mock()
    
    return {
        'core': mock_core,
        'operations': mock_operations,
        'observer': mock_observer
    }

@pytest.fixture
def agent_state_recovery(mock_recovery_dependencies):
    """Fixture providing AgentStateRecovery instance"""
    from ltms.coordination.agent_state_recovery import AgentStateRecovery
    
    deps = mock_recovery_dependencies
    return AgentStateRecovery(deps['core'], deps['operations'], deps['observer'])

@pytest.fixture
def mock_all_ltmc_recovery_tools():
    """Fixture providing mocks for all LTMC tools used in recovery"""
    with patch.multiple(
        'ltms.coordination.agent_state_recovery',
        chat_action=Mock(return_value={'success': True}),
        todo_action=Mock(return_value={'success': True, 'task_id': 'fixture_task'})
    ) as mocks:
        yield mocks