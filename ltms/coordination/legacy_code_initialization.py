"""
Legacy Code Initialization
Agent initialization and coordination framework integration.

Extracted from legacy_code_analyzer.py for smart modularization (300-line limit compliance).
Handles initialize_agent and coordination setup with LTMC tools integration.

Components:
- LegacyCodeInitialization: Agent initialization with chat_action logging
"""

from typing import Dict, Any

# Import coordination framework components
from .agent_coordination_core import LTMCAgentCoordinator
from .agent_coordination_models import AgentStatus
from .mcp_communication_patterns import LTMCMessageBroker
from .agent_state_manager import LTMCAgentStateManager

# Import LTMC tools - MANDATORY
from ltms.tools.consolidated import (
    chat_action        # Tool 3 - Chat logging - MANDATORY
)


class LegacyCodeInitialization:
    """
    Legacy code analyzer agent initialization with LTMC integration.
    
    Handles initialization operations and coordination framework setup:
    - Agent registration with coordinator
    - Initial state creation with state manager
    - Initialization logging with chat_action
    - Message broker setup for agent communication
    - Task scope and output configuration
    
    Uses MANDATORY LTMC tools:
    - chat_action (Tool 3): Initialization logging and communication tracking
    """
    
    def __init__(self, coordinator: LTMCAgentCoordinator, state_manager: LTMCAgentStateManager):
        """
        Initialize legacy code analyzer initialization module.
        
        Args:
            coordinator: LTMC agent coordinator for registration and communication
            state_manager: Agent state manager for lifecycle management
        """
        self.agent_id = "legacy_code_analyzer"
        self.agent_type = "ltmc-legacy-analyzer"
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.message_broker = LTMCMessageBroker(coordinator.conversation_id)
    
    def initialize_agent(self) -> bool:
        """
        Initialize agent with coordination framework and LTMC integration.
        
        Performs complete agent initialization workflow:
        - Registers agent with coordinator with task scope and outputs
        - Creates initial agent state in state manager
        - Logs initialization in LTMC chat system for coordination tracking
        - Sets up message broker for agent communication
        
        Uses MANDATORY LTMC tools for initialization tracking:
        - chat_action for initialization logging and coordination communication
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Register with coordinator
            success = self.coordinator.register_agent(
                self.agent_id,
                self.agent_type,
                task_scope=["legacy_analysis", "decorator_mapping", "code_structure_analysis"],
                outputs=["legacy_inventory", "functional_tool_mapping", "removal_recommendations"]
            )
            
            if success:
                # Create agent state in state manager
                state_data = {
                    "agent_id": self.agent_id,
                    "task_scope": ["legacy_analysis", "decorator_mapping", "code_structure_analysis"],
                    "current_task": "initialization"
                }
                
                self.state_manager.create_agent_state(
                    self.agent_id,
                    AgentStatus.INITIALIZING,
                    state_data
                )
                
                # Log initialization in LTMC chat system (Tool 3) - MANDATORY
                chat_action(
                    action="log",
                    message=f"Legacy Code Analyzer initialized for coordination task {self.coordinator.task_id}",
                    tool_name=self.agent_id,
                    conversation_id=self.coordinator.conversation_id,
                    role="system"
                )
                
                print(f"✅ {self.agent_id} initialized successfully")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to initialize {self.agent_id}: {e}")
            return False