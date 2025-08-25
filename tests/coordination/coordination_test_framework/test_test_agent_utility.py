"""
Comprehensive TDD tests for TestAgent utility class extraction.
Tests the TestAgent utility class that will be extracted from coordination_test_example.py.

Following TDD methodology: Tests written FIRST before extraction.
TestAgent will be extracted to test_agent_utility.py (~140 lines).
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestTestAgentUtility:
    """Test TestAgent utility class - to be extracted from coordination_test_example.py"""
    
    def test_test_agent_creation(self):
        """Test TestAgent class can be instantiated with required parameters"""
        from ltms.coordination.test_agent_utility import TestAgent
        from ltms.coordination.agent_coordination_framework import LTMCAgentCoordinator
        
        # Create mock coordinator
        coordinator = Mock(spec=LTMCAgentCoordinator)
        coordinator.conversation_id = "test_conv_123"
        coordinator.task_id = "test_task_456"
        
        agent = TestAgent("test_agent_1", "ltmc-test-agent", coordinator)
        
        assert agent.agent_id == "test_agent_1"
        assert agent.agent_type == "ltmc-test-agent"
        assert agent.coordinator == coordinator
        assert agent.state_manager is None  # Initially None until initialized
        assert agent.message_broker is None  # Initially None until initialized
        assert isinstance(agent.task_results, dict)
        assert isinstance(agent.received_messages, list)
        assert len(agent.task_results) == 0
        assert len(agent.received_messages) == 0
    
    def test_test_agent_initialize_method(self):
        """Test TestAgent.initialize method properly configures agent"""
        from ltms.coordination.test_agent_utility import TestAgent
        from ltms.coordination.agent_coordination_framework import LTMCAgentCoordinator
        from ltms.coordination.agent_state_manager import LTMCAgentStateManager
        from ltms.coordination.mcp_communication_patterns import LTMCMessageBroker
        
        # Create mocks
        coordinator = Mock(spec=LTMCAgentCoordinator)
        coordinator.register_agent.return_value = True
        
        state_manager = Mock(spec=LTMCAgentStateManager)
        message_broker = Mock(spec=LTMCMessageBroker)
        
        agent = TestAgent("test_agent_2", "ltmc-planner", coordinator)
        
        # Test initialization
        result = agent.initialize(state_manager, message_broker)
        
        assert result is True
        assert agent.state_manager == state_manager
        assert agent.message_broker == message_broker
        
        # Verify coordinator registration was called
        coordinator.register_agent.assert_called_once_with(
            "test_agent_2",
            "ltmc-planner", 
            task_scope=["ltmc-planner_tasks"],
            outputs=["ltmc-planner_results"]
        )
    
    def test_test_agent_initialize_registration_failure(self):
        """Test TestAgent.initialize handles coordinator registration failure"""
        from ltms.coordination.test_agent_utility import TestAgent
        
        # Create mocks
        coordinator = Mock()
        coordinator.register_agent.return_value = False  # Registration fails
        
        state_manager = Mock()
        message_broker = Mock()
        
        agent = TestAgent("test_agent_3", "ltmc-tester", coordinator)
        
        # Test initialization with failure
        result = agent.initialize(state_manager, message_broker)
        
        assert result is False
    
    @patch('ltms.coordination.test_agent_utility.memory_action')
    def test_execute_task_method(self, mock_memory_action):
        """Test TestAgent.execute_task method performs complete task simulation"""
        from ltms.coordination.test_agent_utility import TestAgent
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mocks
        mock_memory_action.return_value = {'success': True, 'doc_id': 123}
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conv_789"
        
        state_manager = Mock()
        
        agent = TestAgent("test_agent_4", "ltmc-executor", coordinator)
        agent.state_manager = state_manager
        
        # Execute task
        task_description = "Test task execution simulation"
        result = agent.execute_task(task_description)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert result["agent_id"] == "test_agent_4"
        assert result["task"] == task_description
        assert result["status"] == "completed"
        assert "timestamp" in result
        assert "findings" in result
        assert "metrics" in result
        assert isinstance(result["metrics"], dict)
        assert "execution_time" in result["metrics"]
        assert "success_rate" in result["metrics"]
        
        # Verify task was stored in agent's results
        assert task_description in agent.task_results
        assert agent.task_results[task_description] == result
        
        # Verify state transitions were called
        assert state_manager.transition_agent_state.call_count == 2  # ACTIVE and COMPLETED
        
        # Verify LTMC memory storage
        mock_memory_action.assert_called_once()
        call_args = mock_memory_action.call_args
        assert call_args[1]["action"] == "store"
        assert "test_agent_result_test_agent_4_" in call_args[1]["file_name"]
        assert "test_agent_result" in call_args[1]["tags"]
        assert "test_agent_4" in call_args[1]["tags"]
        assert "coordination_test" in call_args[1]["tags"]
    
    @patch('ltms.coordination.test_agent_utility.memory_action')
    def test_execute_task_error_handling(self, mock_memory_action):
        """Test TestAgent.execute_task handles errors gracefully"""
        from ltms.coordination.test_agent_utility import TestAgent
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mocks - memory_action succeeds but state_manager fails
        mock_memory_action.return_value = {'success': True}
        
        coordinator = Mock()
        state_manager = Mock()
        state_manager.transition_agent_state.side_effect = Exception("State transition failed")
        
        agent = TestAgent("test_agent_5", "ltmc-error-test", coordinator)
        agent.state_manager = state_manager
        
        # Execute task with error
        result = agent.execute_task("Error test task")
        
        # Should return error result
        assert isinstance(result, dict)
        assert "error" in result
        assert "State transition failed" in result["error"]
    
    def test_send_message_to_agent_method(self):
        """Test TestAgent.send_message_to_agent method creates and sends messages"""
        from ltms.coordination.test_agent_utility import TestAgent
        from ltms.coordination.mcp_communication_patterns import MCPMessage
        
        # Setup mocks
        coordinator = Mock()
        coordinator.conversation_id = "test_conv_msg"
        coordinator.task_id = "test_task_msg"
        
        message_broker = Mock()
        message_broker.send_message.return_value = True
        
        agent = TestAgent("sender_agent", "ltmc-sender", coordinator)
        agent.message_broker = message_broker
        
        # Test message sending
        message_content = {
            "test_data": "Hello from sender",
            "priority": "high"
        }
        
        result = agent.send_message_to_agent("recipient_agent", message_content)
        
        assert result is True
        
        # Verify message broker was called
        message_broker.send_message.assert_called_once()
        
        # Verify message structure (via the mock call)
        sent_message = message_broker.send_message.call_args[0][0]
        assert hasattr(sent_message, 'sender_agent_id')
        assert hasattr(sent_message, 'recipient_agent_id')
    
    def test_send_message_without_broker(self):
        """Test TestAgent.send_message_to_agent returns False without message broker"""
        from ltms.coordination.test_agent_utility import TestAgent
        
        coordinator = Mock()
        agent = TestAgent("no_broker_agent", "ltmc-no-broker", coordinator)
        # message_broker remains None
        
        result = agent.send_message_to_agent("recipient", {"data": "test"})
        
        assert result is False
    
    def test_process_pending_messages_method(self):
        """Test TestAgent.process_pending_messages handles incoming messages"""
        from ltms.coordination.test_agent_utility import TestAgent
        from ltms.coordination.mcp_communication_patterns import MCPMessage
        
        # Create mock messages
        mock_message_1 = Mock()
        mock_message_1.sender_agent_id = "sender_1"
        
        mock_message_2 = Mock()
        mock_message_2.sender_agent_id = "sender_2"
        
        # Setup mocks
        coordinator = Mock()
        message_broker = Mock()
        message_broker.receive_messages.return_value = [mock_message_1, mock_message_2]
        
        agent = TestAgent("receiver_agent", "ltmc-receiver", coordinator)
        agent.message_broker = message_broker
        
        # Process messages
        processed_count = agent.process_pending_messages()
        
        assert processed_count == 2
        assert len(agent.received_messages) == 2
        assert agent.received_messages[0] == mock_message_1
        assert agent.received_messages[1] == mock_message_2
        
        # Verify broker was called with agent ID
        message_broker.receive_messages.assert_called_once_with("receiver_agent")
    
    def test_process_pending_messages_without_broker(self):
        """Test TestAgent.process_pending_messages returns 0 without message broker"""
        from ltms.coordination.test_agent_utility import TestAgent
        
        coordinator = Mock()
        agent = TestAgent("no_broker_receiver", "ltmc-no-broker", coordinator)
        # message_broker remains None
        
        processed_count = agent.process_pending_messages()
        
        assert processed_count == 0
        assert len(agent.received_messages) == 0
    
    def test_process_pending_messages_error_handling(self):
        """Test TestAgent.process_pending_messages handles processing errors"""
        from ltms.coordination.test_agent_utility import TestAgent
        
        # Create problematic mock message that will cause processing error
        mock_message = Mock()
        mock_message.sender_agent_id = None  # This might cause issues
        
        coordinator = Mock()
        message_broker = Mock()
        message_broker.receive_messages.return_value = [mock_message]
        
        agent = TestAgent("error_receiver", "ltmc-error-receiver", coordinator)
        agent.message_broker = message_broker
        
        # Should handle errors gracefully and continue
        processed_count = agent.process_pending_messages()
        
        # Even with error, should return count of attempted processing
        assert processed_count >= 0


class TestTestAgentUtilityIntegration:
    """Test TestAgent integration scenarios with coordination framework"""
    
    def test_complete_agent_workflow(self):
        """Test complete TestAgent workflow from initialization through task execution"""
        from ltms.coordination.test_agent_utility import TestAgent
        
        # Setup complete coordination framework mocks
        coordinator = Mock()
        coordinator.conversation_id = "integration_test_conv"
        coordinator.task_id = "integration_test_task"
        coordinator.register_agent.return_value = True
        
        state_manager = Mock()
        message_broker = Mock()
        message_broker.send_message.return_value = True
        message_broker.receive_messages.return_value = []
        
        with patch('ltms.coordination.test_agent_utility.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            # Create and initialize agent
            agent = TestAgent("integration_agent", "ltmc-integration", coordinator)
            init_success = agent.initialize(state_manager, message_broker)
            
            assert init_success is True
            
            # Execute task
            task_result = agent.execute_task("Integration test task")
            
            assert task_result["status"] == "completed"
            assert task_result["agent_id"] == "integration_agent"
            
            # Send message
            message_sent = agent.send_message_to_agent("other_agent", {"data": "test"})
            
            assert message_sent is True
            
            # Process messages
            processed = agent.process_pending_messages()
            
            assert processed == 0  # No messages in this test
            
            # Verify all components were used
            coordinator.register_agent.assert_called_once()
            message_broker.send_message.assert_called_once()
            message_broker.receive_messages.assert_called_once()
            mock_memory.assert_called_once()
    
    def test_agent_coordination_handoff_simulation(self):
        """Test TestAgent can simulate agent-to-agent coordination handoffs"""
        from ltms.coordination.test_agent_utility import TestAgent
        
        # Create two agents for handoff simulation
        coordinator = Mock()
        coordinator.conversation_id = "handoff_test"
        coordinator.task_id = "handoff_task"
        coordinator.register_agent.return_value = True
        
        state_manager = Mock()
        message_broker = Mock()
        message_broker.send_message.return_value = True
        
        # Mock received messages for handoff
        handoff_message = Mock()
        handoff_message.sender_agent_id = "agent_1"
        message_broker.receive_messages.return_value = [handoff_message]
        
        with patch('ltms.coordination.test_agent_utility.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            # Agent 1 (sender)
            agent_1 = TestAgent("agent_1", "ltmc-planner", coordinator)
            agent_1.initialize(state_manager, message_broker)
            
            # Agent 2 (receiver)
            agent_2 = TestAgent("agent_2", "ltmc-executor", coordinator)
            agent_2.initialize(state_manager, message_broker)
            
            # Agent 1 executes task and hands off to Agent 2
            task_result = agent_1.execute_task("Planning task")
            handoff_success = agent_1.send_message_to_agent("agent_2", {
                "handoff_data": task_result,
                "next_task": "Execute based on plan"
            })
            
            # Agent 2 receives handoff and processes
            messages_received = agent_2.process_pending_messages()
            
            assert task_result["status"] == "completed"
            assert handoff_success is True
            assert messages_received == 1
            assert len(agent_2.received_messages) == 1


# Pytest fixtures for TestAgent testing
@pytest.fixture
def mock_coordinator():
    """Fixture providing a mock LTMCAgentCoordinator"""
    coordinator = Mock()
    coordinator.conversation_id = "test_conversation_123"
    coordinator.task_id = "test_task_456"
    coordinator.register_agent.return_value = True
    return coordinator

@pytest.fixture
def mock_state_manager():
    """Fixture providing a mock LTMCAgentStateManager"""
    state_manager = Mock()
    return state_manager

@pytest.fixture
def mock_message_broker():
    """Fixture providing a mock LTMCMessageBroker"""
    message_broker = Mock()
    message_broker.send_message.return_value = True
    message_broker.receive_messages.return_value = []
    return message_broker

@pytest.fixture
def initialized_test_agent(mock_coordinator, mock_state_manager, mock_message_broker):
    """Fixture providing a fully initialized TestAgent"""
    from ltms.coordination.test_agent_utility import TestAgent
    
    agent = TestAgent("fixture_agent", "ltmc-test", mock_coordinator)
    agent.initialize(mock_state_manager, mock_message_broker)
    return agent

@pytest.fixture
def sample_task_result():
    """Fixture providing a sample task result structure"""
    return {
        "agent_id": "sample_agent",
        "task": "Sample task",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "findings": "Sample findings",
        "metrics": {
            "execution_time": "0.1s",
            "success_rate": "100%"
        }
    }