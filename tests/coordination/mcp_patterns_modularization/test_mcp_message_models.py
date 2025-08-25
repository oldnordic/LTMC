"""
Comprehensive TDD tests for MCP Message Models extraction.
Tests all data structures, enums, and protocol interfaces.

Following TDD methodology: Tests written FIRST before extraction.
MCPMessage models will be extracted to provide clean data layer for MCP communication.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from unittest.mock import Mock


class TestCommunicationProtocol:
    """Test CommunicationProtocol enum - to be extracted from mcp_communication_patterns.py"""
    
    def test_communication_protocol_enum_values(self):
        """Test CommunicationProtocol enum has all required values"""
        from ltms.coordination.mcp_message_models import CommunicationProtocol
        
        # Test all protocol values exist
        assert hasattr(CommunicationProtocol, 'REQUEST_RESPONSE')
        assert hasattr(CommunicationProtocol, 'PUBLISH_SUBSCRIBE')
        assert hasattr(CommunicationProtocol, 'WORKFLOW_HANDOFF')
        assert hasattr(CommunicationProtocol, 'BROADCAST')
        assert hasattr(CommunicationProtocol, 'COORDINATION')
        
        # Test enum values
        assert CommunicationProtocol.REQUEST_RESPONSE.value == "request_response"
        assert CommunicationProtocol.PUBLISH_SUBSCRIBE.value == "publish_subscribe"
        assert CommunicationProtocol.WORKFLOW_HANDOFF.value == "workflow_handoff"
        assert CommunicationProtocol.BROADCAST.value == "broadcast"
        assert CommunicationProtocol.COORDINATION.value == "coordination"
    
    def test_communication_protocol_enum_serialization(self):
        """Test CommunicationProtocol enum serialization"""
        from ltms.coordination.mcp_message_models import CommunicationProtocol
        
        # Test enum serialization
        protocol = CommunicationProtocol.REQUEST_RESPONSE
        assert protocol.value == "request_response"
        
        # Test enum deserialization
        reconstructed = CommunicationProtocol("request_response")
        assert reconstructed == CommunicationProtocol.REQUEST_RESPONSE
    
    def test_communication_protocol_enum_iteration(self):
        """Test CommunicationProtocol enum can be iterated"""
        from ltms.coordination.mcp_message_models import CommunicationProtocol
        
        protocols = list(CommunicationProtocol)
        assert len(protocols) == 5
        assert CommunicationProtocol.REQUEST_RESPONSE in protocols
        assert CommunicationProtocol.BROADCAST in protocols


class TestMessagePriority:
    """Test MessagePriority enum - to be extracted from mcp_communication_patterns.py"""
    
    def test_message_priority_enum_values(self):
        """Test MessagePriority enum has all required priority levels"""
        from ltms.coordination.mcp_message_models import MessagePriority
        
        # Test all priority values exist
        assert hasattr(MessagePriority, 'CRITICAL')
        assert hasattr(MessagePriority, 'HIGH')
        assert hasattr(MessagePriority, 'NORMAL')
        assert hasattr(MessagePriority, 'LOW')
        
        # Test enum values
        assert MessagePriority.CRITICAL.value == "critical"
        assert MessagePriority.HIGH.value == "high"
        assert MessagePriority.NORMAL.value == "normal"
        assert MessagePriority.LOW.value == "low"
    
    def test_message_priority_ordering(self):
        """Test MessagePriority can be used for ordering (if implemented)"""
        from ltms.coordination.mcp_message_models import MessagePriority
        
        # Test all priority levels exist and can be compared
        priorities = [MessagePriority.LOW, MessagePriority.NORMAL, MessagePriority.HIGH, MessagePriority.CRITICAL]
        assert len(priorities) == 4
        
        # Test enum values are distinct
        assert MessagePriority.CRITICAL != MessagePriority.HIGH
        assert MessagePriority.HIGH != MessagePriority.NORMAL
        assert MessagePriority.NORMAL != MessagePriority.LOW
    
    def test_message_priority_serialization(self):
        """Test MessagePriority enum serialization/deserialization"""
        from ltms.coordination.mcp_message_models import MessagePriority
        
        # Test serialization
        priority = MessagePriority.HIGH
        assert priority.value == "high"
        
        # Test deserialization
        reconstructed = MessagePriority("high")
        assert reconstructed == MessagePriority.HIGH


class TestMCPMessage:
    """Test MCPMessage dataclass - to be extracted from mcp_communication_patterns.py"""
    
    def test_mcp_message_creation(self):
        """Test MCPMessage can be created with all required fields"""
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        message = MCPMessage(
            message_id="test_msg_123",
            sender_agent_id="test_sender",
            recipient_agent_id="test_recipient",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.NORMAL,
            message_type="test_message",
            payload={"test": "data"},
            conversation_id="test_conversation",
            task_id="test_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Verify all fields are set correctly
        assert message.message_id == "test_msg_123"
        assert message.sender_agent_id == "test_sender"
        assert message.recipient_agent_id == "test_recipient"
        assert message.protocol == CommunicationProtocol.REQUEST_RESPONSE
        assert message.priority == MessagePriority.NORMAL
        assert message.message_type == "test_message"
        assert message.payload == {"test": "data"}
        assert message.conversation_id == "test_conversation"
        assert message.task_id == "test_task"
        assert message.timestamp is not None
    
    def test_mcp_message_optional_fields(self):
        """Test MCPMessage with optional fields"""
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        message = MCPMessage(
            message_id="test_msg_456",
            sender_agent_id="test_sender",
            recipient_agent_id="test_recipient",
            protocol=CommunicationProtocol.COORDINATION,
            priority=MessagePriority.HIGH,
            message_type="coordination_test",
            payload={"coordination": "data"},
            conversation_id="test_conversation",
            task_id="test_task",
            timestamp=datetime.now(timezone.utc).isoformat(),
            expires_at="2025-08-25T12:00:00Z",
            requires_ack=True,
            correlation_id="test_correlation_789"
        )
        
        # Verify optional fields
        assert message.expires_at == "2025-08-25T12:00:00Z"
        assert message.requires_ack is True
        assert message.correlation_id == "test_correlation_789"
    
    def test_mcp_message_broadcast(self):
        """Test MCPMessage for broadcast (no specific recipient)"""
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        broadcast_message = MCPMessage(
            message_id="broadcast_msg_789",
            sender_agent_id="broadcast_sender",
            recipient_agent_id=None,  # Broadcast
            protocol=CommunicationProtocol.BROADCAST,
            priority=MessagePriority.NORMAL,
            message_type="broadcast_announcement",
            payload={"announcement": "broadcast_data"},
            conversation_id="broadcast_conversation",
            task_id="broadcast_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        assert broadcast_message.recipient_agent_id is None
        assert broadcast_message.protocol == CommunicationProtocol.BROADCAST
    
    def test_mcp_message_serialization(self):
        """Test MCPMessage can be serialized to dict/JSON"""
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        message = MCPMessage(
            message_id="serial_test_123",
            sender_agent_id="serial_sender",
            recipient_agent_id="serial_recipient",
            protocol=CommunicationProtocol.WORKFLOW_HANDOFF,
            priority=MessagePriority.CRITICAL,
            message_type="serialization_test",
            payload={"serialization": "test_data", "nested": {"key": "value"}},
            conversation_id="serial_conversation",
            task_id="serial_task",
            timestamp="2025-08-24T10:30:00Z",
            requires_ack=True
        )
        
        # Test dataclass to dict conversion
        message_dict = asdict(message)
        assert isinstance(message_dict, dict)
        assert message_dict['message_id'] == "serial_test_123"
        assert message_dict['protocol'] == CommunicationProtocol.WORKFLOW_HANDOFF
        assert message_dict['priority'] == MessagePriority.CRITICAL
        
        # Test JSON serialization (enums need special handling)
        message_for_json = asdict(message)
        message_for_json['protocol'] = message.protocol.value
        message_for_json['priority'] = message.priority.value
        
        json_str = json.dumps(message_for_json)
        assert "serial_test_123" in json_str
        assert "workflow_handoff" in json_str
        assert "critical" in json_str
    
    def test_mcp_message_deserialization(self):
        """Test MCPMessage can be reconstructed from dict"""
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        message_data = {
            "message_id": "deserial_test_456",
            "sender_agent_id": "deserial_sender",
            "recipient_agent_id": "deserial_recipient",
            "protocol": "publish_subscribe",
            "priority": "low",
            "message_type": "deserialization_test",
            "payload": {"deserial": "test_data"},
            "conversation_id": "deserial_conversation",
            "task_id": "deserial_task",
            "timestamp": "2025-08-24T11:00:00Z",
            "expires_at": None,
            "requires_ack": False,
            "correlation_id": None
        }
        
        # Reconstruct MCPMessage from dict
        message = MCPMessage(
            message_id=message_data["message_id"],
            sender_agent_id=message_data["sender_agent_id"],
            recipient_agent_id=message_data["recipient_agent_id"],
            protocol=CommunicationProtocol(message_data["protocol"]),
            priority=MessagePriority(message_data["priority"]),
            message_type=message_data["message_type"],
            payload=message_data["payload"],
            conversation_id=message_data["conversation_id"],
            task_id=message_data["task_id"],
            timestamp=message_data["timestamp"],
            expires_at=message_data["expires_at"],
            requires_ack=message_data["requires_ack"],
            correlation_id=message_data["correlation_id"]
        )
        
        assert message.message_id == "deserial_test_456"
        assert message.protocol == CommunicationProtocol.PUBLISH_SUBSCRIBE
        assert message.priority == MessagePriority.LOW
        assert message.requires_ack is False
    
    def test_mcp_message_validation(self):
        """Test MCPMessage field validation"""
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        # Test with valid data
        valid_message = MCPMessage(
            message_id="validation_test",
            sender_agent_id="valid_sender",
            recipient_agent_id="valid_recipient",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.NORMAL,
            message_type="validation_test",
            payload={"valid": True},
            conversation_id="valid_conversation",
            task_id="valid_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        assert valid_message.message_id == "validation_test"
        assert isinstance(valid_message.payload, dict)
        
        # Test message type validation (string)
        assert isinstance(valid_message.message_type, str)
        assert len(valid_message.message_type) > 0


class TestMCPResponse:
    """Test MCPResponse class - to be extracted from mcp_communication_patterns.py"""
    
    def test_mcp_response_creation_success(self):
        """Test MCPResponse creation for successful response"""
        from ltms.coordination.mcp_message_models import MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        
        # Create original message
        original_message = MCPMessage(
            message_id="original_msg_123",
            sender_agent_id="request_sender",
            recipient_agent_id="request_handler",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.NORMAL,
            message_type="test_request",
            payload={"request": "data"},
            conversation_id="response_conversation",
            task_id="response_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Create successful response
        response = MCPResponse(
            original_message=original_message,
            response_payload={"result": "success", "data": "response_data"},
            success=True
        )
        
        # Verify response fields
        assert response.original_message_id == "original_msg_123"
        assert response.sender_agent_id == "request_handler"  # Swapped
        assert response.recipient_agent_id == "request_sender"  # Swapped
        assert response.response_payload == {"result": "success", "data": "response_data"}
        assert response.success is True
        assert response.error_message is None
        assert response.conversation_id == "response_conversation"
        assert response.task_id == "response_task"
        assert response.timestamp is not None
        assert response.response_id is not None
    
    def test_mcp_response_creation_error(self):
        """Test MCPResponse creation for error response"""
        from ltms.coordination.mcp_message_models import MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        
        original_message = MCPMessage(
            message_id="error_msg_456",
            sender_agent_id="error_requester",
            recipient_agent_id="error_handler",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.HIGH,
            message_type="error_request",
            payload={"request": "error_data"},
            conversation_id="error_conversation",
            task_id="error_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Create error response
        response = MCPResponse(
            original_message=original_message,
            response_payload={"partial_result": "available"},
            success=False,
            error_message="Processing failed due to invalid input"
        )
        
        # Verify error response fields
        assert response.success is False
        assert response.error_message == "Processing failed due to invalid input"
        assert response.response_payload == {"partial_result": "available"}
        assert response.original_message_id == "error_msg_456"
    
    def test_mcp_response_agent_swapping(self):
        """Test MCPResponse correctly swaps sender/recipient from original message"""
        from ltms.coordination.mcp_message_models import MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        
        original = MCPMessage(
            message_id="swap_test_789",
            sender_agent_id="agent_alpha",
            recipient_agent_id="agent_beta",
            protocol=CommunicationProtocol.COORDINATION,
            priority=MessagePriority.LOW,
            message_type="swap_test",
            payload={"test": "swapping"},
            conversation_id="swap_conversation",
            task_id="swap_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        response = MCPResponse(
            original_message=original,
            response_payload={"swap": "confirmed"}
        )
        
        # Verify agent IDs are swapped
        assert response.sender_agent_id == "agent_beta"  # Was recipient
        assert response.recipient_agent_id == "agent_alpha"  # Was sender
        assert response.conversation_id == "swap_conversation"
        assert response.task_id == "swap_task"
    
    def test_mcp_response_unique_ids(self):
        """Test MCPResponse generates unique response IDs"""
        from ltms.coordination.mcp_message_models import MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        
        original = MCPMessage(
            message_id="unique_test_101",
            sender_agent_id="unique_sender",
            recipient_agent_id="unique_recipient",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.NORMAL,
            message_type="unique_test",
            payload={"unique": "test"},
            conversation_id="unique_conversation",
            task_id="unique_task",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Create multiple responses
        response1 = MCPResponse(original, {"response": 1})
        response2 = MCPResponse(original, {"response": 2})
        response3 = MCPResponse(original, {"response": 3})
        
        # Verify unique response IDs
        assert response1.response_id != response2.response_id
        assert response2.response_id != response3.response_id
        assert response1.response_id != response3.response_id
        
        # Verify all reference same original
        assert response1.original_message_id == "unique_test_101"
        assert response2.original_message_id == "unique_test_101"
        assert response3.original_message_id == "unique_test_101"


class TestAgentCommunicationInterface:
    """Test AgentCommunicationInterface protocol - to be extracted from mcp_communication_patterns.py"""
    
    def test_agent_communication_protocol_definition(self):
        """Test AgentCommunicationInterface protocol is properly defined"""
        from ltms.coordination.mcp_message_models import AgentCommunicationInterface
        
        # Test protocol has required methods
        assert hasattr(AgentCommunicationInterface, 'send_message')
        assert hasattr(AgentCommunicationInterface, 'receive_messages')
        assert hasattr(AgentCommunicationInterface, 'send_response')
        
        # Note: Protocol methods are abstract, so we can't test implementation
        # We'll test actual implementations in the broker tests
    
    def test_agent_communication_protocol_compliance(self):
        """Test that a mock implementation can satisfy the protocol"""
        from ltms.coordination.mcp_message_models import AgentCommunicationInterface, MCPMessage, MCPResponse
        
        class MockAgentCommunication:
            def send_message(self, message: MCPMessage) -> bool:
                return True
            
            def receive_messages(self, since: Optional[str] = None) -> List[MCPMessage]:
                return []
            
            def send_response(self, response: MCPResponse) -> bool:
                return True
        
        # Test mock implementation
        mock_comm = MockAgentCommunication()
        
        # Test interface methods exist and work
        assert hasattr(mock_comm, 'send_message')
        assert hasattr(mock_comm, 'receive_messages')
        assert hasattr(mock_comm, 'send_response')
        
        # Test method signatures (basic test)
        assert callable(mock_comm.send_message)
        assert callable(mock_comm.receive_messages)
        assert callable(mock_comm.send_response)


class TestMCPMessageModelsIntegration:
    """Test integration between all MCP message model components"""
    
    def test_complete_message_response_cycle(self):
        """Test complete message-response cycle using all model components"""
        from ltms.coordination.mcp_message_models import (
            MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority
        )
        
        # Create request message
        request = MCPMessage(
            message_id="integration_request_123",
            sender_agent_id="integration_requester",
            recipient_agent_id="integration_handler",
            protocol=CommunicationProtocol.REQUEST_RESPONSE,
            priority=MessagePriority.HIGH,
            message_type="integration_test",
            payload={"integration": "test_request", "data": [1, 2, 3]},
            conversation_id="integration_conversation",
            task_id="integration_task",
            timestamp=datetime.now(timezone.utc).isoformat(),
            requires_ack=True,
            correlation_id="integration_correlation_456"
        )
        
        # Create successful response
        response = MCPResponse(
            original_message=request,
            response_payload={"integration": "test_response", "result": "success", "processed": [2, 4, 6]},
            success=True
        )
        
        # Verify complete cycle
        assert request.message_id == "integration_request_123"
        assert response.original_message_id == request.message_id
        assert request.requires_ack is True
        assert request.correlation_id == "integration_correlation_456"
        
        # Verify agent swapping in response
        assert request.sender_agent_id == response.recipient_agent_id
        assert request.recipient_agent_id == response.sender_agent_id
        
        # Verify conversation/task context preserved
        assert request.conversation_id == response.conversation_id
        assert request.task_id == response.task_id
    
    def test_all_protocol_types(self):
        """Test all communication protocol types can be used"""
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        protocols = [
            CommunicationProtocol.REQUEST_RESPONSE,
            CommunicationProtocol.PUBLISH_SUBSCRIBE,
            CommunicationProtocol.WORKFLOW_HANDOFF,
            CommunicationProtocol.BROADCAST,
            CommunicationProtocol.COORDINATION
        ]
        
        messages = []
        for i, protocol in enumerate(protocols):
            message = MCPMessage(
                message_id=f"protocol_test_{i}",
                sender_agent_id=f"sender_{i}",
                recipient_agent_id=f"recipient_{i}" if protocol != CommunicationProtocol.BROADCAST else None,
                protocol=protocol,
                priority=MessagePriority.NORMAL,
                message_type=f"protocol_{protocol.value}_test",
                payload={"protocol": protocol.value, "test": i},
                conversation_id="protocol_test_conversation",
                task_id="protocol_test_task",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            messages.append(message)
        
        # Verify all protocol types work
        assert len(messages) == 5
        assert all(msg.protocol in protocols for msg in messages)
        
        # Verify broadcast message has no recipient
        broadcast_msg = next(msg for msg in messages if msg.protocol == CommunicationProtocol.BROADCAST)
        assert broadcast_msg.recipient_agent_id is None
    
    def test_all_priority_levels(self):
        """Test all message priority levels can be used"""
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        priorities = [
            MessagePriority.LOW,
            MessagePriority.NORMAL,
            MessagePriority.HIGH,
            MessagePriority.CRITICAL
        ]
        
        messages = []
        for i, priority in enumerate(priorities):
            message = MCPMessage(
                message_id=f"priority_test_{i}",
                sender_agent_id=f"priority_sender_{i}",
                recipient_agent_id=f"priority_recipient_{i}",
                protocol=CommunicationProtocol.COORDINATION,
                priority=priority,
                message_type=f"priority_{priority.value}_test",
                payload={"priority": priority.value, "test": i},
                conversation_id="priority_test_conversation",
                task_id="priority_test_task",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            messages.append(message)
        
        # Verify all priority levels work
        assert len(messages) == 4
        assert all(msg.priority in priorities for msg in messages)
        
        # Test priorities are distinct
        priority_values = [msg.priority.value for msg in messages]
        assert len(set(priority_values)) == 4  # All unique


# Pytest fixtures for MCP message model testing
@pytest.fixture
def sample_mcp_message():
    """Fixture providing sample MCPMessage for testing"""
    from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
    
    return MCPMessage(
        message_id="fixture_msg_123",
        sender_agent_id="fixture_sender",
        recipient_agent_id="fixture_recipient",
        protocol=CommunicationProtocol.REQUEST_RESPONSE,
        priority=MessagePriority.NORMAL,
        message_type="fixture_test",
        payload={"fixture": "test_data"},
        conversation_id="fixture_conversation",
        task_id="fixture_task",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@pytest.fixture
def sample_mcp_response(sample_mcp_message):
    """Fixture providing sample MCPResponse for testing"""
    from ltms.coordination.mcp_message_models import MCPResponse
    
    return MCPResponse(
        original_message=sample_mcp_message,
        response_payload={"fixture": "response_data"},
        success=True
    )

@pytest.fixture
def all_communication_protocols():
    """Fixture providing all CommunicationProtocol values"""
    from ltms.coordination.mcp_message_models import CommunicationProtocol
    
    return [
        CommunicationProtocol.REQUEST_RESPONSE,
        CommunicationProtocol.PUBLISH_SUBSCRIBE,
        CommunicationProtocol.WORKFLOW_HANDOFF,
        CommunicationProtocol.BROADCAST,
        CommunicationProtocol.COORDINATION
    ]

@pytest.fixture
def all_message_priorities():
    """Fixture providing all MessagePriority values"""
    from ltms.coordination.mcp_message_models import MessagePriority
    
    return [
        MessagePriority.LOW,
        MessagePriority.NORMAL,
        MessagePriority.HIGH,
        MessagePriority.CRITICAL
    ]