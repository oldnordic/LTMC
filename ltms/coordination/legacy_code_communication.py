"""
Legacy Code Communication
Agent communication and message broker integration.

Extracted from legacy_code_analyzer.py for smart modularization (300-line limit compliance).
Handles send_analysis_to_next_agent and message coordination with LTMC tools integration.

Components:
- LegacyCodeCommunication: Communication handler with chat_action logging
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

# Import coordination framework components
from .agent_coordination_models import AgentStatus
from .agent_state_models import StateTransition
from .mcp_communication_patterns import create_request_response_message, MessagePriority

# Import LTMC tools - MANDATORY
from ltms.tools.consolidated import (
    chat_action        # Tool 3 - Chat logging - MANDATORY
)


class LegacyCodeCommunication:
    """
    Legacy code analyzer communication with LTMC integration.
    
    Handles communication operations and agent coordination:
    - Analysis result transmission to next agent
    - Message broker integration for coordination workflow
    - State transition to handoff status
    - Communication logging with chat_action
    - Message structure creation and validation
    
    Uses MANDATORY LTMC tools:
    - chat_action (Tool 3): Communication logging and handoff tracking
    """
    
    def __init__(self, coordinator, state_manager, message_broker, 
                 legacy_decorators: List[Dict[str, Any]], 
                 functional_tools: List[Dict[str, Any]], 
                 analysis_report: Dict[str, Any]):
        """
        Initialize legacy code analyzer communication module.
        
        Args:
            coordinator: LTMC agent coordinator for task and conversation context
            state_manager: Agent state manager for state transitions
            message_broker: Message broker for agent communication
            legacy_decorators: Analysis results - legacy decorators found
            functional_tools: Analysis results - functional tool mappings
            analysis_report: Analysis results - comprehensive analysis report
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.message_broker = message_broker
        self.agent_id = "legacy_code_analyzer"
        
        # Analysis results for communication
        self.legacy_decorators = legacy_decorators
        self.functional_tools = functional_tools
        self.analysis_report = analysis_report
    
    def send_analysis_to_next_agent(self, recipient_agent_id: str) -> bool:
        """
        Send analysis results to next agent in coordination workflow.
        
        Performs complete communication workflow:
        - Creates coordination message with analysis results
        - Sends message via message broker to recipient agent
        - Logs communication in LTMC chat system
        - Transitions agent to handoff state
        - Handles communication errors gracefully
        
        Uses LTMC message broker and chat system to coordinate with next agent
        in the legacy removal workflow (typically SafetyValidator).
        
        Uses MANDATORY LTMC tools for communication tracking:
        - chat_action for communication logging and handoff coordination
        
        Args:
            recipient_agent_id: ID of the agent to receive analysis results
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Create coordination message
            message_data = {
                "from_agent": self.agent_id,
                "to_agent": recipient_agent_id,
                "message_type": "analysis_results",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "legacy_decorators": self.legacy_decorators,
                    "functional_tools": self.functional_tools,
                    "analysis_report": self.analysis_report,
                    "coordination_task": self.coordinator.task_id
                }
            }
            
            # Send via message broker
            message = create_request_response_message(
                self.agent_id,
                recipient_agent_id,
                "legacy_analysis_complete",
                message_data,
                MessagePriority.HIGH,
                self.coordinator.conversation_id
            )
            
            success = self.message_broker.send_message(message)
            
            if success:
                # Log handoff in LTMC chat system (Tool 3) - MANDATORY
                chat_action(
                    action="log",
                    message=f"Legacy analysis results sent from {self.agent_id} to {recipient_agent_id}",
                    tool_name=self.agent_id,
                    conversation_id=self.coordinator.conversation_id,
                    role="system"
                )
                
                # Transition to handoff state
                self.state_manager.transition_agent_state(
                    self.agent_id,
                    AgentStatus.HANDOFF,
                    StateTransition.HANDOFF,
                    {"state_updates": {"handed_off_to": recipient_agent_id}}
                )
                
                print(f"✅ Analysis results sent to {recipient_agent_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to send analysis to {recipient_agent_id}: {e}")
            return False