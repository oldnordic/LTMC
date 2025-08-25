"""
MCP Communication Factory Functions
Factory functions and public API for common MCP communication patterns.

Extracted from mcp_communication_patterns.py for smart modularization (300-line limit compliance).
Provides clean public API and factory functions for creating standardized MCP messages.

Components:
- create_request_response_message: Factory for request-response pattern messages
- create_broadcast_message: Factory for broadcast pattern messages  
- Demonstration and example usage functions
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Import message models
from .mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority

# Import integrated components for public API
from .mcp_message_broker import LTMCMessageBroker
from .mcp_workflow_orchestrator import WorkflowOrchestrator


# Factory functions for common communication patterns
def create_request_response_message(sender: str, 
                                  recipient: str,
                                  request_type: str, 
                                  request_data: Dict[str, Any],
                                  conversation_id: str,
                                  task_id: str) -> MCPMessage:
    """Create a request-response pattern message"""
    return MCPMessage(
        message_id=str(uuid.uuid4()),
        sender_agent_id=sender,
        recipient_agent_id=recipient,
        protocol=CommunicationProtocol.REQUEST_RESPONSE,
        priority=MessagePriority.NORMAL,
        message_type=request_type,
        payload=request_data,
        conversation_id=conversation_id,
        task_id=task_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        requires_ack=True,
        correlation_id=str(uuid.uuid4())
    )


def create_broadcast_message(sender: str,
                           message_type: str,
                           broadcast_data: Dict[str, Any], 
                           conversation_id: str,
                           task_id: str) -> MCPMessage:
    """Create a broadcast message to all agents"""
    return MCPMessage(
        message_id=str(uuid.uuid4()),
        sender_agent_id=sender,
        recipient_agent_id=None,  # None indicates broadcast
        protocol=CommunicationProtocol.BROADCAST,
        priority=MessagePriority.NORMAL,
        message_type=message_type,
        payload=broadcast_data,
        conversation_id=conversation_id,
        task_id=task_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        requires_ack=False
    )


# Example usage and demonstration functions
def demonstrate_mcp_communication_patterns():
    """
    Demonstrate MCP communication patterns functionality.
    
    Shows usage of factory functions, message broker, and workflow orchestrator
    in a complete example workflow.
    """
    print("🧪 Testing MCP Communication Patterns")
    
    broker = LTMCMessageBroker("test_conversation_123")
    
    # Create and send a test message
    test_message = create_request_response_message(
        sender="agent_a",
        recipient="agent_b", 
        request_type="analysis_request",
        request_data={"analysis_type": "dependency_mapping", "scope": "full_codebase"},
        conversation_id="test_conversation_123",
        task_id="test_task_456"
    )
    
    broker.send_message(test_message)
    
    # Test message retrieval
    messages = broker.receive_messages("agent_b")
    print(f"📬 Retrieved {len(messages)} messages for agent_b")
    
    # Test workflow orchestration
    orchestrator = WorkflowOrchestrator("test_workflow", "test_conversation_123")
    orchestrator.add_workflow_step("step1", "agent_planner", "Analyze architecture")
    orchestrator.add_workflow_step("step2", "agent_enforcer", "Validate quality", ["step1"])
    
    print("🔄 Testing workflow orchestration...")
    # Note: In production, this would be: await orchestrator.execute_workflow()
    print("✅ MCP Communication Patterns test completed")


# Main execution for testing
if __name__ == "__main__":
    # Fix imports for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
    
    from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
    from ltms.coordination.mcp_message_broker import LTMCMessageBroker
    from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
    
    demonstrate_mcp_communication_patterns()