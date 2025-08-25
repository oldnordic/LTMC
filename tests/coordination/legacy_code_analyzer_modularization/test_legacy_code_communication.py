"""
Comprehensive TDD tests for Legacy Code Communication extraction.
Tests agent communication and message broker integration.

Following TDD methodology: Tests written FIRST before extraction.
LegacyCodeCommunication will handle send_analysis_to_next_agent and message coordination.
MANDATORY: Uses ALL required LTMC tools (chat_action for communication logging).
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestLegacyCodeCommunication:
    """Test LegacyCodeCommunication class - to be extracted from legacy_code_analyzer.py"""
    
    def test_legacy_code_communication_creation(self):
        """Test LegacyCodeCommunication can be instantiated"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        # Mock dependencies
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_message_broker = Mock()
        
        # Mock analysis data
        mock_legacy_decorators = [{'name': 'test_func', 'file': 'test.py'}]
        mock_functional_tools = [{'name': 'test_tool'}]
        mock_analysis_report = {'total': 1}
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            mock_legacy_decorators, mock_functional_tools, mock_analysis_report
        )
        
        assert hasattr(communication, 'coordinator')
        assert hasattr(communication, 'state_manager')
        assert hasattr(communication, 'message_broker')
        assert hasattr(communication, 'legacy_decorators')
        assert hasattr(communication, 'functional_tools')
        assert hasattr(communication, 'analysis_report')
        assert communication.coordinator == mock_coordinator
    
    @patch('ltms.coordination.legacy_code_communication.chat_action')
    def test_send_analysis_to_next_agent_success(self, mock_chat):
        """Test successful analysis results sending with LTMC tools integration"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateTransition
        
        # Setup LTMC chat tool mock - MANDATORY
        mock_chat.return_value = {'success': True}
        
        # Setup analysis data
        legacy_decorators = [
            {'name': 'legacy_func', 'file': '/test/legacy.py', 'line': 42}
        ]
        functional_tools = [
            {'name': 'modern_tool', 'status': 'active'}
        ]
        analysis_report = {
            'total_legacy_decorators': 1,
            'total_functional_tools': 1,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Setup coordinator
        mock_coordinator = Mock()
        mock_coordinator.task_id = "comm_test_task"
        mock_coordinator.conversation_id = "comm_test_conv"
        
        # Setup state manager
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        # Setup message broker
        mock_message_broker = Mock()
        mock_message_broker.send_message.return_value = True
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            legacy_decorators, functional_tools, analysis_report
        )
        communication.agent_id = "legacy_code_analyzer"
        
        # Test sending analysis to next agent
        result = communication.send_analysis_to_next_agent("safety_validator")
        
        # Verify success
        assert result is True
        
        # Verify message broker was called
        mock_message_broker.send_message.assert_called_once()
        
        # Get the message that was sent
        sent_message = mock_message_broker.send_message.call_args[0][0]
        
        # Verify message structure
        assert hasattr(sent_message, 'from_agent') or 'from_agent' in sent_message
        assert hasattr(sent_message, 'to_agent') or 'to_agent' in sent_message
        assert hasattr(sent_message, 'message_type') or 'message_type' in sent_message
        assert hasattr(sent_message, 'data') or 'data' in sent_message
        
        # Verify state transition to HANDOFF
        mock_state_manager.transition_agent_state.assert_called_once()
        transition_call = mock_state_manager.transition_agent_state.call_args
        assert transition_call[0][1] == AgentStatus.HANDOFF
        assert transition_call[0][2] == StateTransition.HANDOFF
        
        # Verify LTMC chat logging - MANDATORY
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert 'Legacy analysis results sent' in chat_call[1]['message']
        assert 'legacy_code_analyzer' in chat_call[1]['message']
        assert 'safety_validator' in chat_call[1]['message']
        assert chat_call[1]['conversation_id'] == 'comm_test_conv'
        assert chat_call[1]['role'] == 'system'
    
    def test_send_analysis_to_next_agent_message_broker_failure(self):
        """Test analysis sending when message broker fails"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "comm_fail_task"
        
        mock_state_manager = Mock()
        
        # Setup message broker to fail
        mock_message_broker = Mock()
        mock_message_broker.send_message.return_value = False
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            [], [], {}
        )
        
        # Test failed message sending
        result = communication.send_analysis_to_next_agent("safety_validator")
        
        # Verify failure
        assert result is False
        
        # Verify state manager was not called (no transition on failure)
        mock_state_manager.transition_agent_state.assert_not_called()
    
    def test_send_analysis_to_next_agent_exception_handling(self):
        """Test communication exception handling"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        # Setup message broker to raise exception
        mock_message_broker = Mock()
        mock_message_broker.send_message.side_effect = Exception("Message service unavailable")
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            [], [], {}
        )
        
        # Test exception handling
        result = communication.send_analysis_to_next_agent("safety_validator")
        
        # Should handle gracefully and return False
        assert result is False
    
    def test_message_data_structure_validation(self):
        """Test message data structure includes all required fields"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        # Setup comprehensive test data
        legacy_decorators = [
            {
                'name': 'test_legacy_1',
                'file': '/test/legacy1.py',
                'line': 10,
                'decorators': ['@mcp.tool']
            },
            {
                'name': 'test_legacy_2', 
                'file': '/test/legacy2.py',
                'line': 20,
                'decorators': ['@mcp.tool']
            }
        ]
        
        functional_tools = [
            {'name': 'memory_action', 'status': 'active'},
            {'name': 'chat_action', 'status': 'active'}
        ]
        
        analysis_report = {
            'total_legacy_decorators': 2,
            'total_functional_tools': 2,
            'removal_recommendations': ['Remove test_legacy_1', 'Remove test_legacy_2'],
            'analysis_timestamp': '2025-08-24T10:30:00Z'
        }
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "structure_validation_task"
        
        mock_state_manager = Mock()
        mock_message_broker = Mock()
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            legacy_decorators, functional_tools, analysis_report
        )
        communication.agent_id = "structure_test_analyzer"
        
        # Intercept message creation to validate structure
        def validate_message_structure(message):
            # Parse message data based on message structure
            if hasattr(message, 'data'):
                data = message.data
            elif isinstance(message, dict) and 'data' in message:
                data = message['data']
            else:
                data = message
            
            # Validate required fields in data
            assert 'legacy_decorators' in data
            assert 'functional_tools' in data
            assert 'analysis_report' in data
            assert 'coordination_task' in data
            
            # Validate data content
            assert len(data['legacy_decorators']) == 2
            assert len(data['functional_tools']) == 2
            assert data['coordination_task'] == 'structure_validation_task'
            
            return True
        
        mock_message_broker.send_message.side_effect = validate_message_structure
        
        # Test message structure validation
        with patch('ltms.coordination.legacy_code_communication.chat_action'):
            result = communication.send_analysis_to_next_agent("structure_validator")
        
        # Should succeed after validation
        mock_message_broker.send_message.assert_called_once()
    
    @patch('ltms.coordination.legacy_code_communication.create_request_response_message')
    def test_message_creation_with_correct_parameters(self, mock_create_message):
        """Test message creation with all required parameters"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        # Setup mock message creation
        mock_message = Mock()
        mock_create_message.return_value = mock_message
        
        mock_coordinator = Mock()
        mock_coordinator.conversation_id = "message_creation_conv"
        
        mock_state_manager = Mock()
        mock_message_broker = Mock()
        mock_message_broker.send_message.return_value = True
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            [], [], {}
        )
        communication.agent_id = "message_test_analyzer"
        
        # Test message creation
        with patch('ltms.coordination.legacy_code_communication.chat_action'):
            result = communication.send_analysis_to_next_agent("message_recipient")
        
        # Verify message creation was called with correct parameters
        mock_create_message.assert_called_once()
        create_call = mock_create_message.call_args
        
        # Verify parameters
        assert create_call[0][0] == "message_test_analyzer"  # from_agent
        assert create_call[0][1] == "message_recipient"  # to_agent
        assert create_call[0][2] == "legacy_analysis_complete"  # message_type
        # data parameter (dict) is 4th parameter
        assert isinstance(create_call[0][3], dict)
        # priority and conversation_id are 5th and 6th parameters
        assert create_call[0][5] == "message_creation_conv"  # conversation_id
    
    @patch('ltms.coordination.legacy_code_communication.chat_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_chat):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_chat.return_value = {'success': True}
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "ltmc_comprehensive_comm"
        mock_coordinator.conversation_id = "ltmc_comprehensive_comm_conv"
        
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        mock_message_broker = Mock()
        mock_message_broker.send_message.return_value = True
        
        # Comprehensive test data
        legacy_decorators = [{'name': 'ltmc_legacy', 'ltmc_test': True}]
        functional_tools = [{'name': 'ltmc_tool', 'ltmc_test': True}]
        analysis_report = {'ltmc_comprehensive': True}
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            legacy_decorators, functional_tools, analysis_report
        )
        communication.agent_id = "ltmc_comprehensive_analyzer"
        
        # Test comprehensive communication
        result = communication.send_analysis_to_next_agent("ltmc_comprehensive_recipient")
        
        # Verify success
        assert result is True
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. chat_action - MANDATORY Tool 3
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert chat_call[1]['conversation_id'] == 'ltmc_comprehensive_comm_conv'
        assert chat_call[1]['role'] == 'system'
        assert 'Legacy analysis results sent' in chat_call[1]['message']
        assert 'ltmc_comprehensive_analyzer' in chat_call[1]['message']
        assert 'ltmc_comprehensive_recipient' in chat_call[1]['message']
    
    def test_agent_handoff_state_transition(self):
        """Test proper state transition during agent handoff"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateTransition
        
        mock_coordinator = Mock()
        
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        mock_message_broker = Mock()
        mock_message_broker.send_message.return_value = True
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            [], [], {}
        )
        communication.agent_id = "handoff_test_analyzer"
        
        # Test handoff
        with patch('ltms.coordination.legacy_code_communication.chat_action'):
            result = communication.send_analysis_to_next_agent("handoff_recipient")
        
        # Verify state transition
        mock_state_manager.transition_agent_state.assert_called_once()
        transition_call = mock_state_manager.transition_agent_state.call_args
        
        # Verify parameters
        assert transition_call[0][0] == "handoff_test_analyzer"  # agent_id
        assert transition_call[0][1] == AgentStatus.HANDOFF  # new_status
        assert transition_call[0][2] == StateTransition.HANDOFF  # transition_type
        
        # Verify state updates
        state_updates = transition_call[0][3]["state_updates"]
        assert "handed_off_to" in state_updates
        assert state_updates["handed_off_to"] == "handoff_recipient"


class TestLegacyCodeCommunicationIntegration:
    """Test LegacyCodeCommunication integration scenarios"""
    
    def test_integration_with_message_broker_and_state_manager(self):
        """Test integration with message broker and state manager components"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_message_broker = Mock()
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            [], [], {}
        )
        
        # Test that all components are properly integrated
        assert communication.coordinator == mock_coordinator
        assert communication.state_manager == mock_state_manager
        assert communication.message_broker == mock_message_broker
        assert isinstance(communication.legacy_decorators, list)
        assert isinstance(communication.functional_tools, list)
        assert isinstance(communication.analysis_report, dict)
    
    @patch('ltms.coordination.legacy_code_communication.chat_action')
    def test_end_to_end_communication_workflow(self, mock_chat):
        """Test complete communication workflow with all steps"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        # Setup chat
        mock_chat.return_value = {'success': True}
        
        # Setup comprehensive integration test
        mock_coordinator = Mock()
        mock_coordinator.task_id = "e2e_communication"
        mock_coordinator.conversation_id = "e2e_communication_conv"
        
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        mock_message_broker = Mock()
        mock_message_broker.send_message.return_value = True
        
        # Complete test data
        legacy_decorators = [
            {'name': 'e2e_legacy', 'file': '/e2e/test.py', 'analysis': 'comprehensive'}
        ]
        functional_tools = [
            {'name': 'e2e_tool', 'status': 'active', 'integration': 'complete'}
        ]
        analysis_report = {
            'e2e_test': True,
            'total_legacy_decorators': 1,
            'total_functional_tools': 1
        }
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            legacy_decorators, functional_tools, analysis_report
        )
        communication.agent_id = "e2e_analyzer"
        
        # Test complete workflow
        result = communication.send_analysis_to_next_agent("e2e_recipient")
        
        # Verify complete workflow succeeded
        assert result is True
        
        # Verify all steps were executed in correct order
        # 1. Message creation and sending
        mock_message_broker.send_message.assert_called_once()
        
        # 2. Chat logging
        mock_chat.assert_called_once()
        
        # 3. State transition
        mock_state_manager.transition_agent_state.assert_called_once()
        
        # Verify integration between components
        chat_call = mock_chat.call_args
        assert mock_coordinator.conversation_id in chat_call[1]['conversation_id']
    
    def test_data_consistency_across_integration(self):
        """Test data consistency across all integration points"""
        from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
        
        # Setup consistent test data
        test_task_id = "consistency_test"
        test_conversation_id = "consistency_conv"
        
        legacy_decorators = [{'name': 'consistent_legacy', 'task': test_task_id}]
        functional_tools = [{'name': 'consistent_tool', 'task': test_task_id}]
        analysis_report = {'task_id': test_task_id, 'consistency': True}
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = test_task_id
        mock_coordinator.conversation_id = test_conversation_id
        
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        mock_message_broker = Mock()
        mock_message_broker.send_message.return_value = True
        
        communication = LegacyCodeCommunication(
            mock_coordinator, mock_state_manager, mock_message_broker,
            legacy_decorators, functional_tools, analysis_report
        )
        communication.agent_id = "consistency_analyzer"
        
        # Test consistency across integration
        with patch('ltms.coordination.legacy_code_communication.chat_action') as mock_chat:
            mock_chat.return_value = {'success': True}
            result = communication.send_analysis_to_next_agent("consistency_recipient")
        
        # Verify data consistency
        assert result is True
        
        # All components should use the same task_id and conversation_id
        chat_call = mock_chat.call_args
        assert chat_call[1]['conversation_id'] == test_conversation_id


# Pytest fixtures for communication testing
@pytest.fixture
def mock_communication_dependencies():
    """Fixture providing mock dependencies for communication testing"""
    mock_coordinator = Mock()
    mock_coordinator.task_id = "fixture_comm_task"
    mock_coordinator.conversation_id = "fixture_comm_conv"
    
    mock_state_manager = Mock()
    mock_state_manager.transition_agent_state.return_value = True
    
    mock_message_broker = Mock()
    mock_message_broker.send_message.return_value = True
    
    return {
        'coordinator': mock_coordinator,
        'state_manager': mock_state_manager,
        'message_broker': mock_message_broker
    }

@pytest.fixture
def legacy_code_communication(mock_communication_dependencies):
    """Fixture providing LegacyCodeCommunication instance"""
    from ltms.coordination.legacy_code_communication import LegacyCodeCommunication
    
    deps = mock_communication_dependencies
    return LegacyCodeCommunication(
        deps['coordinator'], deps['state_manager'], deps['message_broker'],
        [], [], {}
    )

@pytest.fixture
def mock_all_ltmc_communication_tools():
    """Fixture providing mocks for all LTMC tools used in communication"""
    with patch.multiple(
        'ltms.coordination.legacy_code_communication',
        chat_action=Mock(return_value={'success': True})
    ) as mocks:
        yield mocks