"""
LTMC Agent Message Handler
Inter-agent message communication for coordination framework.

Extracted from agent_coordination_framework.py for smart modularization (300-line limit compliance).
Handles message sending, retrieval, and LTMC storage integration for agent communication.

Components:
- AgentMessageHandler: Complete inter-agent message communication management
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set

# Import coordination models
from .agent_coordination_models import AgentMessage

# LTMC MCP tool imports for real functionality
from ltms.tools.memory.memory_actions import memory_action


class AgentMessageHandler:
    """Inter-agent message communication handler for coordination framework."""
    
    def __init__(self, task_id: str, conversation_id: str):
        """Initialize agent message handler."""
        self.task_id = task_id
        self.conversation_id = conversation_id
    
    def send_agent_message(self, message: AgentMessage, registered_agents: Set[str]) -> bool:
        """Send message between agents using LTMC communication."""
        try:
            # Validate sender is registered
            if message.sender_agent not in registered_agents:
                raise ValueError(f"Sender agent {message.sender_agent} not registered")
            
            # Store message in LTMC
            message_doc = {
                "message_type": "inter_agent_communication",
                "sender": message.sender_agent,
                "recipient": message.recipient_agent,
                "content": message.content,
                "timestamp": message.timestamp,
                "requires_response": message.requires_response
            }
            
            memory_action(
                action="store", 
                file_name=f"agent_message_{message.sender_agent}_to_{message.recipient_agent or 'broadcast'}_{int(time.time())}.md",
                content=f"# Agent Message: {message.sender_agent} → {message.recipient_agent or 'broadcast'}\n\n{json.dumps(message_doc, indent=2)}",
                tags=["agent_communication", message.sender_agent, message.recipient_agent or "broadcast", self.task_id],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            print(f"✅ Message sent from {message.sender_agent} to {message.recipient_agent or 'broadcast'}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send agent message: {e}")
            return False
    
    def retrieve_agent_messages(self, agent_id: str, since_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve messages for a specific agent using LTMC."""
        try:
            # Query LTMC memory for messages to this agent
            result = memory_action(
                action="retrieve",
                query=f"agent communication {agent_id}",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            if result.get('success') and result.get('documents'):
                messages = []
                for doc in result['documents']:
                    try:
                        # Parse message content
                        content = doc.get('content', '')
                        if f"→ {agent_id}" in content:
                            messages.append({
                                'document': doc,
                                'parsed_content': content
                            })
                    except Exception as parse_error:
                        print(f"⚠️ Failed to parse message document: {parse_error}")
                        continue
                
                return messages
            
            return []
            
        except Exception as e:
            print(f"❌ Failed to retrieve messages for {agent_id}: {e}")
            return []
    
    def get_agent_message_count(self, agent_id: str) -> int:
        """Get count of messages for a specific agent."""
        try:
            messages = self.retrieve_agent_messages(agent_id)
            return len(messages)
        except Exception as e:
            print(f"❌ Failed to get message count for {agent_id}: {e}")
            return 0
    
    def get_conversation_messages(self, sender_id: str, recipient_id: str) -> List[Dict[str, Any]]:
        """Get messages between two specific agents."""
        try:
            # Query for messages from sender to recipient
            result = memory_action(
                action="retrieve",
                query=f"agent communication {sender_id} {recipient_id}",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            if result.get('success') and result.get('documents'):
                conversation_messages = []
                for doc in result['documents']:
                    try:
                        content = doc.get('content', '')
                        if f"{sender_id} → {recipient_id}" in content:
                            conversation_messages.append({
                                'document': doc,
                                'parsed_content': content
                            })
                    except Exception as parse_error:
                        print(f"⚠️ Failed to parse conversation message: {parse_error}")
                        continue
                
                return conversation_messages
            
            return []
            
        except Exception as e:
            print(f"❌ Failed to retrieve conversation messages: {e}")
            return []
    
    def get_broadcast_messages(self) -> List[Dict[str, Any]]:
        """Get all broadcast messages in the conversation."""
        try:
            # Dynamic Method Architecture Principles - Generate query based on conversation context
            broadcast_search_query = f"agent communication broadcast messages for conversation {self.conversation_id}"
            result = memory_action(
                action="retrieve", 
                query=broadcast_search_query,
                conversation_id=self.conversation_id,
                role="system"
            )
            
            if result.get('success') and result.get('documents'):
                broadcast_messages = []
                for doc in result['documents']:
                    try:
                        content = doc.get('content', '')
                        if "→ broadcast" in content:
                            broadcast_messages.append({
                                'document': doc,
                                'parsed_content': content
                            })
                    except Exception as parse_error:
                        print(f"⚠️ Failed to parse broadcast message: {parse_error}")
                        continue
                
                return broadcast_messages
            
            return []
            
        except Exception as e:
            print(f"❌ Failed to retrieve broadcast messages: {e}")
            return []
    
    def get_message_statistics(self) -> Dict[str, Any]:
        """Get comprehensive message handling statistics."""
        try:
            # Dynamic Method Architecture Principles - Generate query based on task and conversation context
            statistics_search_query = f"agent communication statistics for task {self.task_id} conversation {self.conversation_id}"
            result = memory_action(
                action="retrieve",
                query=statistics_search_query,
                conversation_id=self.conversation_id,
                role="system"
            )
            
            stats = {
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "total_messages": 0,
                "broadcast_messages": 0,
                "point_to_point_messages": 0,
                "unique_senders": set(),
                "unique_recipients": set(),
                "message_types": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if result.get('success') and result.get('documents'):
                for doc in result['documents']:
                    try:
                        content = doc.get('content', '')
                        
                        # Count total messages
                        if "Agent Message:" in content:
                            stats["total_messages"] += 1
                            
                            # Classify message type
                            if "→ broadcast" in content:
                                stats["broadcast_messages"] += 1
                            else:
                                stats["point_to_point_messages"] += 1
                            
                            # Extract sender/recipient info
                            if ":" in content and "→" in content:
                                try:
                                    header_line = [line for line in content.split('\n') if 'Agent Message:' in line][0]
                                    message_info = header_line.split('Agent Message:')[1].strip()
                                    if '→' in message_info:
                                        sender, recipient = message_info.split('→', 1)
                                        sender = sender.strip()
                                        recipient = recipient.strip()
                                        
                                        stats["unique_senders"].add(sender)
                                        if recipient != "broadcast":
                                            stats["unique_recipients"].add(recipient)
                                
                                except Exception:
                                    continue  # Skip parsing errors
                    
                    except Exception as parse_error:
                        continue  # Skip document parsing errors
            
            # Convert sets to lists for JSON serialization
            stats["unique_senders"] = list(stats["unique_senders"])
            stats["unique_recipients"] = list(stats["unique_recipients"])
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get message statistics: {e}")
            return {
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }