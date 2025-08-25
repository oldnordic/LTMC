"""
Comprehensive TDD tests for Safety Validation Core extraction.
Tests core agent initialization, coordinator integration, and state management.

Following TDD methodology: Tests written FIRST before extraction.
SafetyValidationCore will provide base agent functionality and coordination integration.
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestSafetyValidationCore:
    """Test SafetyValidationCore class - to be extracted from safety_validator.py"""
    
    def test_safety_validation_core_creation(self):
        """Test SafetyValidationCore can be instantiated with coordinator and state manager"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        # Mock coordinator and state manager
        mock_coordinator = Mock()
        mock_coordinator.conversation_id = "test_conv_123"
        mock_coordinator.task_id = "test_task_456"
        
        mock_state_manager = Mock()
        
        # Create safety validation core
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        
        # Verify initialization
        assert hasattr(validator, 'agent_id')
        assert hasattr(validator, 'agent_type')
        assert hasattr(validator, 'coordinator')
        assert hasattr(validator, 'state_manager')
        assert hasattr(validator, 'message_broker')
        assert hasattr(validator, 'validation_report')
        assert hasattr(validator, 'safety_checks')
        assert hasattr(validator, 'removal_plan')
        
        assert validator.agent_id == "safety_validator"
        assert validator.agent_type == "ltmc-safety-validator"
        assert validator.coordinator == mock_coordinator
        assert validator.state_manager == mock_state_manager
        assert isinstance(validator.validation_report, dict)
        assert isinstance(validator.safety_checks, list)
        assert isinstance(validator.removal_plan, dict)
    
    def test_safety_validation_core_message_broker_integration(self):
        """Test SafetyValidationCore integrates with LTMCMessageBroker"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        mock_coordinator = Mock()
        mock_coordinator.conversation_id = "broker_test_conv"
        mock_state_manager = Mock()
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        
        # Verify message broker integration
        assert isinstance(validator.message_broker, LTMCMessageBroker)
        assert validator.message_broker.conversation_id == "broker_test_conv"
    
    @patch('ltms.coordination.safety_validation_core.chat_action')
    def test_initialize_agent_success(self, mock_chat_action):
        """Test successful agent initialization with coordinator registration"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_coordinator = Mock()
        mock_coordinator.task_id = "init_test_task"
        mock_coordinator.conversation_id = "init_test_conv"
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        mock_chat_action.return_value = {'success': True}
        
        # Create and initialize validator
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        result = validator.initialize_agent()
        
        # Verify successful initialization
        assert result is True
        
        # Verify coordinator registration was called correctly
        mock_coordinator.register_agent.assert_called_once_with(
            "safety_validator",
            "ltmc-safety-validator",
            task_scope=["safety_validation", "dependency_analysis", "removal_planning"],
            dependencies=["legacy_code_analyzer"],
            outputs=["safety_report", "removal_plan", "validation_results"]
        )
        
        # Verify state manager was called correctly
        mock_state_manager.create_agent_state.assert_called_once()
        state_call_args = mock_state_manager.create_agent_state.call_args
        assert state_call_args[0][0] == "safety_validator"  # agent_id
        assert state_call_args[0][1] == AgentStatus.INITIALIZING  # status
        
        state_data = state_call_args[0][2]
        assert state_data["agent_id"] == "safety_validator"
        assert "safety_validation" in state_data["task_scope"]
        assert state_data["current_task"] == "initialization"
        
        # Verify chat logging was called
        mock_chat_action.assert_called_once()
        chat_call = mock_chat_action.call_args
        assert chat_call[1]['action'] == 'log'
        assert 'Safety Validator initialized' in chat_call[1]['message']
        assert chat_call[1]['tool_name'] == 'safety_validator'
        assert chat_call[1]['conversation_id'] == 'init_test_conv'
    
    def test_initialize_agent_coordinator_registration_failure(self):
        """Test agent initialization handles coordinator registration failure"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        # Setup mocks with coordinator registration failure
        mock_coordinator = Mock()
        mock_coordinator.register_agent.return_value = False
        mock_state_manager = Mock()
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        result = validator.initialize_agent()
        
        # Should fail gracefully
        assert result is False
        
        # State manager should not be called if registration fails
        mock_state_manager.create_agent_state.assert_not_called()
    
    @patch('ltms.coordination.safety_validation_core.chat_action')
    def test_initialize_agent_state_creation_failure(self, mock_chat_action):
        """Test agent initialization handles state creation failure"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        # Setup mocks with state creation failure
        mock_coordinator = Mock()
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.side_effect = Exception("State creation failed")
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        result = validator.initialize_agent()
        
        # Should handle exception and return False
        assert result is False
    
    @patch('ltms.coordination.safety_validation_core.chat_action')
    def test_initialize_agent_exception_handling(self, mock_chat_action):
        """Test agent initialization handles general exceptions gracefully"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        # Setup mocks with chat_action failure
        mock_coordinator = Mock()
        mock_coordinator.register_agent.return_value = True
        mock_state_manager = Mock()
        
        mock_chat_action.side_effect = Exception("Chat logging failed")
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        result = validator.initialize_agent()
        
        # Should handle exception gracefully
        assert result is False
    
    def test_safety_validation_core_properties(self):
        """Test SafetyValidationCore properties and attributes"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        mock_coordinator = Mock()
        mock_coordinator.conversation_id = "props_test_conv"
        mock_state_manager = Mock()
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        
        # Test initial property values
        assert validator.validation_report == {}
        assert validator.safety_checks == []
        assert validator.removal_plan == {}
        
        # Test property modification
        test_report = {"test": "report"}
        test_checks = [{"check": "test"}]
        test_plan = {"plan": "test"}
        
        validator.validation_report = test_report
        validator.safety_checks = test_checks
        validator.removal_plan = test_plan
        
        assert validator.validation_report == test_report
        assert validator.safety_checks == test_checks
        assert validator.removal_plan == test_plan
    
    def test_safety_validation_core_agent_identification(self):
        """Test SafetyValidationCore agent identification attributes"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        
        # Test agent identification
        assert validator.agent_id == "safety_validator"
        assert validator.agent_type == "ltmc-safety-validator"
        
        # These should be immutable for this agent type
        assert isinstance(validator.agent_id, str)
        assert isinstance(validator.agent_type, str)


class TestSafetyValidationCoreIntegration:
    """Test SafetyValidationCore integration with other components"""
    
    @patch('ltms.coordination.safety_validation_core.chat_action')
    def test_integration_with_agent_coordination_framework(self, mock_chat_action):
        """Test SafetyValidationCore integration with agent coordination framework"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Mock coordination framework components
        mock_coordinator = Mock()
        mock_coordinator.task_id = "integration_task"
        mock_coordinator.conversation_id = "integration_conv"
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        mock_chat_action.return_value = {'success': True}
        
        # Test integration
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        result = validator.initialize_agent()
        
        assert result is True
        
        # Verify integration points
        assert validator.coordinator.task_id == "integration_task"
        assert validator.coordinator.conversation_id == "integration_conv"
        assert validator.message_broker.conversation_id == "integration_conv"
    
    def test_integration_with_message_broker(self):
        """Test SafetyValidationCore integration with message broker"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        mock_coordinator = Mock()
        mock_coordinator.conversation_id = "msg_broker_conv"
        mock_state_manager = Mock()
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        
        # Verify message broker is properly integrated
        assert isinstance(validator.message_broker, LTMCMessageBroker)
        assert validator.message_broker.conversation_id == mock_coordinator.conversation_id
        
        # Test message broker functionality (basic)
        assert hasattr(validator.message_broker, 'send_message')
        assert hasattr(validator.message_broker, 'receive_messages')
        assert hasattr(validator.message_broker, 'send_response')
    
    @patch('ltms.coordination.safety_validation_core.chat_action')
    def test_coordination_workflow_dependencies(self, mock_chat_action):
        """Test SafetyValidationCore properly declares workflow dependencies"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        mock_coordinator = Mock()
        mock_coordinator.register_agent.return_value = True
        mock_state_manager = Mock()
        mock_chat_action.return_value = {'success': True}
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        validator.initialize_agent()
        
        # Verify dependency declaration
        register_call = mock_coordinator.register_agent.call_args
        assert "legacy_code_analyzer" in register_call[1]['dependencies']
        
        # Verify task scope declaration
        expected_scope = ["safety_validation", "dependency_analysis", "removal_planning"]
        assert register_call[1]['task_scope'] == expected_scope
        
        # Verify outputs declaration
        expected_outputs = ["safety_report", "removal_plan", "validation_results"]
        assert register_call[1]['outputs'] == expected_outputs


class TestSafetyValidationCoreStateManagement:
    """Test SafetyValidationCore state management functionality"""
    
    @patch('ltms.coordination.safety_validation_core.chat_action')
    def test_state_management_integration(self, mock_chat_action):
        """Test SafetyValidationCore state management integration"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        mock_coordinator = Mock()
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        mock_chat_action.return_value = {'success': True}
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        validator.initialize_agent()
        
        # Verify state was created with correct parameters
        mock_state_manager.create_agent_state.assert_called_once()
        call_args = mock_state_manager.create_agent_state.call_args
        
        assert call_args[0][0] == "safety_validator"  # agent_id
        assert call_args[0][1] == AgentStatus.INITIALIZING  # initial status
        
        state_data = call_args[0][2]
        assert isinstance(state_data, dict)
        assert state_data["agent_id"] == "safety_validator"
        assert "current_task" in state_data
        assert "task_scope" in state_data
    
    def test_state_data_structure(self):
        """Test SafetyValidationCore state data structure"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        mock_coordinator = Mock()
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        
        # Test that initialization creates proper state structure
        with patch('ltms.coordination.safety_validation_core.chat_action') as mock_chat:
            mock_chat.return_value = {'success': True}
            validator.initialize_agent()
        
        # Extract state data from the call
        state_data = mock_state_manager.create_agent_state.call_args[0][2]
        
        # Verify state data structure
        required_fields = ["agent_id", "task_scope", "current_task"]
        for field in required_fields:
            assert field in state_data
        
        assert state_data["agent_id"] == "safety_validator"
        assert isinstance(state_data["task_scope"], list)
        assert len(state_data["task_scope"]) > 0
        assert state_data["current_task"] == "initialization"


class TestSafetyValidationCoreErrorHandling:
    """Test SafetyValidationCore error handling and edge cases"""
    
    def test_initialization_with_none_coordinator(self):
        """Test SafetyValidationCore handling of None coordinator"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        mock_state_manager = Mock()
        
        # Should handle None coordinator gracefully during construction
        with pytest.raises(AttributeError):
            validator = SafetyValidationCore(None, mock_state_manager)
            validator.initialize_agent()
    
    def test_initialization_with_none_state_manager(self):
        """Test SafetyValidationCore handling of None state manager"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        mock_coordinator = Mock()
        mock_coordinator.conversation_id = "test_conv"
        
        # Should handle None state manager during construction
        validator = SafetyValidationCore(mock_coordinator, None)
        
        # But should fail during initialization
        result = validator.initialize_agent()
        assert result is False
    
    def test_coordinator_missing_attributes(self):
        """Test SafetyValidationCore with coordinator missing required attributes"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        # Mock coordinator missing conversation_id
        incomplete_coordinator = Mock()
        del incomplete_coordinator.conversation_id  # Remove attribute
        
        mock_state_manager = Mock()
        
        # Should handle missing attributes gracefully
        with pytest.raises(AttributeError):
            SafetyValidationCore(incomplete_coordinator, mock_state_manager)
    
    @patch('ltms.coordination.safety_validation_core.chat_action')
    def test_initialization_partial_success_handling(self, mock_chat_action):
        """Test SafetyValidationCore handling of partial initialization success"""
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        # Coordinator succeeds, state manager succeeds, chat fails
        mock_coordinator = Mock()
        mock_coordinator.register_agent.return_value = True
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        mock_chat_action.side_effect = Exception("Chat service unavailable")
        
        validator = SafetyValidationCore(mock_coordinator, mock_state_manager)
        result = validator.initialize_agent()
        
        # Should fail if any step fails
        assert result is False


# Pytest fixtures for core testing
@pytest.fixture
def mock_coordinator():
    """Fixture providing mock coordinator for testing"""
    coordinator = Mock()
    coordinator.task_id = "fixture_task_123"
    coordinator.conversation_id = "fixture_conv_456"
    coordinator.register_agent.return_value = True
    return coordinator

@pytest.fixture
def mock_state_manager():
    """Fixture providing mock state manager for testing"""
    state_manager = Mock()
    state_manager.create_agent_state.return_value = True
    return state_manager

@pytest.fixture
def safety_validation_core(mock_coordinator, mock_state_manager):
    """Fixture providing SafetyValidationCore instance for testing"""
    from ltms.coordination.safety_validation_core import SafetyValidationCore
    return SafetyValidationCore(mock_coordinator, mock_state_manager)

@pytest.fixture
def initialized_safety_core(safety_validation_core):
    """Fixture providing initialized SafetyValidationCore instance"""
    with patch('ltms.coordination.safety_validation_core.chat_action') as mock_chat:
        mock_chat.return_value = {'success': True}
        success = safety_validation_core.initialize_agent()
        assert success is True
    return safety_validation_core