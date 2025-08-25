"""
LTMC MCP Message Broker
LTMC-based message broker for inter-agent communication with persistence.

Extracted from mcp_communication_patterns.py for smart modularization (300-line limit compliance).
Handles message sending, retrieval, and LTMC storage integration for agent communication.

Components:
- LTMCMessageBroker: Complete message broker with LTMC integration
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Callable

# Import message models
from .mcp_message_models import MCPMessage, MCPResponse, CommunicationProtocol, MessagePriority

# LTMC MCP tool imports for real functionality
from ltms.tools.consolidated import memory_action, graph_action


class LTMCMessageBroker:
    """
    LTMC-based message broker for inter-agent communication.
    Uses LTMC MCP tools for persistent, reliable messaging.
    """
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.message_handlers: Dict[str, Callable[[MCPMessage], Optional[MCPResponse]]] = {}
    
    def send_message(self, message: MCPMessage) -> bool:
        """
        Send message using LTMC memory system for persistence.
        
        Args:
            message: MCPMessage to send
            
        Returns:
            bool: True if message sent successfully
        """
        try:
            # Store message in LTMC memory
            message_doc = {
                "mcp_message": True,
                "message_id": message.message_id,
                "sender": message.sender_agent_id,
                "recipient": message.recipient_agent_id,
                "protocol": message.protocol.value,
                "priority": message.priority.value,
                "type": message.message_type,
                "payload": message.payload,
                "timestamp": message.timestamp,
                "expires_at": message.expires_at,
                "requires_ack": message.requires_ack,
                "correlation_id": message.correlation_id,
                "task_id": message.task_id
            }
            
            # Determine storage tags
            tags = [
                "mcp_message",
                message.sender_agent_id,
                message.protocol.value,
                message.priority.value,
                message.task_id
            ]
            
            if message.recipient_agent_id:
                tags.append(message.recipient_agent_id)
            
            # Store in LTMC
            result = memory_action(
                action="store",
                file_name=f"mcp_message_{message.message_id}.json",
                content=json.dumps(message_doc, indent=2),
                tags=tags,
                conversation_id=self.conversation_id,
                role="system"
            )
            
            if result.get('success'):
                # Create graph relationship for message flow
                graph_action(
                    action="link",
                    source_entity=f"agent_{message.sender_agent_id}",
                    target_entity=f"agent_{message.recipient_agent_id}" if message.recipient_agent_id else "broadcast",
                    relationship="sends_message_to",
                    properties={
                        "message_id": message.message_id,
                        "protocol": message.protocol.value,
                        "timestamp": message.timestamp
                    }
                )
                
                print(f"✅ MCP message sent: {message.sender_agent_id} → {message.recipient_agent_id or 'broadcast'}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to send MCP message: {e}")
            return False
    
    def receive_messages(self, agent_id: str, since: Optional[str] = None) -> List[MCPMessage]:
        """
        Receive messages for an agent from LTMC memory.
        
        Args:
            agent_id: Agent ID to retrieve messages for
            since: Optional timestamp to filter messages since
            
        Returns:
            List[MCPMessage]: Messages for the agent
        """
        try:
            # Query LTMC for messages to this agent
            result = memory_action(
                action="retrieve", 
                query=f"mcp_message recipient:{agent_id}",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            messages = []
            if result.get('success') and result.get('documents'):
                for doc in result['documents']:
                    try:
                        # Parse message content
                        content = doc.get('content', '')
                        if content:
                            message_data = json.loads(content)
                            
                            # Filter by timestamp if provided
                            if since:
                                msg_time = message_data.get('timestamp', '')
                                if msg_time <= since:
                                    continue
                            
                            # Reconstruct MCPMessage
                            message = MCPMessage(
                                message_id=message_data['message_id'],
                                sender_agent_id=message_data['sender'],
                                recipient_agent_id=message_data.get('recipient'),
                                protocol=CommunicationProtocol(message_data['protocol']),
                                priority=MessagePriority(message_data['priority']),
                                message_type=message_data['type'],
                                payload=message_data['payload'],
                                conversation_id=self.conversation_id,
                                task_id=message_data['task_id'],
                                timestamp=message_data['timestamp'],
                                expires_at=message_data.get('expires_at'),
                                requires_ack=message_data.get('requires_ack', False),
                                correlation_id=message_data.get('correlation_id')
                            )
                            
                            messages.append(message)
                            
                    except Exception as parse_error:
                        print(f"⚠️ Failed to parse message: {parse_error}")
                        continue
            
            return messages
            
        except Exception as e:
            print(f"❌ Failed to receive messages for {agent_id}: {e}")
            return []
    
    def send_response(self, response: MCPResponse) -> bool:
        """
        Send response to a received message.
        
        Args:
            response: MCPResponse to send
            
        Returns:
            bool: True if response sent successfully
        """
        try:
            # Store response in LTMC
            response_doc = {
                "mcp_response": True,
                "response_id": response.response_id,
                "original_message_id": response.original_message_id,
                "sender": response.sender_agent_id,
                "recipient": response.recipient_agent_id,
                "success": response.success,
                "error_message": response.error_message,
                "payload": response.response_payload,
                "timestamp": response.timestamp,
                "task_id": response.task_id
            }
            
            result = memory_action(
                action="store",
                file_name=f"mcp_response_{response.response_id}.json",
                content=json.dumps(response_doc, indent=2),
                tags=[
                    "mcp_response",
                    response.sender_agent_id,
                    response.recipient_agent_id,
                    response.task_id
                ],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            if result.get('success'):
                print(f"✅ MCP response sent: {response.sender_agent_id} → {response.recipient_agent_id}")
                return True
                
            return False
            
        except Exception as e:
            print(f"❌ Failed to send MCP response: {e}")
            return False

    def register_message_handler(self, 
                                message_type: str, 
                                handler: Callable[[MCPMessage], Optional[MCPResponse]]) -> None:
        """
        Register handler for specific message types.
        
        Args:
            message_type: Type of message to handle
            handler: Function to handle the message
        """
        self.message_handlers[message_type] = handler
        print(f"✅ Message handler registered for type: {message_type}")
    
    def process_pending_messages(self, agent_id: str) -> int:
        """
        Process all pending messages for an agent.
        
        Args:
            agent_id: Agent ID to process messages for
            
        Returns:
            int: Number of messages processed
        """
        try:
            messages = self.receive_messages(agent_id)
            processed = 0
            
            for message in messages:
                if message.message_type in self.message_handlers:
                    try:
                        handler = self.message_handlers[message.message_type]
                        response = handler(message)
                        
                        if response and message.requires_ack:
                            self.send_response(response)
                        
                        processed += 1
                        
                    except Exception as handler_error:
                        print(f"⚠️ Message handler error: {handler_error}")
                        
                        if message.requires_ack:
                            error_response = MCPResponse(
                                original_message=message,
                                response_payload={},
                                success=False,
                                error_message=str(handler_error)
                            )
                            self.send_response(error_response)
            
            return processed
            
        except Exception as e:
            print(f"❌ Failed to process pending messages: {e}")
            return 0