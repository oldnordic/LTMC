"""
Workflow Initialization
Workflow setup and coordination framework integration.

Extracted from legacy_removal_workflow.py for smart modularization (300-line limit compliance).
Handles __init__ and framework setup with LTMC tools integration.

Components:
- WorkflowInitialization: Framework setup with todo_action and chat_action logging
"""

import time
from typing import Dict, Any

# Import coordination framework components
from .agent_coordination_core import AgentCoordinationCore
from .agent_state_manager import LTMCAgentStateManager
from .mcp_workflow_orchestrator import WorkflowOrchestrator
from .agent_state_integration import integrate_state_manager_with_coordinator

# Import coordinated agents
from .legacy_code_analyzer import LegacyCodeAnalyzer
from .safety_validator import SafetyValidator

# Import LTMC tools - MANDATORY
from ltms.tools.todos.todo_actions import todo_action        # Tool 2 - Task management - MANDATORY
from ltms.tools.memory.chat_actions import chat_action         # Tool 3 - Chat logging - MANDATORY


class WorkflowInitialization:
    """
    Workflow initialization with comprehensive LTMC integration.
    
    Handles initialization operations and framework setup:
    - Workflow ID and conversation ID generation
    - Coordination framework initialization
    - State management with coordinator integration
    - Workflow orchestrator setup for advanced coordination
    - Agent initialization and registration
    - Initialization logging with todo_action and chat_action
    
    Uses MANDATORY LTMC tools:
    - todo_action (Tool 2): Workflow tracking task creation
    - chat_action (Tool 3): Phase completion logging and coordination tracking
    """
    
    def __init__(self):
        """
        Initialize coordinated legacy removal workflow framework.
        
        Sets up complete coordination framework, state management,
        workflow orchestration, and specialized agents with unique identifiers.
        """
        self.workflow_id = f"legacy_removal_workflow_{int(time.time())}"
        self.conversation_id = f"legacy_removal_{self.workflow_id}"
        
        # Initialize coordination framework
        self.coordinator = AgentCoordinationCore(
            f"Legacy Code Removal - Coordinated Multi-Agent Workflow",
            self.workflow_id
        )
        
        # Initialize state management with coordinator integration
        self.state_manager = integrate_state_manager_with_coordinator(self.coordinator)
        
        # Initialize workflow orchestrator for advanced coordination
        self.workflow_orchestrator = WorkflowOrchestrator(
            self.workflow_id,
            self.conversation_id
        )
        
        # Initialize specialized coordinated agents
        self.analyzer = LegacyCodeAnalyzer(self.coordinator, self.state_manager)
        self.validator = SafetyValidator(self.coordinator, self.state_manager)
        
        # Workflow execution results storage
        self.workflow_results = {}
    
    def initialize_workflow(self) -> Dict[str, Any]:
        """
        Initialize workflow with complete coordination framework setup.
        
        Performs complete workflow initialization:
        - Creates workflow tracking task with todo_action
        - Initializes all coordinated agents
        - Validates agent initialization success
        - Logs phase completion with chat_action
        - Returns initialization status and metadata
        
        Uses MANDATORY LTMC tools for workflow tracking and logging:
        - todo_action for workflow task tracking
        - chat_action for phase completion logging
        
        Returns:
            Dict[str, Any]: Initialization results with success status and metadata
        """
        try:
            print("\n📋 Phase 1: Agent Initialization and Workflow Setup")
            
            # Create workflow tracking task using todo_action (Tool 2) - MANDATORY
            workflow_task = todo_action(
                action="add",
                content=f"Execute coordinated legacy removal workflow {self.workflow_id}",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Initialize all coordinated agents
            analyzer_init = self.analyzer.initialize_agent()
            validator_init = self.validator.initialize_agent()
            
            if not (analyzer_init and validator_init):
                raise Exception("Agent initialization failed - coordination cannot proceed")
            
            # Log phase completion using chat_action (Tool 3) - MANDATORY
            chat_action(
                action="log",
                message=f"Phase 1 Complete: All agents initialized for workflow {self.workflow_id}",
                tool_name="workflow_orchestrator",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            print("✅ All agents initialized successfully")
            
            return {
                "success": True,
                "workflow_id": self.workflow_id,
                "conversation_id": self.conversation_id,
                "agents_initialized": 2,
                "phase": 1,
                "workflow_task": workflow_task,
                "analyzer_initialized": analyzer_init,
                "validator_initialized": validator_init
            }
            
        except Exception as e:
            error_msg = f"Workflow initialization failed: {e}"
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "workflow_id": self.workflow_id,
                "conversation_id": self.conversation_id,
                "error": error_msg,
                "phase": 1
            }