"""
Agent State Recovery
Recovery operations and performance monitoring with LTMC tools integration.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Handles recover_agent_state, performance metrics, and observer management with LTMC tools.

Components:
- AgentStateRecovery: Recovery operations with chat_action and todo_action integration
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Callable

# Import coordination models
from .agent_coordination_models import AgentStatus
from .agent_state_models import StateTransition

# Import LTMC tools - MANDATORY
from ltms.tools.memory.chat_actions import chat_action        # Tool 3 - Chat logging - MANDATORY
from ltms.tools.todos.todo_actions import todo_action         # Tool 2 - Todo management - MANDATORY


class AgentStateRecovery:
    """
    Agent state recovery with comprehensive LTMC integration.
    
    Handles recovery operations and monitoring:
    - Agent error state recovery with validation
    - Recovery task tracking with todo_action
    - Recovery logging with chat_action
    - Performance metrics and monitoring
    - Observer pattern integration
    
    Uses MANDATORY LTMC tools:
    - chat_action (Tool 3): Recovery logging and communication
    - todo_action (Tool 2): Recovery task management and tracking
    """
    
    def __init__(self, core, operations, observer):
        """
        Initialize recovery management with dependencies.
        
        Args:
            core: AgentStateCore instance for state access
            operations: AgentStateOperations for state transitions
            observer: AgentStateObserver for state change notifications
        """
        self.core = core
        self.operations = operations
        self.observer = observer
        
        # Performance metrics for recovery operations
        self.performance_metrics = {
            "recovery_attempts": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "average_recovery_time": 0.0
        }
    
    def recover_agent_state(self, agent_id: str) -> bool:
        """
        Attempt to recover an agent from error state with LTMC integration.
        
        Uses MANDATORY LTMC tools for complete recovery process:
        - Validates agent exists and is in error state
        - Creates recovery data with error context
        - Logs recovery attempt with chat_action
        - Creates recovery task with todo_action
        - Transitions agent state via operations
        
        Args:
            agent_id: Agent to recover
            
        Returns:
            bool: True if recovery successful
        """
        try:
            # Check if agent exists in core state storage
            current_snapshot = self.core.agent_states.get(agent_id)
            if not current_snapshot:
                print(f"❌ Cannot recover {agent_id}: agent not found")
                return False
            
            # Check if agent is in error state
            if current_snapshot.status != AgentStatus.ERROR:
                print(f"⚠️ Agent {agent_id} is not in error state, recovery not needed")
                return True
            
            # Prepare recovery data with error context
            recovery_data = {
                "recovery_attempt": True,
                "original_error": current_snapshot.metadata.get("error_message", "Unknown error"),
                "recovery_time": datetime.now(timezone.utc).isoformat(),
                "recovery_initiated_by": "state_recovery_system"
            }
            
            # Log recovery initiation with chat_action (Tool 3) - MANDATORY
            chat_action(
                action="log",
                message=f"Agent recovery initiated for {agent_id}: attempting to recover from error state",
                tool_name="state_recovery",
                conversation_id=self.core.conversation_id,
                role="system"
            )
            
            # Create recovery tracking task with todo_action (Tool 2) - MANDATORY
            todo_action(
                action="add",
                task=f"Recovery: {agent_id} - Recover agent from error state and restore functionality",
                tags=["agent_recovery", "error_recovery", self.core.coordination_id, agent_id],
                conversation_id=self.core.conversation_id,
                role="system"
            )
            
            # Attempt recovery transition via operations
            transition_success = self.operations.transition_agent_state(
                agent_id,
                AgentStatus.INITIALIZING,
                StateTransition.RETRY,
                {"state_updates": recovery_data}
            )
            
            if transition_success:
                # Update performance metrics
                self.performance_metrics["recovery_attempts"] += 1
                self.performance_metrics["successful_recoveries"] += 1
                
                print(f"✅ Agent {agent_id} recovery initiated successfully")
                return True
            else:
                # Update failure metrics
                self.performance_metrics["failed_recoveries"] += 1
                print(f"❌ Failed to transition {agent_id} during recovery")
                return False
            
        except Exception as e:
            print(f"❌ Failed to recover agent {agent_id}: {e}")
            self.performance_metrics["failed_recoveries"] += 1
            return False
    
    def register_state_observer(self, 
                               agent_id: str,
                               observer: Callable[[str, AgentStatus, AgentStatus], None]) -> None:
        """
        Register observer for agent state changes.
        
        Delegates to the observer system for state change notifications.
        
        Args:
            agent_id: Agent to observe (or "*" for all agents)
            observer: Callback function for state change notifications
        """
        self.observer.register_observer(agent_id, observer)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get recovery performance metrics.
        
        Returns:
            Dict[str, Any]: Copy of current performance metrics including:
                - recovery_attempts: Total recovery attempts
                - successful_recoveries: Number of successful recoveries
                - failed_recoveries: Number of failed recovery attempts
                - average_recovery_time: Average time for recovery operations
        """
        return self.performance_metrics.copy()