"""
LTMC Test Agent Utility
Reusable test agent for coordination framework validation and testing.

Extracted from coordination_test_example.py for smart modularization (300-line limit compliance).
Provides simulated agent behavior for comprehensive coordination framework testing.

Components:
- TestAgent: Simulated agent with full coordination framework integration
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any

# Import coordination framework components
from .agent_coordination_core import AgentCoordinationCore
from .agent_coordination_models import (
    AgentStatus,
    AgentMessage
)
from .mcp_message_broker import LTMCMessageBroker
from .mcp_message_models import MCPMessage
from .mcp_communication_factory import create_request_response_message
from .agent_state_manager import LTMCAgentStateManager
from .agent_state_models import StateTransition

# LTMC MCP tool imports for validation
from ltms.tools.memory.memory_actions import memory_action


class TestAgent:
    """
    Simulated agent for testing coordination framework.
    
    Provides complete agent simulation including:
    - Coordination framework integration
    - Task execution simulation with real LTMC tool usage
    - Inter-agent communication via message broker
    - State management with proper transitions
    - Error handling and recovery mechanisms
    
    Used for comprehensive testing of the LTMC agent coordination system.
    """
    
    def __init__(self, agent_id: str, agent_type: str, coordinator: AgentCoordinationCore):
        """
        Initialize test agent with coordination framework.
        
        Args:
            agent_id: Unique identifier for this test agent
            agent_type: Type of agent being simulated (e.g., 'ltmc-planner')
            coordinator: AgentCoordinationCore instance for registration and coordination
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.coordinator = coordinator
        self.state_manager = None
        self.message_broker = None
        
        # Agent-specific behavior tracking
        self.task_results = {}
        self.received_messages = []
    
    def initialize(self, state_manager: LTMCAgentStateManager, message_broker: LTMCMessageBroker) -> bool:
        """
        Initialize agent with coordination components.
        
        Registers agent with coordinator and sets up state management and messaging.
        
        Args:
            state_manager: State management system for agent coordination
            message_broker: Message broker for inter-agent communication
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        self.state_manager = state_manager
        self.message_broker = message_broker
        
        # Register with coordinator
        success = self.coordinator.register_agent(
            self.agent_id,
            self.agent_type,
            task_scope=[f"{self.agent_type}_tasks"],
            outputs=[f"{self.agent_type}_results"]
        )
        
        if success:
            print(f"✅ Test agent {self.agent_id} initialized successfully")
        
        return success
    
    def execute_task(self, task_description: str) -> Dict[str, Any]:
        """
        Simulate agent task execution with full coordination framework integration.
        
        Performs realistic task simulation including:
        - State transitions (ACTIVE → COMPLETED/ERROR)
        - Task execution simulation
        - Result generation and storage
        - LTMC memory integration for result persistence
        
        Args:
            task_description: Description of task to simulate
            
        Returns:
            Dict[str, Any]: Task execution results or error information
        """
        try:
            # Update state to active
            if self.state_manager:
                self.state_manager.transition_agent_state(
                    self.agent_id,
                    AgentStatus.ACTIVE,
                    StateTransition.ACTIVATE,
                    {"state_updates": {"current_task": task_description}}
                )
            
            # Simulate work
            print(f"🔄 {self.agent_id} executing: {task_description}")
            time.sleep(0.1)  # Brief simulation delay
            
            # Generate realistic results
            result = {
                "agent_id": self.agent_id,
                "task": task_description,
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "findings": f"Simulated findings from {self.agent_id}",
                "metrics": {
                    "execution_time": "0.1s",
                    "success_rate": "100%"
                }
            }
            
            self.task_results[task_description] = result
            
            # Update state to completed
            if self.state_manager:
                self.state_manager.transition_agent_state(
                    self.agent_id,
                    AgentStatus.COMPLETED,
                    StateTransition.COMPLETE,
                    {"state_updates": {"last_result": result}}
                )
            
            # Store results in LTMC using real memory_action tool
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic file name based on test agent execution context, task, and result metrics
            execution_timestamp = result["timestamp"].replace(':', '_').replace('-', '_')
            task_name_clean = task_description.replace(' ', '_').replace('/', '_').lower()[:20]  # Truncate long task names
            agent_type_clean = self.agent_type.replace('-', '_').lower()
            result_status = result["status"]
            success_rate = result["metrics"]["success_rate"].replace('%', 'pct')
            dynamic_test_result_file_name = f"test_agent_result_{self.agent_id}_{agent_type_clean}_{task_name_clean}_{result_status}_{success_rate}_{execution_timestamp}.json"
            
            memory_action(
                action="store",
                file_name=dynamic_test_result_file_name,
                content=json.dumps(result, indent=2),
                tags=["test_agent_result", self.agent_id, "coordination_test"],
                conversation_id=self.coordinator.conversation_id,
                role="system"
            )
            
            print(f"✅ {self.agent_id} completed task: {task_description}")
            return result
            
        except Exception as e:
            print(f"❌ {self.agent_id} task execution failed: {e}")
            
            # Update state to error
            if self.state_manager:
                self.state_manager.transition_agent_state(
                    self.agent_id,
                    AgentStatus.ERROR,
                    StateTransition.FAIL,
                    {"state_updates": {"error_message": str(e)}}
                )
            
            return {"error": str(e)}
    
    def send_message_to_agent(self, recipient_id: str, message_content: Dict[str, Any]) -> bool:
        """
        Send message to another agent via message broker.
        
        Creates properly formatted MCP message and sends via broker system.
        
        Args:
            recipient_id: ID of recipient agent
            message_content: Message content to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.message_broker:
            return False
        
        message = create_request_response_message(
            sender=self.agent_id,
            recipient=recipient_id,
            request_type="agent_communication",
            request_data=message_content,
            conversation_id=self.coordinator.conversation_id,
            task_id=self.coordinator.task_id
        )
        
        return self.message_broker.send_message(message)
    
    def process_pending_messages(self) -> int:
        """
        Process messages sent to this agent.
        
        Retrieves and processes all pending messages from the message broker.
        Handles processing errors gracefully to prevent message loss.
        
        Returns:
            int: Number of messages successfully processed
        """
        if not self.message_broker:
            return 0
        
        messages = self.message_broker.receive_messages(self.agent_id)
        processed = 0
        
        for message in messages:
            try:
                print(f"📬 {self.agent_id} received message from {message.sender_agent_id}")
                self.received_messages.append(message)
                processed += 1
            except Exception as e:
                print(f"⚠️ Failed to process message: {e}")
        
        return processed