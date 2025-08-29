"""
Workflow Error Handler
Error handling, rollback, and recovery mechanisms.

Extracted from legacy_removal_workflow.py for smart modularization (300-line limit compliance).
Handles exception management and error reporting with LTMC tools integration.

Components:
- WorkflowErrorHandler: Error handling with chat_action and memory_action logging
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

# Import coordination models
from .agent_coordination_models import AgentStatus

# Import LTMC tools - MANDATORY
from ltms.tools.memory.chat_actions import chat_action        # Tool 3 - Chat logging - MANDATORY
from ltms.tools.memory.memory_actions import memory_action       # Tool 1 - Memory operations - MANDATORY


class WorkflowErrorHandler:
    """
    Workflow error handling with comprehensive LTMC integration.
    
    Handles error management and recovery operations:
    - Comprehensive error logging with chat_action
    - Error report generation and storage with memory_action
    - Failure phase detection based on agent states
    - Error context compilation for debugging
    - Rollback preparation and error recovery guidance
    
    Uses MANDATORY LTMC tools:
    - chat_action (Tool 3): Error logging and communication tracking
    - memory_action (Tool 1): Error report storage and persistence
    """
    
    def __init__(self, coordinator, state_manager, analyzer, validator,
                 workflow_id: str, conversation_id: str):
        """
        Initialize workflow error handler.
        
        Args:
            coordinator: LTMC agent coordinator for coordination context
            state_manager: Agent state manager for state inspection
            analyzer: LegacyCodeAnalyzer agent for analysis context
            validator: SafetyValidator agent for validation context
            workflow_id: Unique workflow identifier
            conversation_id: Conversation context identifier
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.analyzer = analyzer
        self.validator = validator
        self.workflow_id = workflow_id
        self.conversation_id = conversation_id
    
    def handle_workflow_error(self, exception: Exception, error_phase: str) -> Dict[str, Any]:
        """
        Handle workflow error with comprehensive LTMC integration.
        
        Performs complete error handling workflow:
        - Creates comprehensive error message with context
        - Logs error for debugging with chat_action
        - Generates detailed error report with metadata
        - Stores error report with memory_action
        - Returns structured error response for workflow
        
        Uses MANDATORY LTMC tools for error tracking and storage:
        - chat_action for error logging and debugging
        - memory_action for error report persistence
        
        Args:
            exception: The exception that caused the workflow failure
            error_phase: The phase where the error occurred
            
        Returns:
            Dict[str, Any]: Structured error response with report and metadata
        """
        # Create comprehensive error message
        error_msg = f"Coordinated legacy removal workflow failed: {exception}"
        print(f"❌ {error_msg}")
        
        # Log error for debugging using chat_action (Tool 3) - MANDATORY
        chat_action(
            action="log",
            message=f"Workflow {self.workflow_id} failed: {error_msg}",
            tool_name="workflow_orchestrator",
            conversation_id=self.conversation_id,
            role="system"
        )
        
        # Generate detailed error report
        error_report = {
            "workflow_id": self.workflow_id,
            "error_timestamp": datetime.now(timezone.utc).isoformat(),
            "error_message": error_msg,
            "workflow_status": "FAILED",
            "error_phase": self.determine_failure_phase()
        }
        
        # Store error report using memory_action (Tool 1) - MANDATORY
        # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
        # Generate dynamic file name based on workflow error context, phase, and timestamp
        error_timestamp = error_report["error_timestamp"].replace(':', '_').replace('-', '_')
        error_phase = error_report["error_phase"]
        dynamic_error_report_file_name = f"workflow_error_report_{self.workflow_id}_{error_phase}_{error_timestamp}.json"
        
        memory_action(
            action="store",
            file_name=dynamic_error_report_file_name,
            content=json.dumps(error_report, indent=2),
            tags=["workflow_error", "legacy_removal", "coordination_failure"],
            conversation_id=self.conversation_id,
            role="system"
        )
        
        return {
            "success": False,
            "workflow_id": self.workflow_id,
            "error": error_msg,
            "error_report": error_report
        }
    
    def determine_failure_phase(self) -> str:
        """
        Determine which phase the workflow failed in for better error reporting.
        
        Analyzes agent states to determine the failure phase:
        - agent_initialization: Agent states not found
        - legacy_analysis: Analyzer in error state
        - safety_validation: Validator in error state or not found
        - workflow_coordination: Both agents active (coordination failure)
        - unknown_phase: State detection failed
        
        Returns:
            str: The phase where the workflow failure occurred
        """
        try:
            analyzer_state = self.state_manager.get_agent_state(self.analyzer.agent_id)
            validator_state = self.state_manager.get_agent_state(self.validator.agent_id)
            
            if not analyzer_state:
                return "agent_initialization"
            elif analyzer_state.status == AgentStatus.ERROR:
                return "legacy_analysis"
            elif not validator_state or validator_state.status == AgentStatus.ERROR:
                return "safety_validation"
            else:
                return "workflow_coordination"
                
        except Exception:
            return "unknown_phase"