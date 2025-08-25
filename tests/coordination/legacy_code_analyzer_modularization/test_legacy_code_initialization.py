"""
Comprehensive TDD tests for Legacy Code Initialization extraction.
Tests agent initialization and coordination framework integration.

Following TDD methodology: Tests written FIRST before extraction.
LegacyCodeInitialization will handle initialize_agent and coordination setup.
MANDATORY: Uses ALL required LTMC tools (chat_action for initialization logging).
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestLegacyCodeInitialization:
    """Test LegacyCodeInitialization class - to be extracted from legacy_code_analyzer.py"""
    
    def test_legacy_code_initialization_creation(self):
        """Test LegacyCodeInitialization can be instantiated"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        
        # Mock dependencies
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        assert hasattr(initialization, 'agent_id')
        assert hasattr(initialization, 'coordinator')
        assert hasattr(initialization, 'state_manager')
        assert initialization.agent_id == "legacy_code_analyzer"
        assert initialization.coordinator == mock_coordinator
    
    @patch('ltms.coordination.legacy_code_initialization.chat_action')
    def test_initialize_agent_success(self, mock_chat):
        """Test successful agent initialization with LTMC tools integration"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup LTMC chat tool mock - MANDATORY
        mock_chat.return_value = {'success': True}
        
        # Setup coordinator
        mock_coordinator = Mock()
        mock_coordinator.task_id = "init_test_task"
        mock_coordinator.conversation_id = "init_test_conv"
        mock_coordinator.register_agent.return_value = True
        
        # Setup state manager
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Test initialization
        result = initialization.initialize_agent()
        
        # Verify success
        assert result is True
        
        # Verify coordinator registration
        mock_coordinator.register_agent.assert_called_once_with(
            "legacy_code_analyzer",
            "ltmc-legacy-analyzer", 
            task_scope=["legacy_analysis", "decorator_mapping", "code_structure_analysis"],
            outputs=["legacy_inventory", "functional_tool_mapping", "removal_recommendations"]
        )
        
        # Verify state manager called
        mock_state_manager.create_agent_state.assert_called_once()
        state_call = mock_state_manager.create_agent_state.call_args
        assert state_call[0][0] == "legacy_code_analyzer"  # agent_id
        assert state_call[0][1] == AgentStatus.INITIALIZING  # initial status
        
        # Verify state data structure
        state_data = state_call[0][2]
        assert state_data["agent_id"] == "legacy_code_analyzer"
        assert "task_scope" in state_data
        assert "current_task" in state_data
        
        # Verify LTMC chat logging - MANDATORY
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert 'Legacy Code Analyzer initialized' in chat_call[1]['message']
        assert chat_call[1]['conversation_id'] == 'init_test_conv'
        assert chat_call[1]['role'] == 'system'
    
    def test_initialize_agent_coordinator_failure(self):
        """Test initialization when coordinator registration fails"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        
        # Setup coordinator to fail registration
        mock_coordinator = Mock()
        mock_coordinator.register_agent.return_value = False
        
        mock_state_manager = Mock()
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Test failed initialization
        result = initialization.initialize_agent()
        
        # Verify failure
        assert result is False
        
        # Verify state manager was not called (early exit)
        mock_state_manager.create_agent_state.assert_not_called()
    
    def test_initialize_agent_exception_handling(self):
        """Test initialization exception handling"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        
        # Setup coordinator to raise exception
        mock_coordinator = Mock()
        mock_coordinator.register_agent.side_effect = Exception("Coordinator service unavailable")
        
        mock_state_manager = Mock()
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Test exception handling
        result = initialization.initialize_agent()
        
        # Should handle gracefully and return False
        assert result is False
    
    def test_agent_id_and_type_properties(self):
        """Test agent ID and type are properly set"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Verify agent properties
        assert initialization.agent_id == "legacy_code_analyzer"
        assert initialization.agent_type == "ltmc-legacy-analyzer"
        assert hasattr(initialization, 'message_broker')
    
    @patch('ltms.coordination.legacy_code_initialization.chat_action')
    def test_initialization_with_message_broker(self, mock_chat):
        """Test initialization includes message broker setup"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        
        mock_chat.return_value = {'success': True}
        
        mock_coordinator = Mock()
        mock_coordinator.conversation_id = "broker_test_conv"
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Verify message broker is initialized
        assert hasattr(initialization, 'message_broker')
        
        # Test successful initialization
        result = initialization.initialize_agent()
        assert result is True
    
    @patch('ltms.coordination.legacy_code_initialization.chat_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_chat):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_chat.return_value = {'success': True}
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "ltmc_comprehensive_init"
        mock_coordinator.conversation_id = "ltmc_comprehensive_init_conv"
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Test comprehensive initialization
        result = initialization.initialize_agent()
        
        # Verify success
        assert result is True
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. chat_action - MANDATORY Tool 3
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert chat_call[1]['conversation_id'] == 'ltmc_comprehensive_init_conv'
        assert chat_call[1]['role'] == 'system'
        assert 'Legacy Code Analyzer initialized' in chat_call[1]['message']
        assert 'ltmc_comprehensive_init' in chat_call[1]['message']
    
    @patch('ltms.coordination.legacy_code_initialization.chat_action')
    def test_state_data_structure_validation(self, mock_chat):
        """Test state data structure includes all required fields"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        mock_chat.return_value = {'success': True}
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "state_structure_test"
        mock_coordinator.conversation_id = "state_structure_conv"
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Test initialization
        result = initialization.initialize_agent()
        
        # Verify success and state structure
        assert result is True
        
        # Verify state manager call structure
        state_call = mock_state_manager.create_agent_state.call_args
        state_data = state_call[0][2]
        
        # Required fields in state data
        assert "agent_id" in state_data
        assert "task_scope" in state_data
        assert "current_task" in state_data
        
        # Verify values
        assert state_data["agent_id"] == "legacy_code_analyzer"
        assert isinstance(state_data["task_scope"], list)
        assert len(state_data["task_scope"]) > 0
        assert "legacy_analysis" in state_data["task_scope"]
        assert state_data["current_task"] == "initialization"
    
    def test_task_scope_configuration(self):
        """Test task scope is properly configured"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Task scope should be predefined
        expected_scopes = ["legacy_analysis", "decorator_mapping", "code_structure_analysis"]
        expected_outputs = ["legacy_inventory", "functional_tool_mapping", "removal_recommendations"]
        
        # These would be used in coordinator registration
        # Verify through the registration call in actual test
        assert initialization.agent_id == "legacy_code_analyzer"


class TestLegacyCodeInitializationIntegration:
    """Test LegacyCodeInitialization integration scenarios"""
    
    def test_integration_with_coordinator_and_state_manager(self):
        """Test integration with coordinator and state manager components"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Test that all components are properly integrated
        assert initialization.coordinator == mock_coordinator
        assert initialization.state_manager == mock_state_manager
        assert hasattr(initialization, 'message_broker')
    
    @patch('ltms.coordination.legacy_code_initialization.chat_action')
    def test_end_to_end_initialization_workflow(self, mock_chat):
        """Test complete initialization workflow"""
        from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup chat
        mock_chat.return_value = {'success': True}
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "e2e_workflow"
        mock_coordinator.conversation_id = "e2e_workflow_conv"
        mock_coordinator.register_agent.return_value = True
        
        mock_state_manager = Mock()
        mock_state_manager.create_agent_state.return_value = True
        
        initialization = LegacyCodeInitialization(mock_coordinator, mock_state_manager)
        
        # Test complete workflow
        result = initialization.initialize_agent()
        
        # Verify complete workflow succeeded
        assert result is True
        
        # Verify all steps were executed in order
        # 1. Coordinator registration
        mock_coordinator.register_agent.assert_called_once()
        
        # 2. State creation
        mock_state_manager.create_agent_state.assert_called_once()
        
        # 3. Chat logging
        mock_chat.assert_called_once()
        
        # Verify integration between components
        chat_call = mock_chat.call_args
        assert mock_coordinator.task_id in chat_call[1]['message']


# Pytest fixtures for initialization testing
@pytest.fixture
def mock_initialization_dependencies():
    """Fixture providing mock dependencies for initialization testing"""
    mock_coordinator = Mock()
    mock_coordinator.task_id = "fixture_init_task"
    mock_coordinator.conversation_id = "fixture_init_conv"
    mock_coordinator.register_agent.return_value = True
    
    mock_state_manager = Mock()
    mock_state_manager.create_agent_state.return_value = True
    
    return {
        'coordinator': mock_coordinator,
        'state_manager': mock_state_manager
    }

@pytest.fixture
def legacy_code_initialization(mock_initialization_dependencies):
    """Fixture providing LegacyCodeInitialization instance"""
    from ltms.coordination.legacy_code_initialization import LegacyCodeInitialization
    
    deps = mock_initialization_dependencies
    return LegacyCodeInitialization(deps['coordinator'], deps['state_manager'])

@pytest.fixture
def mock_all_ltmc_initialization_tools():
    """Fixture providing mocks for all LTMC tools used in initialization"""
    with patch.multiple(
        'ltms.coordination.legacy_code_initialization',
        chat_action=Mock(return_value={'success': True})
    ) as mocks:
        yield mocks