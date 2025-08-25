"""
LTMC Agent State Validator
Validation logic for agent state transitions and data integrity.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Provides comprehensive validation for the agent coordination framework.

Components:
- AgentStateValidator: Validates state transitions and state data structure
"""

from typing import Dict, Any, Optional
from .agent_coordination_models import AgentStatus


class AgentStateValidator:
    """
    Validates agent state transitions and data integrity.
    
    Provides static validation methods for the agent coordination framework:
    - State transition validation using transition matrix
    - State data structure validation with type checking
    - Comprehensive error reporting for invalid states
    
    Used by LTMCAgentStateManager to ensure coordination framework integrity.
    """
    
    # Valid state transitions matrix
    # Defines which state transitions are allowed in the coordination framework
    VALID_TRANSITIONS = {
        AgentStatus.INITIALIZING: [AgentStatus.ACTIVE, AgentStatus.ERROR],
        AgentStatus.ACTIVE: [AgentStatus.WAITING, AgentStatus.COMPLETED, AgentStatus.ERROR, AgentStatus.HANDOFF],
        AgentStatus.WAITING: [AgentStatus.ACTIVE, AgentStatus.ERROR, AgentStatus.COMPLETED],
        AgentStatus.COMPLETED: [AgentStatus.ACTIVE],  # Allow reactivation if needed
        AgentStatus.ERROR: [AgentStatus.ACTIVE, AgentStatus.INITIALIZING],  # Recovery options
        AgentStatus.HANDOFF: [AgentStatus.COMPLETED, AgentStatus.ACTIVE]
    }
    
    @classmethod
    def validate_transition(cls, from_status: AgentStatus, to_status: AgentStatus) -> bool:
        """
        Validate if state transition is allowed.
        
        Checks the transition matrix to determine if an agent can move
        from one status to another. Used to prevent invalid state changes
        that could compromise coordination framework integrity.
        
        Args:
            from_status: Current AgentStatus of the agent
            to_status: Desired target AgentStatus
            
        Returns:
            bool: True if transition is valid, False otherwise
            
        Example:
            >>> AgentStateValidator.validate_transition(
            ...     AgentStatus.INITIALIZING, 
            ...     AgentStatus.ACTIVE
            ... )
            True
            
            >>> AgentStateValidator.validate_transition(
            ...     AgentStatus.COMPLETED, 
            ...     AgentStatus.ERROR
            ... )
            False
        """
        if from_status not in cls.VALID_TRANSITIONS:
            return False
        return to_status in cls.VALID_TRANSITIONS[from_status]
    
    @classmethod
    def validate_state_data(cls, state_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate agent state data structure.
        
        Ensures that agent state data contains all required fields
        with correct data types. Used during agent state creation
        and updates to maintain data consistency.
        
        Required fields:
        - agent_id: string identifier
        - task_scope: list of task categories
        - current_task: string or None for current task name
        
        Args:
            state_data: Dictionary containing agent state information
            
        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
            - is_valid: True if data is valid, False otherwise
            - error_message: Description of validation error if invalid, None if valid
            
        Example:
            >>> valid_data = {
            ...     "agent_id": "test_agent",
            ...     "task_scope": ["analysis", "reporting"],
            ...     "current_task": "data_analysis"
            ... }
            >>> AgentStateValidator.validate_state_data(valid_data)
            (True, None)
            
            >>> invalid_data = {"agent_id": "test"}
            >>> AgentStateValidator.validate_state_data(invalid_data)
            (False, "Missing required field: task_scope")
        """
        required_fields = ["agent_id", "task_scope", "current_task"]
        
        # Check for required fields
        for field in required_fields:
            if field not in state_data:
                return False, f"Missing required field: {field}"
        
        # Validate data types
        if not isinstance(state_data.get("task_scope"), list):
            return False, "task_scope must be a list"
        
        if not isinstance(state_data.get("current_task"), (str, type(None))):
            return False, "current_task must be string or None"
        
        return True, None