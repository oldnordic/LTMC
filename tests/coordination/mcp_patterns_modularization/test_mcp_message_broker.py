"""
Comprehensive TDD tests for MCP Message Broker extraction.
Tests LTMC integration, message handling, and broker functionality.

Following TDD methodology: Tests written FIRST before extraction.
LTMCMessageBroker will handle persistent messaging via LTMC MCP tools.
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import Mock, patch, MagicMock
import uuid


class TestLTMCMessageBroker:
    """Test LTMCMessageBroker class - to be extracted from mcp_communication_patterns.py"""
    
    def test_message_broker_creation(self):
        """Test LTMCMessageBroker can be instantiated"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        broker = LTMCMessageBroker("test_conversation_123")
        
        assert hasattr(broker, 'conversation_id')
        assert hasattr(broker, 'message_handlers')
        assert broker.conversation_id == "test_conversation_123"
        assert isinstance(broker.message_handlers, dict)
        assert len(broker.message_handlers) == 0
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    @patch('ltms.coordination.mcp_message_broker.graph_action')
    def test_send_message_success(self, mock_graph_action, mock_memory_action):
        """Test successful message sending with LTMC integration"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        # Setup mocks
        mock_memory_action.return_value = {'success': True, 'doc_id': 123}
        mock_graph_action.return_value = {'success': True}
        
        broker = LTMCMessageBroker("broker_test_conv")
        
        # Create test message
        message = MCPMessage(
            message_id="broker_test_msg_123",
            sender_agent_id="broker_sender",
            recipient_agent_id="broker_recipient",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.NORMAL,
            message_type="broker_test",
            payload={"broker": "test_data"},
            conversation_id="broker_test_conv",
            task_id="broker_test_task",
            timestamp=datetime.now(timezone.utc).isoformat(),
            requires_ack=True,
            correlation_id="broker_correlation_456"
        )
        
        # Test message sending
        result = broker.send_message(message)
        
        assert result is True
        
        # Verify LTMC memory_action was called correctly
        mock_memory_action.assert_called_once()
        memory_call = mock_memory_action.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'mcp_message_broker_test_msg_123.json' in memory_call[1]['file_name']
        assert 'mcp_message' in memory_call[1]['tags']
        assert 'broker_sender' in memory_call[1]['tags']
        assert 'broker_recipient' in memory_call[1]['tags']
        assert 'request_response' in memory_call[1]['tags']
        assert 'normal' in memory_call[1]['tags']
        assert 'broker_test_task' in memory_call[1]['tags']
        
        # Verify message content structure
        stored_content = json.loads(memory_call[1]['content'])
        assert stored_content['mcp_message'] is True
        assert stored_content['message_id'] == "broker_test_msg_123"
        assert stored_content['sender'] == "broker_sender"
        assert stored_content['recipient'] == "broker_recipient"
        assert stored_content['protocol'] == "request_response"
        assert stored_content['priority'] == "normal"
        assert stored_content['type'] == "broker_test"
        assert stored_content['payload'] == {"broker": "test_data"}
        assert stored_content['requires_ack'] is True
        assert stored_content['correlation_id'] == "broker_correlation_456"
        
        # Verify graph relationship was created
        mock_graph_action.assert_called_once()
        graph_call = mock_graph_action.call_args
        assert graph_call[1]['action'] == 'link'
        assert graph_call[1]['source_entity'] == 'agent_broker_sender'
        assert graph_call[1]['target_entity'] == 'agent_broker_recipient'
        assert graph_call[1]['relationship'] == 'sends_message_to'
        assert graph_call[1]['properties']['message_id'] == "broker_test_msg_123"
        assert graph_call[1]['properties']['protocol'] == "request_response"
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    @patch('ltms.coordination.mcp_message_broker.graph_action')
    def test_send_broadcast_message(self, mock_graph_action, mock_memory_action):
        """Test broadcast message sending (no specific recipient)"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        mock_memory_action.return_value = {'success': True}
        mock_graph_action.return_value = {'success': True}
        
        broker = LTMCMessageBroker("broadcast_test_conv")
        
        # Create broadcast message
        broadcast_message = MCPMessage(
            message_id="broadcast_msg_789",
            sender_agent_id="broadcast_sender",
            recipient_agent_id=None,  # Broadcast
            protocol=CommunicationProtocol.BROADCAST,
            priority=MessagePriority.HIGH,
            message_type="broadcast_announcement",
            payload={"announcement": "broadcast_data"},
            conversation_id="broadcast_test_conv",
            task_id="broadcast_test_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        result = broker.send_message(broadcast_message)
        
        assert result is True
        
        # Verify broadcast message handling
        memory_call = mock_memory_action.call_args
        stored_content = json.loads(memory_call[1]['content'])
        assert stored_content['recipient'] is None
        assert stored_content['protocol'] == "broadcast"
        
        # Verify graph relationship for broadcast
        graph_call = mock_graph_action.call_args
        assert graph_call[1]['target_entity'] == 'broadcast'
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_send_message_ltmc_failure(self, mock_memory_action):
        """Test message sending handles LTMC storage failures gracefully"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        # Setup mock to fail
        mock_memory_action.return_value = {'success': False, 'error': 'Storage failed'}
        
        broker = LTMCMessageBroker("error_test_conv")
        
        message = MCPMessage(
            message_id="error_test_msg",
            sender_agent_id="error_sender",
            recipient_agent_id="error_recipient",
            protocol=CommunicationProtocol.COORDINATION,
            priority=MessagePriority.CRITICAL,
            message_type="error_test",
            payload={"error": "test"},
            conversation_id="error_test_conv",
            task_id="error_test_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        result = broker.send_message(message)
        
        assert result is False
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_send_message_exception_handling(self, mock_memory_action):
        """Test message sending handles exceptions gracefully"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        # Setup mock to raise exception
        mock_memory_action.side_effect = Exception("LTMC storage exception")
        
        broker = LTMCMessageBroker("exception_test_conv")
        
        message = MCPMessage(
            message_id="exception_test_msg",
            sender_agent_id="exception_sender",
            recipient_agent_id="exception_recipient",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.LOW,
            message_type="exception_test",
            payload={"exception": "test"},
            conversation_id="exception_test_conv",
            task_id="exception_test_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        result = broker.send_message(message)
        
        assert result is False
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_receive_messages_success(self, mock_memory_action):
        """Test successful message retrieval from LTMC"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        # Setup mock memory response
        mock_documents = [
            {
                'id': 1,
                'content': json.dumps({
                    "mcp_message": True,
                    "message_id": "retrieved_msg_1",
                    "sender": "retrieve_sender_1",
                    "recipient": "test_agent",
                    "protocol": "request_response",
                    "priority": "normal",
                    "type": "retrieve_test_1",
                    "payload": {"retrieve": "test_1"},
                    "timestamp": "2025-08-24T10:30:00Z",
                    "expires_at": None,
                    "requires_ack": False,
                    "correlation_id": None,
                    "task_id": "retrieve_test_task"
                })
            },
            {
                'id': 2,
                'content': json.dumps({
                    "mcp_message": True,
                    "message_id": "retrieved_msg_2",
                    "sender": "retrieve_sender_2",
                    "recipient": "test_agent",
                    "protocol": "coordination",
                    "priority": "high",
                    "type": "retrieve_test_2",
                    "payload": {"retrieve": "test_2"},
                    "timestamp": "2025-08-24T10:35:00Z",
                    "expires_at": "2025-08-24T12:00:00Z",
                    "requires_ack": True,
                    "correlation_id": "correlation_456",
                    "task_id": "retrieve_test_task"
                })
            }
        ]
        
        mock_memory_action.return_value = {
            'success': True,
            'documents': mock_documents
        }
        
        broker = LTMCMessageBroker("retrieve_test_conv")
        
        # Test message retrieval
        messages = broker.receive_messages("test_agent")
        
        assert isinstance(messages, list)
        assert len(messages) == 2
        
        # Verify LTMC memory_action was called correctly
        mock_memory_action.assert_called_once()
        memory_call = mock_memory_action.call_args
        assert memory_call[1]['action'] == 'retrieve'
        assert 'mcp_message recipient:test_agent' in memory_call[1]['query']
        assert memory_call[1]['conversation_id'] == 'retrieve_test_conv'
        
        # Verify reconstructed message 1
        msg1 = messages[0]
        assert msg1.message_id == "retrieved_msg_1"
        assert msg1.sender_agent_id == "retrieve_sender_1"
        assert msg1.recipient_agent_id == "test_agent"
        assert msg1.message_type == "retrieve_test_1"
        assert msg1.payload == {"retrieve": "test_1"}
        assert msg1.requires_ack is False
        assert msg1.correlation_id is None
        
        # Verify reconstructed message 2
        msg2 = messages[1]
        assert msg2.message_id == "retrieved_msg_2"
        assert msg2.expires_at == "2025-08-24T12:00:00Z"
        assert msg2.requires_ack is True
        assert msg2.correlation_id == "correlation_456"
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_receive_messages_with_timestamp_filter(self, mock_memory_action):
        """Test message retrieval with timestamp filtering"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        # Setup mock with messages at different timestamps
        mock_documents = [
            {
                'id': 1,
                'content': json.dumps({
                    "mcp_message": True,
                    "message_id": "old_msg_1",
                    "sender": "time_sender",
                    "recipient": "time_agent",
                    "protocol": "coordination",
                    "priority": "normal",
                    "type": "time_test",
                    "payload": {"time": "old"},
                    "timestamp": "2025-08-24T10:00:00Z",  # Old
                    "task_id": "time_test_task"
                })
            },
            {
                'id': 2,
                'content': json.dumps({
                    "mcp_message": True,
                    "message_id": "new_msg_2",
                    "sender": "time_sender",
                    "recipient": "time_agent",
                    "protocol": "coordination", 
                    "priority": "normal",
                    "type": "time_test",
                    "payload": {"time": "new"},
                    "timestamp": "2025-08-24T11:00:00Z",  # New
                    "task_id": "time_test_task"
                })
            }
        ]
        
        mock_memory_action.return_value = {
            'success': True,
            'documents': mock_documents
        }
        
        broker = LTMCMessageBroker("time_filter_conv")
        
        # Test with timestamp filter
        since_timestamp = "2025-08-24T10:30:00Z"
        messages = broker.receive_messages("time_agent", since_timestamp)
        
        # Should only return messages after the filter timestamp
        assert len(messages) == 1
        assert messages[0].message_id == "new_msg_2"
        assert messages[0].payload == {"time": "new"}
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_receive_messages_no_results(self, mock_memory_action):
        """Test message retrieval with no results"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        mock_memory_action.return_value = {
            'success': True,
            'documents': []
        }
        
        broker = LTMCMessageBroker("no_messages_conv")
        
        messages = broker.receive_messages("no_messages_agent")
        
        assert isinstance(messages, list)
        assert len(messages) == 0
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_receive_messages_parsing_errors(self, mock_memory_action):
        """Test message retrieval handles parsing errors gracefully"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        # Setup mock with some invalid documents
        mock_documents = [
            {
                'id': 1,
                'content': json.dumps({
                    "mcp_message": True,
                    "message_id": "valid_msg",
                    "sender": "parse_sender",
                    "recipient": "parse_agent",
                    "protocol": "coordination",
                    "priority": "normal",
                    "type": "parse_test",
                    "payload": {"valid": True},
                    "timestamp": "2025-08-24T10:30:00Z",
                    "task_id": "parse_test_task"
                })
            },
            {
                'id': 2,
                'content': 'invalid json content'
            },
            {
                'id': 3,
                'content': None
            }
        ]
        
        mock_memory_action.return_value = {
            'success': True,
            'documents': mock_documents
        }
        
        broker = LTMCMessageBroker("parse_error_conv")
        
        messages = broker.receive_messages("parse_agent")
        
        # Should only return valid messages, skip parsing errors
        assert len(messages) == 1
        assert messages[0].message_id == "valid_msg"
        assert messages[0].payload == {"valid": True}
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_receive_messages_ltmc_failure(self, mock_memory_action):
        """Test message retrieval handles LTMC failures gracefully"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        # Setup mock to fail
        mock_memory_action.return_value = {'success': False, 'error': 'Retrieval failed'}
        
        broker = LTMCMessageBroker("fail_retrieve_conv")
        
        messages = broker.receive_messages("fail_agent")
        
        assert isinstance(messages, list)
        assert len(messages) == 0
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_send_response_success(self, mock_memory_action):
        """Test successful response sending with LTMC integration"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        
        mock_memory_action.return_value = {'success': True, 'doc_id': 456}
        
        broker = LTMCMessageBroker("response_test_conv")
        
        # Create original message
        original_message = MCPMessage(
            message_id="response_original_123",
            sender_agent_id="response_requester",
            recipient_agent_id="response_handler",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.NORMAL,
            message_type="response_test",
            payload={"request": "data"},
            conversation_id="response_test_conv",
            task_id="response_test_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Create response
        response = MCPResponse(
            original_message=original_message,
            response_payload={"result": "success", "data": "response_data"},
            success=True
        )
        
        # Test response sending
        result = broker.send_response(response)
        
        assert result is True
        
        # Verify LTMC memory_action was called correctly
        mock_memory_action.assert_called_once()
        memory_call = mock_memory_action.call_args
        assert memory_call[1]['action'] == 'store'
        assert f'mcp_response_{response.response_id}.json' in memory_call[1]['file_name']
        assert 'mcp_response' in memory_call[1]['tags']
        assert 'response_handler' in memory_call[1]['tags']  # Sender in response
        assert 'response_requester' in memory_call[1]['tags']  # Recipient in response
        
        # Verify response content structure
        stored_content = json.loads(memory_call[1]['content'])
        assert stored_content['mcp_response'] is True
        assert stored_content['original_message_id'] == "response_original_123"
        assert stored_content['sender'] == "response_handler"
        assert stored_content['recipient'] == "response_requester"
        assert stored_content['success'] is True
        assert stored_content['error_message'] is None
        assert stored_content['payload'] == {"result": "success", "data": "response_data"}
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_send_error_response(self, mock_memory_action):
        """Test error response sending"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        
        mock_memory_action.return_value = {'success': True}
        
        broker = LTMCMessageBroker("error_response_conv")
        
        original_message = MCPMessage(
            message_id="error_original_789",
            sender_agent_id="error_requester",
            recipient_agent_id="error_handler",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.HIGH,
            message_type="error_test",
            payload={"request": "error_data"},
            conversation_id="error_response_conv",
            task_id="error_response_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Create error response
        error_response = MCPResponse(
            original_message=original_message,
            response_payload={"partial": "data"},
            success=False,
            error_message="Processing failed due to invalid input"
        )
        
        result = broker.send_response(error_response)
        
        assert result is True
        
        # Verify error response content
        memory_call = mock_memory_action.call_args
        stored_content = json.loads(memory_call[1]['content'])
        assert stored_content['success'] is False
        assert stored_content['error_message'] == "Processing failed due to invalid input"
        assert stored_content['payload'] == {"partial": "data"}
    
    def test_register_message_handler(self):
        """Test message handler registration"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        broker = LTMCMessageBroker("handler_test_conv")
        
        # Define test handler
        def test_handler(message):
            return {"handled": True, "message_id": message.message_id}
        
        # Register handler
        broker.register_message_handler("test_message_type", test_handler)
        
        # Verify handler registration
        assert "test_message_type" in broker.message_handlers
        assert broker.message_handlers["test_message_type"] == test_handler
        assert callable(broker.message_handlers["test_message_type"])
    
    def test_register_multiple_message_handlers(self):
        """Test registration of multiple message handlers"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        broker = LTMCMessageBroker("multi_handler_conv")
        
        # Define test handlers
        def coordination_handler(message):
            return {"type": "coordination", "handled": True}
        
        def workflow_handler(message):
            return {"type": "workflow", "handled": True}
        
        def broadcast_handler(message):
            return {"type": "broadcast", "handled": True}
        
        # Register multiple handlers
        broker.register_message_handler("coordination", coordination_handler)
        broker.register_message_handler("workflow_task", workflow_handler)
        broker.register_message_handler("broadcast", broadcast_handler)
        
        # Verify all handlers registered
        assert len(broker.message_handlers) == 3
        assert "coordination" in broker.message_handlers
        assert "workflow_task" in broker.message_handlers
        assert "broadcast" in broker.message_handlers
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_process_pending_messages_with_handlers(self, mock_memory_action):
        """Test processing pending messages with registered handlers"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import MCPResponse
        
        # Setup mock messages
        mock_documents = [
            {
                'id': 1,
                'content': json.dumps({
                    "mcp_message": True,
                    "message_id": "process_msg_1",
                    "sender": "process_sender",
                    "recipient": "process_agent",
                    "protocol": "request_response",
                    "priority": "normal",
                    "type": "processable_type",
                    "payload": {"process": "test_1"},
                    "timestamp": "2025-08-24T10:30:00Z",
                    "requires_ack": True,
                    "task_id": "process_test_task"
                })
            }
        ]
        
        # Mock for message retrieval, then for response sending
        mock_memory_action.side_effect = [
            {'success': True, 'documents': mock_documents},  # retrieve call
            {'success': True, 'doc_id': 789}  # store response call
        ]
        
        broker = LTMCMessageBroker("process_test_conv")
        
        # Register handler that returns a response
        def processable_handler(message):
            return MCPResponse(
                original_message=message,
                response_payload={"processed": True, "original_id": message.message_id},
                success=True
            )
        
        broker.register_message_handler("processable_type", processable_handler)
        
        # Process pending messages
        processed_count = broker.process_pending_messages("process_agent")
        
        assert processed_count == 1
        
        # Verify both retrieve and store calls were made
        assert mock_memory_action.call_count == 2
        
        # Verify retrieve call
        retrieve_call = mock_memory_action.call_args_list[0]
        assert retrieve_call[1]['action'] == 'retrieve'
        
        # Verify response store call
        store_call = mock_memory_action.call_args_list[1]
        assert store_call[1]['action'] == 'store'
        assert 'mcp_response_' in store_call[1]['file_name']
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_process_pending_messages_handler_error(self, mock_memory_action):
        """Test processing messages when handler raises exception"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        # Setup mock message
        mock_documents = [
            {
                'id': 1,
                'content': json.dumps({
                    "mcp_message": True,
                    "message_id": "error_msg_1",
                    "sender": "error_sender",
                    "recipient": "error_agent",
                    "protocol": "request_response",
                    "priority": "normal",
                    "type": "error_type",
                    "payload": {"error": "test"},
                    "timestamp": "2025-08-24T10:30:00Z",
                    "requires_ack": True,
                    "task_id": "error_test_task"
                })
            }
        ]
        
        # Mock for message retrieval, then for error response sending
        mock_memory_action.side_effect = [
            {'success': True, 'documents': mock_documents},
            {'success': True}  # Error response storage
        ]
        
        broker = LTMCMessageBroker("error_handler_conv")
        
        # Register handler that raises exception
        def error_handler(message):
            raise ValueError("Handler processing error")
        
        broker.register_message_handler("error_type", error_handler)
        
        # Process messages should handle error gracefully
        processed_count = broker.process_pending_messages("error_agent")
        
        assert processed_count == 1
        
        # Verify error response was sent
        assert mock_memory_action.call_count == 2
        error_response_call = mock_memory_action.call_args_list[1]
        stored_response = json.loads(error_response_call[1]['content'])
        assert stored_response['success'] is False
        assert "Handler processing error" in stored_response['error_message']
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    def test_process_pending_messages_no_handler(self, mock_memory_action):
        """Test processing messages with no registered handler"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        # Setup mock message
        mock_documents = [
            {
                'id': 1,
                'content': json.dumps({
                    "mcp_message": True,
                    "message_id": "no_handler_msg",
                    "sender": "no_handler_sender",
                    "recipient": "no_handler_agent",
                    "protocol": "coordination",
                    "priority": "normal",
                    "type": "unhandled_type",
                    "payload": {"no_handler": "test"},
                    "timestamp": "2025-08-24T10:30:00Z",
                    "task_id": "no_handler_test_task"
                })
            }
        ]
        
        mock_memory_action.return_value = {'success': True, 'documents': mock_documents}
        
        broker = LTMCMessageBroker("no_handler_conv")
        
        # Don't register any handlers
        processed_count = broker.process_pending_messages("no_handler_agent")
        
        # Message should be skipped (no handler)
        assert processed_count == 0
        
        # Only retrieve call should be made
        assert mock_memory_action.call_count == 1
        assert mock_memory_action.call_args[1]['action'] == 'retrieve'


class TestLTMCMessageBrokerIntegration:
    """Test LTMCMessageBroker integration scenarios"""
    
    @patch('ltms.coordination.mcp_message_broker.memory_action')
    @patch('ltms.coordination.mcp_message_broker.graph_action')
    def test_complete_message_workflow(self, mock_graph_action, mock_memory_action):
        """Test complete send-receive-respond workflow"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        
        # Setup mocks for all LTMC operations
        mock_memory_action.return_value = {'success': True, 'doc_id': 999}
        mock_graph_action.return_value = {'success': True}
        
        broker = LTMCMessageBroker("workflow_test_conv")
        
        # Step 1: Send message
        original_message = MCPMessage(
            message_id="workflow_msg_123",
            sender_agent_id="workflow_sender",
            recipient_agent_id="workflow_recipient",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.NORMAL,
            message_type="workflow_test",
            payload={"workflow": "test_data"},
            conversation_id="workflow_test_conv",
            task_id="workflow_test_task",
            timestamp=datetime.now(timezone.utc).isoformat(),
            requires_ack=True
        )
        
        send_result = broker.send_message(original_message)
        assert send_result is True
        
        # Step 2: Simulate message retrieval (prepare mock for receive)
        mock_memory_action.return_value = {
            'success': True,
            'documents': [
                {
                    'id': 999,
                    'content': json.dumps({
                        "mcp_message": True,
                        "message_id": "workflow_msg_123",
                        "sender": "workflow_sender",
                        "recipient": "workflow_recipient",
                        "protocol": "request_response",
                        "priority": "normal",
                        "type": "workflow_test",
                        "payload": {"workflow": "test_data"},
                        "timestamp": original_message.timestamp,
                        "requires_ack": True,
                        "task_id": "workflow_test_task"
                    })
                }
            ]
        }
        
        # Receive messages
        received_messages = broker.receive_messages("workflow_recipient")
        assert len(received_messages) == 1
        assert received_messages[0].message_id == "workflow_msg_123"
        
        # Step 3: Send response
        mock_memory_action.return_value = {'success': True}
        
        response = MCPResponse(
            original_message=received_messages[0],
            response_payload={"workflow": "completed", "result": "success"},
            success=True
        )
        
        response_result = broker.send_response(response)
        assert response_result is True
        
        # Verify all LTMC operations were called
        assert mock_memory_action.call_count >= 3  # send, receive, respond
        assert mock_graph_action.call_count >= 1  # graph relationship
    
    def test_message_broker_with_coordination_models_integration(self):
        """Test LTMCMessageBroker integration with all message model types"""
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import (
            MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        )
        
        broker = LTMCMessageBroker("integration_test_conv")
        
        # Test all protocol types work with broker
        protocols = [
            CommunicationProtocol.REQUEST_RESPONSE,
            CommunicationProtocol.PUBLISH_SUBSCRIBE,
            CommunicationProtocol.WORKFLOW_HANDOFF,
            CommunicationProtocol.BROADCAST,
            CommunicationProtocol.COORDINATION
        ]
        
        with patch('ltms.coordination.mcp_message_broker.memory_action') as mock_memory:
            with patch('ltms.coordination.mcp_message_broker.graph_action') as mock_graph:
                mock_memory.return_value = {'success': True}
                mock_graph.return_value = {'success': True}
                
                # Test sending messages with all protocol types
                for i, protocol in enumerate(protocols):
                    message = MCPMessage(
                        message_id=f"integration_msg_{i}",
                        sender_agent_id=f"integration_sender_{i}",
                        recipient_agent_id=f"integration_recipient_{i}" if protocol != CommunicationProtocol.BROADCAST else None,
                        protocol=protocol,
                        priority=MessagePriority.NORMAL,
                        message_type=f"integration_{protocol.value}",
                        payload={"integration": protocol.value, "test": i},
                        conversation_id="integration_test_conv",
                        task_id="integration_test_task",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
                    result = broker.send_message(message)
                    assert result is True
                
                # Verify all protocol types were processed
                assert mock_memory.call_count == len(protocols)
                assert mock_graph.call_count == len(protocols)


# Pytest fixtures for message broker testing
@pytest.fixture
def message_broker():
    """Fixture providing LTMCMessageBroker instance"""
    from ltms.coordination.mcp_message_broker import LTMCMessageBroker
    return LTMCMessageBroker("fixture_broker_conv")

@pytest.fixture
def sample_mcp_message():
    """Fixture providing sample MCPMessage for broker testing"""
    from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
    
    return MCPMessage(
        message_id="fixture_broker_msg",
        sender_agent_id="fixture_broker_sender",
        recipient_agent_id="fixture_broker_recipient",
        protocol=CommunicationProtocol.REQUEST_RESPONSE,
        priority=MessagePriority.NORMAL,
        message_type="fixture_broker_test",
        payload={"fixture": "broker_data"},
        conversation_id="fixture_broker_conv",
        task_id="fixture_broker_task",
        timestamp=datetime.now(timezone.utc).isoformat(),
        requires_ack=True
    )

@pytest.fixture
def mock_ltmc_tools():
    """Fixture providing mocked LTMC tools for broker testing"""
    with patch('ltms.coordination.mcp_message_broker.memory_action') as mock_memory:
        with patch('ltms.coordination.mcp_message_broker.graph_action') as mock_graph:
            mock_memory.return_value = {'success': True, 'doc_id': 777}
            mock_graph.return_value = {'success': True}
            
            yield {
                'memory_action': mock_memory,
                'graph_action': mock_graph
            }