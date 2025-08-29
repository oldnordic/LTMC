"""
Safety Validation Core Agent
Base agent functionality and coordination integration for safety validation.

Extracted from safety_validator.py for smart modularization (300-line limit compliance).
Provides core agent lifecycle, coordinator registration, and state management integration.

Components:
- SafetyValidationCore: Base agent class with coordination framework integration
"""

from typing import Dict, Any

# Import coordination framework components  
from .agent_coordination_models import AgentStatus
from .mcp_message_broker import LTMCMessageBroker

# Import LTMC chat tool for initialization logging - MANDATORY
from ltms.tools.memory.chat_actions import chat_action


class SafetyValidationCore:
    """
    Core safety validation agent with coordination framework integration.
    
    Provides base agent functionality including:
    - Agent registration with coordination framework
    - State management integration
    - Message broker integration for communication
    - Agent lifecycle management
    - LTMC tool integration for logging and tracking
    
    Part of the coordinated legacy removal workflow alongside LegacyCodeAnalyzer
    and LegacyRemovalWorkflow agents.
    """
    
    def __init__(self, coordinator, state_manager):
        """
        Initialize safety validation core agent.
        
        Args:
            coordinator: LTMC agent coordinator for registration and communication
            state_manager: Agent state manager for lifecycle management
        """
        self.agent_id = "safety_validator"
        self.agent_type = "ltmc-safety-validator" 
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.message_broker = LTMCMessageBroker(coordinator.conversation_id)
        
        # Initialize storage for validation results
        self.validation_report = {}
        self.safety_checks = []
        self.removal_plan = {}
    
    def initialize_agent(self) -> bool:
        """
        Initialize safety validator agent with coordination framework.
        
        Registers agent with coordinator, creates initial state, and sets up
        dependencies on LegacyCodeAnalyzer. Essential for coordinated workflow.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Register with coordinator including dependencies
            success = self.coordinator.register_agent(
                self.agent_id,
                self.agent_type,
                task_scope=["safety_validation", "dependency_analysis", "removal_planning"],
                dependencies=["legacy_code_analyzer"],
                outputs=["safety_report", "removal_plan", "validation_results"]
            )
            
            if success:
                # Create agent state in state manager
                state_data = {
                    "agent_id": self.agent_id,
                    "task_scope": ["safety_validation", "dependency_analysis", "removal_planning"],
                    "current_task": "initialization"
                }
                
                self.state_manager.create_agent_state(
                    self.agent_id,
                    AgentStatus.INITIALIZING,
                    state_data
                )
                
                # Log initialization in LTMC chat system - MANDATORY LTMC tool usage
                chat_action(
                    action="log",
                    message=f"Safety Validator initialized for coordination task {self.coordinator.task_id}",
                    tool_name=self.agent_id,
                    conversation_id=self.coordinator.conversation_id,
                    role="system"
                )
                
                print(f"✅ {self.agent_id} initialized successfully")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to initialize {self.agent_id}: {e}")
            return False