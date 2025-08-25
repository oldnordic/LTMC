"""
Comprehensive TDD tests for agent_state_validator module.
Tests the AgentStateValidator class that will be extracted from agent_state_manager.py.

Following TDD methodology: Tests written FIRST before implementation.
"""

import pytest
from typing import Dict, Any, Optional, Tuple


class TestAgentStateValidator:
    """Test AgentStateValidator class - extracted from agent_state_manager.py lines 50-86"""
    
    def test_valid_transitions_matrix_structure(self):
        """Test that VALID_TRANSITIONS matrix has correct structure"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Test that VALID_TRANSITIONS exists and is a dictionary
        assert hasattr(AgentStateValidator, 'VALID_TRANSITIONS')
        assert isinstance(AgentStateValidator.VALID_TRANSITIONS, dict)
        
        # Test that all keys are AgentStatus enums
        for from_status in AgentStateValidator.VALID_TRANSITIONS.keys():
            assert isinstance(from_status, AgentStatus)
        
        # Test that all values are lists of AgentStatus enums
        for status_list in AgentStateValidator.VALID_TRANSITIONS.values():
            assert isinstance(status_list, list)
            for status in status_list:
                assert isinstance(status, AgentStatus)
    
    def test_valid_transitions_coverage(self):
        """Test that VALID_TRANSITIONS covers all expected states"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        expected_states = {
            AgentStatus.INITIALIZING,
            AgentStatus.ACTIVE,
            AgentStatus.WAITING,
            AgentStatus.COMPLETED,
            AgentStatus.ERROR,
            AgentStatus.HANDOFF
        }
        
        # Test that all expected states are covered as source states
        covered_states = set(AgentStateValidator.VALID_TRANSITIONS.keys())
        assert expected_states == covered_states
    
    def test_specific_valid_transitions(self):
        """Test specific valid transition cases from the matrix"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Test INITIALIZING transitions
        assert AgentStatus.ACTIVE in AgentStateValidator.VALID_TRANSITIONS[AgentStatus.INITIALIZING]
        assert AgentStatus.ERROR in AgentStateValidator.VALID_TRANSITIONS[AgentStatus.INITIALIZING]
        
        # Test ACTIVE transitions
        active_transitions = AgentStateValidator.VALID_TRANSITIONS[AgentStatus.ACTIVE]
        assert AgentStatus.WAITING in active_transitions
        assert AgentStatus.COMPLETED in active_transitions
        assert AgentStatus.ERROR in active_transitions
        assert AgentStatus.HANDOFF in active_transitions
        
        # Test WAITING transitions
        waiting_transitions = AgentStateValidator.VALID_TRANSITIONS[AgentStatus.WAITING]
        assert AgentStatus.ACTIVE in waiting_transitions
        assert AgentStatus.ERROR in waiting_transitions
        assert AgentStatus.COMPLETED in waiting_transitions
        
        # Test COMPLETED transitions (should allow reactivation)
        completed_transitions = AgentStateValidator.VALID_TRANSITIONS[AgentStatus.COMPLETED]
        assert AgentStatus.ACTIVE in completed_transitions
        
        # Test ERROR transitions (should allow recovery)
        error_transitions = AgentStateValidator.VALID_TRANSITIONS[AgentStatus.ERROR]
        assert AgentStatus.ACTIVE in error_transitions
        assert AgentStatus.INITIALIZING in error_transitions
        
        # Test HANDOFF transitions
        handoff_transitions = AgentStateValidator.VALID_TRANSITIONS[AgentStatus.HANDOFF]
        assert AgentStatus.COMPLETED in handoff_transitions
        assert AgentStatus.ACTIVE in handoff_transitions
    
    def test_validate_transition_method_exists(self):
        """Test that validate_transition classmethod exists and is callable"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        assert hasattr(AgentStateValidator, 'validate_transition')
        assert callable(AgentStateValidator.validate_transition)
    
    def test_validate_transition_valid_cases(self):
        """Test validate_transition with valid transition cases"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Test all valid transitions return True
        valid_cases = [
            (AgentStatus.INITIALIZING, AgentStatus.ACTIVE),
            (AgentStatus.INITIALIZING, AgentStatus.ERROR),
            (AgentStatus.ACTIVE, AgentStatus.WAITING),
            (AgentStatus.ACTIVE, AgentStatus.COMPLETED),
            (AgentStatus.ACTIVE, AgentStatus.ERROR),
            (AgentStatus.ACTIVE, AgentStatus.HANDOFF),
            (AgentStatus.WAITING, AgentStatus.ACTIVE),
            (AgentStatus.WAITING, AgentStatus.ERROR),
            (AgentStatus.WAITING, AgentStatus.COMPLETED),
            (AgentStatus.COMPLETED, AgentStatus.ACTIVE),
            (AgentStatus.ERROR, AgentStatus.ACTIVE),
            (AgentStatus.ERROR, AgentStatus.INITIALIZING),
            (AgentStatus.HANDOFF, AgentStatus.COMPLETED),
            (AgentStatus.HANDOFF, AgentStatus.ACTIVE)
        ]
        
        for from_status, to_status in valid_cases:
            result = AgentStateValidator.validate_transition(from_status, to_status)
            assert result is True, f"Expected True for {from_status.value} → {to_status.value}"
    
    def test_validate_transition_invalid_cases(self):
        """Test validate_transition with invalid transition cases"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Test some clearly invalid transitions
        invalid_cases = [
            (AgentStatus.INITIALIZING, AgentStatus.COMPLETED),  # Can't skip ACTIVE
            (AgentStatus.INITIALIZING, AgentStatus.WAITING),    # Can't skip ACTIVE
            (AgentStatus.INITIALIZING, AgentStatus.HANDOFF),    # Can't skip ACTIVE
            (AgentStatus.COMPLETED, AgentStatus.ERROR),         # Can't fail after completion
            (AgentStatus.COMPLETED, AgentStatus.WAITING),       # Can't wait after completion
            (AgentStatus.COMPLETED, AgentStatus.HANDOFF),       # Can't handoff after completion
        ]
        
        for from_status, to_status in invalid_cases:
            result = AgentStateValidator.validate_transition(from_status, to_status)
            assert result is False, f"Expected False for {from_status.value} → {to_status.value}"
    
    def test_validate_transition_unknown_status(self):
        """Test validate_transition with unknown from_status"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # This should be handled by the VALID_TRANSITIONS check
        # Since we control the enum, this mainly tests robustness
        result = AgentStateValidator.validate_transition(
            AgentStatus.ACTIVE,  # Known status
            AgentStatus.COMPLETED  # Known valid transition
        )
        assert result is True
        
        # Test self-transition (should be invalid for most states)
        result = AgentStateValidator.validate_transition(
            AgentStatus.ACTIVE,
            AgentStatus.ACTIVE
        )
        assert result is False  # ACTIVE → ACTIVE not in transition matrix
    
    def test_validate_state_data_method_exists(self):
        """Test that validate_state_data classmethod exists and is callable"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        assert hasattr(AgentStateValidator, 'validate_state_data')
        assert callable(AgentStateValidator.validate_state_data)
    
    def test_validate_state_data_valid_case(self):
        """Test validate_state_data with valid state data"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        valid_state_data = {
            "agent_id": "test_agent",
            "task_scope": ["analysis", "reporting"],
            "current_task": "data_analysis"
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(valid_state_data)
        
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_state_data_valid_with_none_current_task(self):
        """Test validate_state_data with None current_task (should be valid)"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        valid_state_data = {
            "agent_id": "test_agent",
            "task_scope": ["initialization"],
            "current_task": None  # Should be valid
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(valid_state_data)
        
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_state_data_missing_required_fields(self):
        """Test validate_state_data with missing required fields"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        # Test missing agent_id
        missing_agent_id = {
            "task_scope": ["analysis"],
            "current_task": "test"
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(missing_agent_id)
        assert is_valid is False
        assert error_msg == "Missing required field: agent_id"
        
        # Test missing task_scope
        missing_task_scope = {
            "agent_id": "test_agent",
            "current_task": "test"
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(missing_task_scope)
        assert is_valid is False
        assert error_msg == "Missing required field: task_scope"
        
        # Test missing current_task
        missing_current_task = {
            "agent_id": "test_agent",
            "task_scope": ["analysis"]
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(missing_current_task)
        assert is_valid is False
        assert error_msg == "Missing required field: current_task"
    
    def test_validate_state_data_invalid_task_scope_type(self):
        """Test validate_state_data with invalid task_scope type"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        # Test task_scope as string instead of list
        invalid_task_scope_string = {
            "agent_id": "test_agent",
            "task_scope": "analysis",  # Should be list
            "current_task": "test"
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(invalid_task_scope_string)
        assert is_valid is False
        assert error_msg == "task_scope must be a list"
        
        # Test task_scope as dict instead of list
        invalid_task_scope_dict = {
            "agent_id": "test_agent",
            "task_scope": {"analysis": True},  # Should be list
            "current_task": "test"
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(invalid_task_scope_dict)
        assert is_valid is False
        assert error_msg == "task_scope must be a list"
        
        # Test task_scope as None
        invalid_task_scope_none = {
            "agent_id": "test_agent", 
            "task_scope": None,  # Should be list
            "current_task": "test"
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(invalid_task_scope_none)
        assert is_valid is False
        assert error_msg == "task_scope must be a list"
    
    def test_validate_state_data_invalid_current_task_type(self):
        """Test validate_state_data with invalid current_task type"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        # Test current_task as int instead of string/None
        invalid_current_task_int = {
            "agent_id": "test_agent",
            "task_scope": ["analysis"],
            "current_task": 123  # Should be string or None
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(invalid_current_task_int)
        assert is_valid is False
        assert error_msg == "current_task must be string or None"
        
        # Test current_task as list instead of string/None
        invalid_current_task_list = {
            "agent_id": "test_agent",
            "task_scope": ["analysis"],
            "current_task": ["task1", "task2"]  # Should be string or None
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(invalid_current_task_list)
        assert is_valid is False
        assert error_msg == "current_task must be string or None"
    
    def test_validate_state_data_return_type(self):
        """Test that validate_state_data returns correct tuple type"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        valid_data = {
            "agent_id": "test_agent",
            "task_scope": ["test"],
            "current_task": "testing"
        }
        
        result = AgentStateValidator.validate_state_data(valid_data)
        
        # Should return tuple
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        is_valid, error_msg = result
        assert isinstance(is_valid, bool)
        assert error_msg is None or isinstance(error_msg, str)
    
    def test_validate_state_data_additional_fields_allowed(self):
        """Test that validate_state_data allows additional fields"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        state_data_with_extras = {
            "agent_id": "test_agent",
            "task_scope": ["analysis", "reporting"],
            "current_task": "data_processing",
            # Additional fields should be allowed
            "extra_field": "extra_value",
            "metadata": {"key": "value"},
            "progress": 50
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(state_data_with_extras)
        
        assert is_valid is True
        assert error_msg is None
    
    def test_empty_task_scope_list_valid(self):
        """Test that empty task_scope list is valid"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        empty_task_scope_data = {
            "agent_id": "test_agent",
            "task_scope": [],  # Empty list should be valid
            "current_task": "initialization"
        }
        
        is_valid, error_msg = AgentStateValidator.validate_state_data(empty_task_scope_data)
        
        assert is_valid is True
        assert error_msg is None


class TestAgentStateValidatorIntegration:
    """Test integration between validation methods"""
    
    def test_validator_with_all_agent_statuses(self):
        """Test validator works with all possible AgentStatus values"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Get all AgentStatus values
        all_statuses = list(AgentStatus)
        
        # Test that each status can be used in transition validation
        for status in all_statuses:
            # Test transition from this status to all possible targets
            for target_status in all_statuses:
                result = AgentStateValidator.validate_transition(status, target_status)
                # Result should be boolean (either True or False, not error)
                assert isinstance(result, bool)
    
    def test_comprehensive_workflow_validation(self):
        """Test comprehensive agent workflow validation"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Test typical agent workflow
        workflow_steps = [
            (AgentStatus.INITIALIZING, AgentStatus.ACTIVE),
            (AgentStatus.ACTIVE, AgentStatus.WAITING),
            (AgentStatus.WAITING, AgentStatus.ACTIVE),
            (AgentStatus.ACTIVE, AgentStatus.COMPLETED)
        ]
        
        for from_status, to_status in workflow_steps:
            is_valid = AgentStateValidator.validate_transition(from_status, to_status)
            assert is_valid is True, f"Workflow step {from_status.value} → {to_status.value} should be valid"
        
        # Test error recovery workflow
        error_recovery_steps = [
            (AgentStatus.ACTIVE, AgentStatus.ERROR),
            (AgentStatus.ERROR, AgentStatus.INITIALIZING),
            (AgentStatus.INITIALIZING, AgentStatus.ACTIVE)
        ]
        
        for from_status, to_status in error_recovery_steps:
            is_valid = AgentStateValidator.validate_transition(from_status, to_status)
            assert is_valid is True, f"Error recovery step {from_status.value} → {to_status.value} should be valid"
    
    def test_validation_methods_consistency(self):
        """Test that validation methods work consistently together"""
        from ltms.coordination.agent_state_validator import AgentStateValidator
        
        # Test valid state data with various task_scope sizes
        test_cases = [
            {"agent_id": "agent1", "task_scope": [], "current_task": None},
            {"agent_id": "agent2", "task_scope": ["single"], "current_task": "task1"},
            {"agent_id": "agent3", "task_scope": ["multi", "task", "scope"], "current_task": "task2"}
        ]
        
        for state_data in test_cases:
            is_valid, error_msg = AgentStateValidator.validate_state_data(state_data)
            assert is_valid is True
            assert error_msg is None


# Pytest fixtures for common test data
@pytest.fixture
def valid_state_data():
    """Fixture providing valid state data for testing"""
    return {
        "agent_id": "fixture_test_agent",
        "task_scope": ["testing", "validation"],
        "current_task": "running_tests"
    }

@pytest.fixture
def all_agent_statuses():
    """Fixture providing all AgentStatus enum values"""
    from ltms.coordination.agent_coordination_framework import AgentStatus
    return list(AgentStatus)