"""
MCP Message Models for LTMC Agent Coordination
Pure data structures and enums for MCP-based inter-agent communication.

Extracted from mcp_communication_patterns.py for smart modularization (300-line limit compliance).
Provides clean data layer with no LTMC dependencies for maximum reusability.

Components:
- CommunicationProtocol: Standard communication protocols for agent interaction
- MessagePriority: Message priority levels 
- MCPMessage: Standard MCP message format dataclass
- MCPResponse: Standard MCP response format class
- AgentCommunicationInterface: Protocol interface for agent communication
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class CommunicationProtocol(Enum):
    """Standard communication protocols for agent interaction"""
    REQUEST_RESPONSE = "request_response"
    PUBLISH_SUBSCRIBE = "publish_subscribe"  
    WORKFLOW_HANDOFF = "workflow_handoff"
    BROADCAST = "broadcast"
    COORDINATION = "coordination"


class MessagePriority(Enum):
    """Message priority levels"""
    CRITICAL = "critical"
    HIGH = "high" 
    NORMAL = "normal"
    LOW = "low"


@dataclass
class MCPMessage:
    """Standard MCP message format for inter-agent communication"""
    message_id: str
    sender_agent_id: str
    recipient_agent_id: Optional[str] 
    protocol: CommunicationProtocol
    priority: MessagePriority
    message_type: str
    payload: Dict[str, Any]
    conversation_id: str
    task_id: str
    timestamp: str
    expires_at: Optional[str] = None
    requires_ack: bool = False
    correlation_id: Optional[str] = None


class MCPResponse:
    """Standard MCP response format"""
    def __init__(self, 
                 original_message: MCPMessage,
                 response_payload: Dict[str, Any],
                 success: bool = True,
                 error_message: Optional[str] = None):
        self.response_id = str(uuid.uuid4())
        self.original_message_id = original_message.message_id
        self.sender_agent_id = original_message.recipient_agent_id
        self.recipient_agent_id = original_message.sender_agent_id
        self.response_payload = response_payload
        self.success = success
        self.error_message = error_message
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.conversation_id = original_message.conversation_id
        self.task_id = original_message.task_id


class AgentCommunicationInterface(Protocol):
    """Protocol interface for agent communication"""
    
    def send_message(self, message: MCPMessage) -> bool:
        """Send message to another agent"""
        ...
    
    def receive_messages(self, since: Optional[str] = None) -> List[MCPMessage]:
        """Receive pending messages"""
        ...
    
    def send_response(self, response: MCPResponse) -> bool:
        """Send response to a received message"""
        ...