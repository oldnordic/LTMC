"""
Comprehensive TDD tests for CoordinationCommunicationTests class extraction.
Tests the inter-agent communication functionality in coordination framework.

Following TDD methodology: Tests written FIRST before extraction.
CoordinationCommunicationTests will handle message communication and workflow orchestration testing.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestCoordinationCommunicationTests:
    """Test CoordinationCommunicationTests class - to be extracted from coordination_test_example.py"""
    
    def test_coordination_communication_tests_creation(self):
        """Test CoordinationCommunicationTests class can be instantiated"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        comm_tests = CoordinationCommunicationTests()
        
        assert hasattr(comm_tests, 'test_results')
        assert hasattr(comm_tests, 'test_agents')
        assert hasattr(comm_tests, 'message_broker')
        assert isinstance(comm_tests.test_results, dict)
        assert isinstance(comm_tests.test_agents, dict)
    
    def test_setup_communication_testing_agents(self):
        """Test setup of test agents for communication testing"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        # Mock framework components
        coordinator = Mock()
        coordinator.conversation_id = "comm_test_conv"
        coordinator.task_id = "comm_test_task"
        coordinator.register_agent.return_value = True
        
        state_manager = Mock()
        message_broker = Mock()
        
        comm_tests = CoordinationCommunicationTests()
        
        # Setup test agents
        result = comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
        
        assert result is True
        assert len(comm_tests.test_agents) >= 2  # Need at least 2 for communication testing
        
        # Verify message broker is set
        assert comm_tests.message_broker == message_broker
        assert comm_tests.coordinator == coordinator
    
    def test_inter_agent_message_communication(self):
        """Test inter-agent message communication functionality"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        # Setup mocks
        coordinator = Mock()
        coordinator.conversation_id = "test_comm_conv"
        coordinator.task_id = "test_comm_task"
        
        state_manager = Mock()
        message_broker = Mock()
        message_broker.send_message.return_value = True
        
        comm_tests = CoordinationCommunicationTests()
        comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
        
        # Run inter-agent communication test
        result = comm_tests.test_message_communication()
        
        assert isinstance(result, dict)
        assert result['status'] == 'passed'
        assert 'inter_agent_communication' in result
        assert 'broadcast_success' in result
        assert 'timestamp' in result
        
        # Should be stored in test results
        assert 'message_communication' in comm_tests.test_results
    
    def test_broadcast_message_functionality(self):
        """Test broadcast message functionality"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        coordinator = Mock()
        coordinator.conversation_id = "broadcast_test_conv"
        coordinator.task_id = "broadcast_test_task"
        
        state_manager = Mock()
        message_broker = Mock()
        message_broker.send_message.return_value = True
        
        comm_tests = CoordinationCommunicationTests()
        comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
        
        result = comm_tests.test_message_communication()
        
        # Verify broadcast message was sent
        assert message_broker.send_message.called
        assert result['broadcast_success'] is True
        
        # Check that broadcast message creation was attempted
        call_args = message_broker.send_message.call_args_list
        assert len(call_args) >= 1  # At least one message (broadcast)
    
    def test_message_processing_functionality(self):
        """Test message processing functionality for agents"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        coordinator = Mock()
        state_manager = Mock()
        
        # Mock message broker with messages to process
        mock_message = Mock()
        mock_message.sender_agent_id = "sender_agent"
        
        message_broker = Mock()
        message_broker.send_message.return_value = True
        
        comm_tests = CoordinationCommunicationTests()
        comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
        
        # Mock agent message processing
        for agent in comm_tests.test_agents.values():
            agent.process_pending_messages = Mock(return_value=1)
        
        result = comm_tests.test_message_communication()
        
        assert result['status'] == 'passed'
        
        # Verify message processing was called for recipient agents
        processed_agents = [agent for agent in comm_tests.test_agents.values() 
                          if agent.process_pending_messages.called]
        assert len(processed_agents) > 0
    
    def test_communication_error_handling(self):
        """Test communication tests handle errors gracefully"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        coordinator = Mock()
        state_manager = Mock()
        message_broker = Mock()
        message_broker.send_message.side_effect = Exception("Message sending failed")
        
        comm_tests = CoordinationCommunicationTests()
        comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
        
        # Should handle errors gracefully
        with pytest.raises(Exception) as excinfo:
            comm_tests.test_message_communication()
        
        assert "Message sending failed" in str(excinfo.value)
        
        # Should record error in test results
        assert 'message_communication' in comm_tests.test_results
        assert comm_tests.test_results['message_communication']['status'] == 'failed'
    
    def test_workflow_orchestration_testing(self):
        """Test workflow orchestration functionality"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        coordinator = Mock()
        coordinator.conversation_id = "workflow_test_conv"
        
        state_manager = Mock()
        message_broker = Mock()
        
        comm_tests = CoordinationCommunicationTests()
        comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
        
        # Test workflow orchestration
        result = comm_tests.test_workflow_orchestration()
        
        assert isinstance(result, dict)
        assert result['status'] == 'passed'
        assert 'workflow_created' in result
        assert 'steps_added' in result
        assert 'execution_results' in result
        assert 'timestamp' in result
        
        # Should be stored in test results
        assert 'workflow_orchestration' in comm_tests.test_results
    
    def test_get_communication_test_results(self):
        """Test retrieval of communication test results"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        coordinator = Mock()
        coordinator.conversation_id = "results_test"
        coordinator.task_id = "results_task"
        
        state_manager = Mock()
        message_broker = Mock()
        message_broker.send_message.return_value = True
        
        comm_tests = CoordinationCommunicationTests()
        comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
        comm_tests.test_message_communication()
        comm_tests.test_workflow_orchestration()
        
        results = comm_tests.get_test_results()
        
        assert isinstance(results, dict)
        assert 'message_communication' in results
        assert 'workflow_orchestration' in results
        assert results['message_communication']['status'] == 'passed'
        assert results['workflow_orchestration']['status'] == 'passed'


class TestCoordinationCommunicationTestsIntegration:
    """Test CoordinationCommunicationTests integration scenarios"""
    
    @patch('ltms.coordination.coordination_communication_tests.create_request_response_message')
    @patch('ltms.coordination.coordination_communication_tests.create_broadcast_message')
    def test_real_message_creation_integration(self, mock_broadcast, mock_request_response):
        """Test integration with real message creation functions"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        # Mock message creation functions
        mock_request_response.return_value = Mock()
        mock_broadcast.return_value = Mock()
        
        coordinator = Mock()
        coordinator.conversation_id = "integration_conv"
        coordinator.task_id = "integration_task"
        
        state_manager = Mock()
        message_broker = Mock()
        message_broker.send_message.return_value = True
        
        comm_tests = CoordinationCommunicationTests()
        comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
        
        result = comm_tests.test_message_communication()
        
        # Verify real message creation functions were used
        assert mock_broadcast.called
        assert result['status'] == 'passed'
    
    def test_workflow_orchestrator_integration(self):
        """Test integration with WorkflowOrchestrator"""
        from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
        
        coordinator = Mock()
        coordinator.conversation_id = "orchestrator_test"
        
        state_manager = Mock()
        message_broker = Mock()
        
        with patch('ltms.coordination.coordination_communication_tests.WorkflowOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator.workflow_id = "test_workflow"
            mock_orchestrator.add_workflow_step.return_value = True
            mock_orchestrator_class.return_value = mock_orchestrator
            
            comm_tests = CoordinationCommunicationTests()
            comm_tests.setup_test_agents(coordinator, state_manager, message_broker)
            
            result = comm_tests.test_workflow_orchestration()
            
            # Verify WorkflowOrchestrator was created and used
            mock_orchestrator_class.assert_called_once()
            assert mock_orchestrator.add_workflow_step.called
            assert result['workflow_created'] is True


# Pytest fixtures for CoordinationCommunicationTests testing
@pytest.fixture
def communication_tests_instance():
    """Fixture providing a CoordinationCommunicationTests instance"""
    from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
    return CoordinationCommunicationTests()

@pytest.fixture
def communication_test_setup():
    """Fixture providing setup coordination components for communication testing"""
    coordinator = Mock()
    coordinator.conversation_id = "fixture_comm_test"
    coordinator.task_id = "fixture_task"
    coordinator.register_agent.return_value = True
    
    state_manager = Mock()
    message_broker = Mock()
    message_broker.send_message.return_value = True
    
    return {
        'coordinator': coordinator,
        'state_manager': state_manager,
        'message_broker': message_broker
    }

@pytest.fixture
def communication_tests_with_agents(communication_test_setup):
    """Fixture providing CoordinationCommunicationTests with agents setup"""
    from ltms.coordination.coordination_communication_tests import CoordinationCommunicationTests
    
    comm_tests = CoordinationCommunicationTests()
    comm_tests.setup_test_agents(
        communication_test_setup['coordinator'],
        communication_test_setup['state_manager'],
        communication_test_setup['message_broker']
    )
    return comm_tests