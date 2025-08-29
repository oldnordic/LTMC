"""
LTMC Agent State Logging System
Centralized logging for agent state transitions using LTMC memory system.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Provides structured logging and storage of all agent state transitions.

Components:
- AgentStateLogging: Handles transition logging with LTMC storage
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# LTMC MCP tool imports
from ltms.tools.memory.memory_actions import memory_action

# Import state models and coordination framework types
from .agent_state_models import StateTransition, StateTransitionLog
from .agent_coordination_models import AgentStatus


class AgentStateLogging:
    """
    Agent state transition logging system using LTMC memory storage.
    
    Provides centralized logging for agent state transitions:
    - Log all successful and failed state transitions
    - Store structured transition data in LTMC memory
    - Maintain local transition history for quick access
    - Handle LTMC storage failures gracefully without affecting state management
    - Support complex transition data with nested structures
    
    Used by LTMCAgentStateManager to maintain comprehensive audit trail
    of all agent lifecycle events and state changes.
    """
    
    def __init__(self, coordination_id: str, conversation_id: str):
        """
        Initialize agent state logging system.
        
        Args:
            coordination_id: Unique identifier for the coordination session
            conversation_id: Conversation context identifier for LTMC storage
        """
        self.coordination_id = coordination_id
        self.conversation_id = conversation_id
        self.transition_logs: List[StateTransitionLog] = []
    
    def log_transition(self,
                      agent_id: str,
                      from_status: AgentStatus,
                      to_status: AgentStatus,
                      transition_type: StateTransition,
                      success: bool,
                      error_message: Optional[str] = None,
                      transition_data: Dict[str, Any] = None) -> None:
        """
        Log agent state transition with LTMC storage.
        
        Creates a comprehensive log entry for the state transition and stores
        it both locally and in LTMC memory system. Handles storage failures
        gracefully by maintaining local logs even if LTMC storage fails.
        
        Args:
            agent_id: Unique identifier of the agent
            from_status: Previous AgentStatus
            to_status: New AgentStatus
            transition_type: Type of state transition
            success: Whether the transition was successful
            error_message: Optional error message for failed transitions
            transition_data: Optional transition-specific data and metadata
            
        Example:
            >>> logging_system.log_transition(
            ...     "agent_1",
            ...     AgentStatus.INITIALIZING,
            ...     AgentStatus.ACTIVE,
            ...     StateTransition.ACTIVATE,
            ...     True,
            ...     transition_data={"activation_time": 150}
            ... )
        """
        # Create structured log entry
        log_entry = StateTransitionLog(
            agent_id=agent_id,
            from_status=from_status,
            to_status=to_status,
            transition_type=transition_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=success,
            error_message=error_message,
            transition_data=transition_data or {}
        )
        
        # Store locally for immediate access
        self.transition_logs.append(log_entry)
        
        # Prepare structured data for LTMC storage
        log_document = {
            "agent_id": log_entry.agent_id,
            "from_status": log_entry.from_status.value,
            "to_status": log_entry.to_status.value,
            "transition_type": log_entry.transition_type.value,
            "timestamp": log_entry.timestamp,
            "success": log_entry.success,
            "error_message": log_entry.error_message,
            "transition_data": log_entry.transition_data,
            "log_id": log_entry.log_id
        }
        
        # Store in LTMC memory with error handling
        # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
        # Generate dynamic file name based on transition log context, agent, and timestamp
        log_timestamp = log_entry.timestamp.replace(':', '_').replace('-', '_')
        transition_result = "success" if log_entry.success else "failed"
        dynamic_transition_log_file_name = f"transition_log_{agent_id}_{log_entry.from_status.value.lower()}_to_{log_entry.to_status.value.lower()}_{transition_result}_{log_entry.log_id}_{log_timestamp}.json"
        
        try:
            memory_action(
                action="store",
                file_name=dynamic_transition_log_file_name,
                content=json.dumps(log_document, indent=2),
                tags=["transition_log", agent_id, self.coordination_id],
                conversation_id=self.conversation_id,
                role="system"
            )
        except Exception as storage_error:
            # Log storage failure but don't raise exception
            # This ensures state management continues even if logging fails
            print(f"⚠️ Failed to store transition log in LTMC: {storage_error}")
    
    def get_transition_history(self, agent_id: str) -> List[StateTransitionLog]:
        """
        Get transition history for a specific agent.
        
        Returns all logged transitions for the specified agent in chronological
        order. Useful for debugging, auditing, and state analysis.
        
        Args:
            agent_id: Agent to get transition history for
            
        Returns:
            List[StateTransitionLog]: Chronologically ordered list of transitions
            
        Example:
            >>> history = logging_system.get_transition_history("agent_1")
            >>> for log in history:
            ...     print(f"{log.timestamp}: {log.from_status.value} → {log.to_status.value}")
        """
        return [log for log in self.transition_logs if log.agent_id == agent_id]
    
    def get_all_transition_logs(self) -> List[StateTransitionLog]:
        """
        Get all transition logs for all agents.
        
        Returns complete transition history in chronological order.
        
        Returns:
            List[StateTransitionLog]: All logged transitions
        """
        return self.transition_logs.copy()
    
    def get_failed_transitions(self) -> List[StateTransitionLog]:
        """
        Get all failed transition attempts.
        
        Useful for debugging and identifying problematic state transitions.
        
        Returns:
            List[StateTransitionLog]: All failed transitions
        """
        return [log for log in self.transition_logs if not log.success]
    
    def get_transition_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all transitions.
        
        Returns:
            Dict[str, Any]: Summary including counts, success rate, etc.
        """
        total_transitions = len(self.transition_logs)
        if total_transitions == 0:
            return {
                "total_transitions": 0,
                "successful_transitions": 0,
                "failed_transitions": 0,
                "success_rate": 0.0,
                "unique_agents": 0
            }
        
        successful_transitions = sum(1 for log in self.transition_logs if log.success)
        failed_transitions = total_transitions - successful_transitions
        unique_agents = len(set(log.agent_id for log in self.transition_logs))
        
        return {
            "total_transitions": total_transitions,
            "successful_transitions": successful_transitions,
            "failed_transitions": failed_transitions,
            "success_rate": successful_transitions / total_transitions,
            "unique_agents": unique_agents
        }