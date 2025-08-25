"""
Comprehensive TDD tests for agent_state_logging module.
Tests the AgentStateLogging class that will be extracted from agent_state_manager.py.

Following TDD methodology: Tests written FIRST before implementation.
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock


class TestAgentStateLogging:
    """Test AgentStateLogging class - extracted from agent_state_manager.py logging methods"""
    
    def test_agent_state_logging_creation(self):
        """Test AgentStateLogging class can be instantiated"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        assert logging_system.coordination_id == "test_coordination"
        assert logging_system.conversation_id == "test_conversation"
        assert hasattr(logging_system, 'transition_logs')
        assert isinstance(logging_system.transition_logs, list)
        assert len(logging_system.transition_logs) == 0
    
    def test_log_transition_method_exists(self):
        """Test that log_transition method exists and is callable"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        assert hasattr(logging_system, 'log_transition')
        assert callable(logging_system.log_transition)
    
    def test_get_transition_history_method_exists(self):
        """Test that get_transition_history method exists and is callable"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        assert hasattr(logging_system, 'get_transition_history')
        assert callable(logging_system.get_transition_history)
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_log_transition_successful_transition(self, mock_memory_action):
        """Test logging a successful state transition"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        # Log successful transition
        logging_system.log_transition(
            agent_id="test_agent",
            from_status=AgentStatus.INITIALIZING,
            to_status=AgentStatus.ACTIVE,
            transition_type=StateTransition.ACTIVATE,
            success=True,
            error_message=None,
            transition_data={"activation": "successful"}
        )
        
        # Verify log entry was created and stored
        assert len(logging_system.transition_logs) == 1
        
        log_entry = logging_system.transition_logs[0]
        assert log_entry.agent_id == "test_agent"
        assert log_entry.from_status == AgentStatus.INITIALIZING
        assert log_entry.to_status == AgentStatus.ACTIVE
        assert log_entry.transition_type == StateTransition.ACTIVATE
        assert log_entry.success is True
        assert log_entry.error_message is None
        assert log_entry.transition_data == {"activation": "successful"}
        
        # Verify memory_action was called for storage
        assert mock_memory_action.called
        call_args = mock_memory_action.call_args
        assert call_args[1]['action'] == 'store'
        assert 'transition_log_' in call_args[1]['file_name']
        assert call_args[1]['file_name'].endswith('.json')
        
        # Verify log document structure
        log_content = json.loads(call_args[1]['content'])
        assert log_content['agent_id'] == "test_agent"
        assert log_content['from_status'] == "initializing"
        assert log_content['to_status'] == "active"
        assert log_content['transition_type'] == "activate"
        assert log_content['success'] is True
        assert log_content['error_message'] is None
        assert log_content['transition_data'] == {"activation": "successful"}
        assert 'timestamp' in log_content
        assert 'log_id' in log_content
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_log_transition_failed_transition(self, mock_memory_action):
        """Test logging a failed state transition with error message"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        error_message = "Invalid transition: cannot skip states"
        transition_data = {"attempted_skip": True, "validation_failed": True}
        
        # Log failed transition
        logging_system.log_transition(
            agent_id="failing_agent",
            from_status=AgentStatus.INITIALIZING,
            to_status=AgentStatus.COMPLETED,
            transition_type=StateTransition.COMPLETE,
            success=False,
            error_message=error_message,
            transition_data=transition_data
        )
        
        # Verify failed log entry
        assert len(logging_system.transition_logs) == 1
        
        log_entry = logging_system.transition_logs[0]
        assert log_entry.agent_id == "failing_agent"
        assert log_entry.success is False
        assert log_entry.error_message == error_message
        assert log_entry.transition_data == transition_data
        
        # Verify LTMC storage of failed transition
        assert mock_memory_action.called
        call_args = mock_memory_action.call_args
        log_content = json.loads(call_args[1]['content'])
        assert log_content['success'] is False
        assert log_content['error_message'] == error_message
        assert log_content['transition_data'] == transition_data
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_log_transition_with_complex_transition_data(self, mock_memory_action):
        """Test logging transition with complex nested transition data"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        complex_transition_data = {
            "state_updates": {
                "current_task": "complex_operation",
                "progress": 0.75,
                "metadata": {"priority": "high", "retries": 2}
            },
            "context": {
                "triggered_by": "user_action",
                "environment": "production",
                "dependencies": ["service_a", "service_b"]
            },
            "timing": {
                "started_at": "2025-08-24T10:30:00Z",
                "duration_ms": 150
            }
        }
        
        # Log transition with complex data
        logging_system.log_transition(
            agent_id="complex_agent",
            from_status=AgentStatus.ACTIVE,
            to_status=AgentStatus.WAITING,
            transition_type=StateTransition.PAUSE,
            success=True,
            error_message=None,
            transition_data=complex_transition_data
        )
        
        # Verify complex data is preserved
        log_entry = logging_system.transition_logs[0]
        assert log_entry.transition_data == complex_transition_data
        assert log_entry.transition_data["state_updates"]["progress"] == 0.75
        assert log_entry.transition_data["context"]["dependencies"] == ["service_a", "service_b"]
        
        # Verify JSON serialization preserves structure
        call_args = mock_memory_action.call_args
        log_content = json.loads(call_args[1]['content'])
        assert log_content['transition_data'] == complex_transition_data
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_log_transition_multiple_logs(self, mock_memory_action):
        """Test logging multiple transitions for different agents"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        # Log multiple transitions
        transitions = [
            ("agent_1", AgentStatus.INITIALIZING, AgentStatus.ACTIVE, StateTransition.ACTIVATE, True),
            ("agent_2", AgentStatus.ACTIVE, AgentStatus.WAITING, StateTransition.PAUSE, True),
            ("agent_1", AgentStatus.ACTIVE, AgentStatus.ERROR, StateTransition.FAIL, False),
            ("agent_3", AgentStatus.INITIALIZING, AgentStatus.ACTIVE, StateTransition.ACTIVATE, True)
        ]
        
        for agent_id, from_status, to_status, transition_type, success in transitions:
            logging_system.log_transition(
                agent_id=agent_id,
                from_status=from_status,
                to_status=to_status,
                transition_type=transition_type,
                success=success,
                error_message="Test error" if not success else None,
                transition_data={"test": True}
            )
        
        # Verify all transitions were logged
        assert len(logging_system.transition_logs) == 4
        
        # Verify each log entry
        logged_agents = [log.agent_id for log in logging_system.transition_logs]
        assert logged_agents == ["agent_1", "agent_2", "agent_1", "agent_3"]
        
        # Verify memory_action called for each log
        assert mock_memory_action.call_count == 4
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_log_transition_memory_storage_failure(self, mock_memory_action):
        """Test log_transition handles memory storage failure gracefully"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock to simulate storage failure
        mock_memory_action.return_value = {'success': False, 'error': 'Storage failed'}
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        # Should not raise exception despite storage failure
        logging_system.log_transition(
            agent_id="test_agent",
            from_status=AgentStatus.INITIALIZING,
            to_status=AgentStatus.ACTIVE,
            transition_type=StateTransition.ACTIVATE,
            success=True
        )
        
        # Log should still be stored locally even if LTMC storage fails
        assert len(logging_system.transition_logs) == 1
        assert mock_memory_action.called
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_log_transition_memory_exception_handling(self, mock_memory_action):
        """Test log_transition handles memory_action exceptions gracefully"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock to raise exception
        mock_memory_action.side_effect = Exception("Memory system error")
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        # Should not raise exception despite memory system error
        logging_system.log_transition(
            agent_id="test_agent",
            from_status=AgentStatus.ACTIVE,
            to_status=AgentStatus.COMPLETED,
            transition_type=StateTransition.COMPLETE,
            success=True
        )
        
        # Local log should still be created
        assert len(logging_system.transition_logs) == 1
    
    def test_log_transition_timestamp_generation(self):
        """Test that log_transition generates proper timestamps"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        with patch('ltms.coordination.agent_state_logging.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            logging_system = AgentStateLogging("test_coordination", "test_conversation")
            
            # Record time before logging
            before_time = datetime.now(timezone.utc)
            
            logging_system.log_transition(
                agent_id="timestamp_test",
                from_status=AgentStatus.INITIALIZING,
                to_status=AgentStatus.ACTIVE,
                transition_type=StateTransition.ACTIVATE,
                success=True
            )
            
            # Record time after logging
            after_time = datetime.now(timezone.utc)
            
            log_entry = logging_system.transition_logs[0]
            log_timestamp = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
            
            # Timestamp should be between before and after times
            assert before_time <= log_timestamp <= after_time
    
    def test_log_transition_tagging(self):
        """Test that logs are properly tagged for LTMC retrieval"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        with patch('ltms.coordination.agent_state_logging.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            logging_system = AgentStateLogging("test_coord_123", "test_conversation")
            
            logging_system.log_transition(
                agent_id="tagged_agent",
                from_status=AgentStatus.ACTIVE,
                to_status=AgentStatus.COMPLETED,
                transition_type=StateTransition.COMPLETE,
                success=True
            )
            
            call_args = mock_memory.call_args
            tags = call_args[1]['tags']
            
            assert 'transition_log' in tags
            assert 'tagged_agent' in tags
            assert 'test_coord_123' in tags
    
    def test_get_transition_history_empty_history(self):
        """Test get_transition_history with no logs"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        history = logging_system.get_transition_history("nonexistent_agent")
        
        assert isinstance(history, list)
        assert len(history) == 0
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_get_transition_history_single_agent(self, mock_memory_action):
        """Test get_transition_history for single agent with multiple transitions"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        # Log transitions for target agent
        agent_transitions = [
            (AgentStatus.INITIALIZING, AgentStatus.ACTIVE, StateTransition.ACTIVATE),
            (AgentStatus.ACTIVE, AgentStatus.WAITING, StateTransition.PAUSE),
            (AgentStatus.WAITING, AgentStatus.ACTIVE, StateTransition.RESUME),
            (AgentStatus.ACTIVE, AgentStatus.COMPLETED, StateTransition.COMPLETE)
        ]
        
        for from_status, to_status, transition_type in agent_transitions:
            logging_system.log_transition(
                agent_id="target_agent",
                from_status=from_status,
                to_status=to_status,
                transition_type=transition_type,
                success=True
            )
        
        # Log transition for different agent (should be filtered out)
        logging_system.log_transition(
            agent_id="other_agent",
            from_status=AgentStatus.INITIALIZING,
            to_status=AgentStatus.ACTIVE,
            transition_type=StateTransition.ACTIVATE,
            success=True
        )
        
        # Get history for target agent
        history = logging_system.get_transition_history("target_agent")
        
        assert len(history) == 4
        assert all(log.agent_id == "target_agent" for log in history)
        
        # Verify transition sequence
        transitions = [(log.from_status, log.to_status, log.transition_type) for log in history]
        assert transitions == agent_transitions
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_get_transition_history_multiple_agents(self, mock_memory_action):
        """Test get_transition_history filtering works correctly with multiple agents"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        logging_system = AgentStateLogging("test_coordination", "test_conversation")
        
        # Log transitions for multiple agents
        agents_data = {
            "agent_a": [(AgentStatus.INITIALIZING, AgentStatus.ACTIVE), (AgentStatus.ACTIVE, AgentStatus.COMPLETED)],
            "agent_b": [(AgentStatus.INITIALIZING, AgentStatus.ERROR)],
            "agent_c": [(AgentStatus.INITIALIZING, AgentStatus.ACTIVE), (AgentStatus.ACTIVE, AgentStatus.WAITING), (AgentStatus.WAITING, AgentStatus.COMPLETED)]
        }
        
        for agent_id, transitions in agents_data.items():
            for from_status, to_status in transitions:
                logging_system.log_transition(
                    agent_id=agent_id,
                    from_status=from_status,
                    to_status=to_status,
                    transition_type=StateTransition.ACTIVATE,
                    success=True
                )
        
        # Test history for each agent
        for agent_id, expected_transitions in agents_data.items():
            history = logging_system.get_transition_history(agent_id)
            assert len(history) == len(expected_transitions)
            assert all(log.agent_id == agent_id for log in history)
    
    def test_get_transition_history_chronological_order(self):
        """Test that transition history maintains chronological order"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        with patch('ltms.coordination.agent_state_logging.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            logging_system = AgentStateLogging("test_coordination", "test_conversation")
            
            # Log transitions with slight time delays to ensure chronological order
            import time
            transitions = [
                (AgentStatus.INITIALIZING, AgentStatus.ACTIVE, "first"),
                (AgentStatus.ACTIVE, AgentStatus.WAITING, "second"), 
                (AgentStatus.WAITING, AgentStatus.ACTIVE, "third"),
                (AgentStatus.ACTIVE, AgentStatus.COMPLETED, "fourth")
            ]
            
            for i, (from_status, to_status, marker) in enumerate(transitions):
                if i > 0:
                    time.sleep(0.001)  # Ensure different timestamps
                
                logging_system.log_transition(
                    agent_id="chronological_test",
                    from_status=from_status,
                    to_status=to_status,
                    transition_type=StateTransition.ACTIVATE,
                    success=True,
                    transition_data={"order": marker}
                )
            
            history = logging_system.get_transition_history("chronological_test")
            
            # Verify chronological order by checking timestamps
            timestamps = [log.timestamp for log in history]
            sorted_timestamps = sorted(timestamps)
            assert timestamps == sorted_timestamps
            
            # Verify order markers
            order_markers = [log.transition_data["order"] for log in history]
            assert order_markers == ["first", "second", "third", "fourth"]


class TestAgentStateLoggingIntegration:
    """Test integration scenarios for AgentStateLogging"""
    
    @patch('ltms.coordination.agent_state_logging.memory_action')
    def test_logging_system_realistic_workflow(self, mock_memory_action):
        """Test logging system in realistic agent workflow scenario"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        logging_system = AgentStateLogging("workflow_coordination", "workflow_conversation")
        
        # Simulate realistic agent workflow with various transition types
        workflow_steps = [
            # Normal initialization
            ("workflow_agent", AgentStatus.INITIALIZING, AgentStatus.ACTIVE, StateTransition.ACTIVATE, True, None),
            
            # Pause for external dependency
            ("workflow_agent", AgentStatus.ACTIVE, AgentStatus.WAITING, StateTransition.PAUSE, True, None),
            
            # Resume after dependency resolved
            ("workflow_agent", AgentStatus.WAITING, AgentStatus.ACTIVE, StateTransition.RESUME, True, None),
            
            # Failure scenario
            ("workflow_agent", AgentStatus.ACTIVE, AgentStatus.ERROR, StateTransition.FAIL, False, "External service timeout"),
            
            # Recovery attempt
            ("workflow_agent", AgentStatus.ERROR, AgentStatus.INITIALIZING, StateTransition.RETRY, True, None),
            
            # Successful completion
            ("workflow_agent", AgentStatus.INITIALIZING, AgentStatus.ACTIVE, StateTransition.ACTIVATE, True, None),
            ("workflow_agent", AgentStatus.ACTIVE, AgentStatus.COMPLETED, StateTransition.COMPLETE, True, None)
        ]
        
        for agent_id, from_status, to_status, transition_type, success, error_msg in workflow_steps:
            logging_system.log_transition(
                agent_id=agent_id,
                from_status=from_status,
                to_status=to_status,
                transition_type=transition_type,
                success=success,
                error_message=error_msg,
                transition_data={"workflow_step": True}
            )
        
        # Verify complete workflow was logged
        history = logging_system.get_transition_history("workflow_agent")
        assert len(history) == 7
        
        # Verify failure was logged with error message
        failure_log = next(log for log in history if not log.success)
        assert failure_log.error_message == "External service timeout"
        assert failure_log.from_status == AgentStatus.ACTIVE
        assert failure_log.to_status == AgentStatus.ERROR
        
        # Verify recovery was logged
        recovery_log = next(log for log in history if log.transition_type == StateTransition.RETRY)
        assert recovery_log.from_status == AgentStatus.ERROR
        assert recovery_log.to_status == AgentStatus.INITIALIZING
        
        # Verify final completion
        completion_log = history[-1]
        assert completion_log.to_status == AgentStatus.COMPLETED
        assert completion_log.success is True
    
    def test_logging_with_all_agent_statuses(self):
        """Test logging system works with all possible AgentStatus values"""
        from ltms.coordination.agent_state_logging import AgentStateLogging
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        with patch('ltms.coordination.agent_state_logging.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            logging_system = AgentStateLogging("comprehensive_coordination", "comprehensive_conversation")
            
            # Test transitions involving all status types
            all_statuses = list(AgentStatus)
            
            for i, status in enumerate(all_statuses):
                # Use next status or first status if at end
                next_status = all_statuses[(i + 1) % len(all_statuses)]
                
                logging_system.log_transition(
                    agent_id=f"agent_{status.value}",
                    from_status=status,
                    to_status=next_status,
                    transition_type=StateTransition.ACTIVATE,
                    success=True,
                    transition_data={"comprehensive_test": True}
                )
            
            # Verify all statuses were logged
            assert len(logging_system.transition_logs) == len(all_statuses)
            
            # Verify each status appears in logs
            logged_from_statuses = {log.from_status for log in logging_system.transition_logs}
            logged_to_statuses = {log.to_status for log in logging_system.transition_logs}
            
            assert logged_from_statuses == set(all_statuses)
            assert logged_to_statuses == set(all_statuses)


# Pytest fixtures for common test data
@pytest.fixture
def logging_system():
    """Fixture providing a fresh AgentStateLogging instance"""
    from ltms.coordination.agent_state_logging import AgentStateLogging
    return AgentStateLogging("fixture_coordination", "fixture_conversation")

@pytest.fixture
def sample_transition_data():
    """Fixture providing sample transition data"""
    return {
        "state_updates": {"current_task": "testing", "progress": 0.5},
        "context": {"test_mode": True, "environment": "test"}
    }

@pytest.fixture
def mock_successful_memory():
    """Fixture providing a mocked successful memory_action"""
    with patch('ltms.coordination.agent_state_logging.memory_action') as mock:
        mock.return_value = {'success': True}
        yield mock