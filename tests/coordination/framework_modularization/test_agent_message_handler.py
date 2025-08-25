"""
Comprehensive TDD tests for AgentMessageHandler extraction.
Tests the message communication functionality for agent coordination.

Following TDD methodology: Tests written FIRST before extraction.
AgentMessageHandler will handle inter-agent communication via LTMC tools.
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestAgentMessageHandler:
    """Test AgentMessageHandler class - to be extracted from agent_coordination_framework.py"""
    
    def test_agent_message_handler_creation(self):
        """Test AgentMessageHandler can be instantiated"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        
        handler = AgentMessageHandler("test_task_123", "test_conv_456")
        
        assert hasattr(handler, 'task_id')
        assert hasattr(handler, 'conversation_id')
        assert handler.task_id == "test_task_123"
        assert handler.conversation_id == "test_conv_456"
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_send_agent_message_success(self, mock_memory_action):
        """Test successful agent message sending with LTMC integration"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        # Setup mocks
        mock_memory_action.return_value = {'success': True, 'doc_id': 789}
        
        handler = AgentMessageHandler("msg_task", "msg_conv")
        
        # Create test message
        message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="test_recipient",
            message_type="test_message",
            content={"test_data": "message_content"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id="msg_conv",
            task_id="msg_task",
            requires_response=True
        )
        
        # Mock registered agents (sender must be registered)
        registered_agents = {"test_sender", "test_recipient"}
        
        # Test message sending
        result = handler.send_agent_message(message, registered_agents)
        
        assert result is True
        
        # Verify LTMC memory_action was called
        mock_memory_action.assert_called_once()
        
        # Verify memory_action call structure
        memory_call = mock_memory_action.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'agent_message_test_sender_to_test_recipient' in memory_call[1]['file_name']
        assert 'agent_communication' in memory_call[1]['tags']
        assert 'test_sender' in memory_call[1]['tags']
        assert 'test_recipient' in memory_call[1]['tags']
        assert 'msg_task' in memory_call[1]['tags']
        
        # Verify message content structure in stored document
        stored_content = memory_call[1]['content']
        assert 'test_sender → test_recipient' in stored_content
        assert 'test_message' in stored_content
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_send_broadcast_message(self, mock_memory_action):
        """Test broadcast message sending (no specific recipient)"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        mock_memory_action.return_value = {'success': True}
        
        handler = AgentMessageHandler("broadcast_task", "broadcast_conv")
        
        # Create broadcast message
        broadcast_message = AgentMessage(
            sender_agent="broadcast_sender",
            recipient_agent=None,  # Broadcast message
            message_type="broadcast_announcement",
            content={"announcement": "broadcast_data"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id="broadcast_conv",
            task_id="broadcast_task"
        )
        
        registered_agents = {"broadcast_sender"}
        
        result = handler.send_agent_message(broadcast_message, registered_agents)
        
        assert result is True
        
        # Verify broadcast message handling
        memory_call = mock_memory_action.call_args
        assert 'agent_message_broadcast_sender_to_broadcast' in memory_call[1]['file_name']
        assert 'broadcast' in memory_call[1]['tags']
    
    def test_send_message_unregistered_sender(self):
        """Test sending message from unregistered agent fails"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        handler = AgentMessageHandler("unreg_task", "unreg_conv")
        
        message = AgentMessage(
            sender_agent="unregistered_sender",
            recipient_agent="test_recipient",
            message_type="test_message",
            content={"data": "test"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id="unreg_conv",
            task_id="unreg_task"
        )
        
        # Empty registered agents - sender not registered
        registered_agents = set()
        
        result = handler.send_agent_message(message, registered_agents)
        
        assert result is False
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_send_message_ltmc_error(self, mock_memory_action):
        """Test message sending handles LTMC storage errors gracefully"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        # Setup mock to fail
        mock_memory_action.side_effect = Exception("LTMC storage failed")
        
        handler = AgentMessageHandler("error_task", "error_conv")
        
        message = AgentMessage(
            sender_agent="error_sender",
            recipient_agent="error_recipient",
            message_type="error_test",
            content={"error": "test"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id="error_conv",
            task_id="error_task"
        )
        
        registered_agents = {"error_sender"}
        
        result = handler.send_agent_message(message, registered_agents)
        
        assert result is False
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_retrieve_agent_messages_success(self, mock_memory_action):
        """Test successful retrieval of agent messages from LTMC"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        
        # Setup mock memory response
        mock_documents = [
            {
                'id': 1,
                'content': '# Agent Message: sender1 → target_agent\n\n{"message_type": "test1"}',
                'metadata': {'timestamp': '2025-08-24T10:30:00Z'}
            },
            {
                'id': 2, 
                'content': '# Agent Message: sender2 → target_agent\n\n{"message_type": "test2"}',
                'metadata': {'timestamp': '2025-08-24T10:31:00Z'}
            },
            {
                'id': 3,
                'content': '# Agent Message: sender3 → other_agent\n\n{"message_type": "test3"}',
                'metadata': {'timestamp': '2025-08-24T10:32:00Z'}
            }
        ]
        
        mock_memory_action.return_value = {
            'success': True,
            'documents': mock_documents
        }
        
        handler = AgentMessageHandler("retrieve_task", "retrieve_conv")
        
        # Test message retrieval
        messages = handler.retrieve_agent_messages("target_agent")
        
        assert isinstance(messages, list)
        assert len(messages) == 2  # Only messages for target_agent
        
        # Verify LTMC memory_action was called correctly
        mock_memory_action.assert_called_once()
        memory_call = mock_memory_action.call_args
        assert memory_call[1]['action'] == 'retrieve'
        assert 'agent communication target_agent' in memory_call[1]['query']
        assert memory_call[1]['conversation_id'] == 'retrieve_conv'
        
        # Verify returned message structure
        for message in messages:
            assert 'document' in message
            assert 'parsed_content' in message
            assert '→ target_agent' in message['parsed_content']
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_retrieve_agent_messages_no_results(self, mock_memory_action):
        """Test message retrieval with no results"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        
        # Setup mock with no documents
        mock_memory_action.return_value = {
            'success': True,
            'documents': []
        }
        
        handler = AgentMessageHandler("no_msgs_task", "no_msgs_conv")
        
        messages = handler.retrieve_agent_messages("no_messages_agent")
        
        assert isinstance(messages, list)
        assert len(messages) == 0
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_retrieve_agent_messages_ltmc_error(self, mock_memory_action):
        """Test message retrieval handles LTMC errors gracefully"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        
        # Setup mock to fail
        mock_memory_action.side_effect = Exception("LTMC retrieval failed")
        
        handler = AgentMessageHandler("error_retrieve_task", "error_retrieve_conv")
        
        messages = handler.retrieve_agent_messages("error_agent")
        
        assert isinstance(messages, list)
        assert len(messages) == 0
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_retrieve_messages_with_timestamp_filter(self, mock_memory_action):
        """Test message retrieval with timestamp filtering"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        
        # Setup mock documents with various timestamps
        mock_documents = [
            {
                'id': 1,
                'content': '# Agent Message: sender1 → filtered_agent\n\n{"timestamp": "2025-08-24T10:30:00Z"}',
                'metadata': {'timestamp': '2025-08-24T10:30:00Z'}
            },
            {
                'id': 2,
                'content': '# Agent Message: sender2 → filtered_agent\n\n{"timestamp": "2025-08-24T10:35:00Z"}',
                'metadata': {'timestamp': '2025-08-24T10:35:00Z'}
            }
        ]
        
        mock_memory_action.return_value = {
            'success': True,
            'documents': mock_documents
        }
        
        handler = AgentMessageHandler("filter_task", "filter_conv")
        
        # Test with timestamp filter
        since_timestamp = "2025-08-24T10:32:00Z"
        messages = handler.retrieve_agent_messages("filtered_agent", since_timestamp)
        
        assert isinstance(messages, list)
        # Handler should return all documents and let caller filter by timestamp
        # The actual filtering would be application-specific
        assert len(messages) == 2
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_retrieve_messages_parsing_errors(self, mock_memory_action):
        """Test message retrieval handles document parsing errors gracefully"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        
        # Setup mock documents with parsing issues
        mock_documents = [
            {
                'id': 1,
                'content': '# Valid Message: sender → parse_test_agent\n\n{"valid": true}',
            },
            {
                'id': 2,
                'content': 'Invalid document format',  # This will cause parsing issues
            },
            {
                'id': 3,
                'content': None,  # This might cause issues
            }
        ]
        
        mock_memory_action.return_value = {
            'success': True,
            'documents': mock_documents
        }
        
        handler = AgentMessageHandler("parse_error_task", "parse_error_conv")
        
        messages = handler.retrieve_agent_messages("parse_test_agent")
        
        # Should handle parsing errors gracefully and return valid messages
        assert isinstance(messages, list)
        assert len(messages) == 1  # Only the valid message
        assert '→ parse_test_agent' in messages[0]['parsed_content']
    
    def test_get_message_statistics(self):
        """Test retrieval of message handling statistics"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        
        handler = AgentMessageHandler("stats_task", "stats_conv")
        
        # Test initial statistics
        stats = handler.get_message_statistics()
        
        assert isinstance(stats, dict)
        assert 'task_id' in stats
        assert 'conversation_id' in stats
        assert stats['task_id'] == "stats_task"
        assert stats['conversation_id'] == "stats_conv"
        # Additional statistics would be added based on implementation


class TestAgentMessageHandlerIntegration:
    """Test AgentMessageHandler integration scenarios"""
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_complete_message_workflow(self, mock_memory_action):
        """Test complete message send and retrieve workflow"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        # Setup mock for sending
        mock_memory_action.return_value = {'success': True, 'doc_id': 999}
        
        handler = AgentMessageHandler("workflow_task", "workflow_conv")
        
        # Send message
        message = AgentMessage(
            sender_agent="workflow_sender",
            recipient_agent="workflow_recipient",
            message_type="workflow_test",
            content={"workflow": "test_data"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id="workflow_conv",
            task_id="workflow_task"
        )
        
        registered_agents = {"workflow_sender", "workflow_recipient"}
        send_result = handler.send_agent_message(message, registered_agents)
        
        assert send_result is True
        
        # Setup mock for retrieval
        mock_memory_action.return_value = {
            'success': True,
            'documents': [
                {
                    'id': 999,
                    'content': f'# Agent Message: workflow_sender → workflow_recipient\n\n{json.dumps({"workflow": "test_data"})}',
                }
            ]
        }
        
        # Retrieve messages
        messages = handler.retrieve_agent_messages("workflow_recipient")
        
        assert len(messages) == 1
        assert 'workflow_sender → workflow_recipient' in messages[0]['parsed_content']
    
    @patch('ltms.coordination.agent_message_handler.memory_action')
    def test_multiple_agent_communication(self, mock_memory_action):
        """Test communication between multiple agents"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        mock_memory_action.return_value = {'success': True}
        
        handler = AgentMessageHandler("multi_comm_task", "multi_comm_conv")
        
        registered_agents = {"agent_a", "agent_b", "agent_c"}
        
        # Send messages from A to B and B to C
        message_a_to_b = AgentMessage(
            sender_agent="agent_a",
            recipient_agent="agent_b", 
            message_type="coordination",
            content={"from_a": "data_for_b"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id="multi_comm_conv",
            task_id="multi_comm_task"
        )
        
        message_b_to_c = AgentMessage(
            sender_agent="agent_b",
            recipient_agent="agent_c",
            message_type="handoff",
            content={"from_b": "processed_data_for_c"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id="multi_comm_conv",
            task_id="multi_comm_task"
        )
        
        # Send both messages
        result_1 = handler.send_agent_message(message_a_to_b, registered_agents)
        result_2 = handler.send_agent_message(message_b_to_c, registered_agents)
        
        assert result_1 is True
        assert result_2 is True
        
        # Verify both messages were stored
        assert mock_memory_action.call_count == 2
    
    def test_message_handler_with_registration_manager_integration(self):
        """Test AgentMessageHandler integration with AgentRegistrationManager"""
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        # Create both managers
        registration_manager = AgentRegistrationManager("integration_task", "integration_conv")
        message_handler = AgentMessageHandler("integration_task", "integration_conv")
        
        # Register agents
        with patch('ltms.coordination.agent_registration_manager.memory_action'):
            with patch('ltms.coordination.agent_registration_manager.graph_action'):
                registration_manager.register_agent("integrated_sender", "ltmc-sender", ["send_tasks"])
                registration_manager.register_agent("integrated_receiver", "ltmc-receiver", ["receive_tasks"])
        
        # Get registered agent IDs for message validation
        registered_agents = set(registration_manager.get_all_registrations().keys())
        
        # Create and send message
        message = AgentMessage(
            sender_agent="integrated_sender",
            recipient_agent="integrated_receiver",
            message_type="integration_test",
            content={"integration": "success"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id="integration_conv",
            task_id="integration_task"
        )
        
        with patch('ltms.coordination.agent_message_handler.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            result = message_handler.send_agent_message(message, registered_agents)
            
            assert result is True
            
            # Verify message was sent between registered agents
            memory_call = mock_memory.call_args
            assert 'integrated_sender_to_integrated_receiver' in memory_call[1]['file_name']


# Pytest fixtures for message handler testing  
@pytest.fixture
def message_handler():
    """Fixture providing an AgentMessageHandler instance"""
    from ltms.coordination.agent_message_handler import AgentMessageHandler
    return AgentMessageHandler("fixture_task", "fixture_conv")

@pytest.fixture
def sample_agent_message():
    """Fixture providing sample AgentMessage for testing"""
    from ltms.coordination.agent_coordination_models import AgentMessage
    
    return AgentMessage(
        sender_agent="fixture_sender",
        recipient_agent="fixture_recipient", 
        message_type="fixture_test",
        content={"fixture": "message_data"},
        timestamp=datetime.now(timezone.utc).isoformat(),
        conversation_id="fixture_conv",
        task_id="fixture_task"
    )

@pytest.fixture
def registered_agents():
    """Fixture providing set of registered agent IDs"""
    return {"fixture_sender", "fixture_recipient", "fixture_broadcast"}

@pytest.fixture
def mock_ltmc_memory():
    """Fixture providing mocked LTMC memory_action"""
    with patch('ltms.coordination.agent_message_handler.memory_action') as mock_memory:
        mock_memory.return_value = {'success': True, 'doc_id': 888}
        yield mock_memory