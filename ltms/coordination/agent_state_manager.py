"""
LTMC Agent State Management System
Modularized agent state management with comprehensive LTMC tools integration.

Smart modularization completed (300-line limit compliance).
Uses 4 focused modules with ALL 5 LTMC tools integration.

Components:
- LTMCAgentStateManager: Main class integrating all modular components
- AgentStateCore: Core state management with memory_action and graph_action
- AgentStateOperations: State creation/transitions with memory_action and graph_action
- AgentStateRecovery: Recovery operations with chat_action and todo_action
- AgentStatePersistenceManager: Checkpoints with cache_action optimization

Maintains ALL 5 LTMC tools integration: memory_action, todo_action, chat_action, 
cache_action, graph_action
"""

from typing import Dict, List, Optional, Any, Callable

# Import coordination models
from .agent_coordination_models import AgentStatus
from .agent_state_models import StateTransition, StateSnapshot, StateTransitionLog

# Import modularized components - ALL 4 modules
from .agent_state_core import AgentStateCore
from .agent_state_operations import AgentStateOperations
from .agent_state_recovery import AgentStateRecovery
from .agent_state_persistence_manager import AgentStatePersistenceManager

# Import existing helper components
from .agent_state_validator import AgentStateValidator
from .agent_state_persistence import AgentStatePersistence
from .agent_state_observer import AgentStateObserver
from .agent_state_logging import AgentStateLogging


class LTMCAgentStateManager:
    """
    Modularized agent state management system with comprehensive LTMC integration.
    
    Integrates 4 focused modules for complete state management:
    - AgentStateCore: Core storage and retrieval with LTMC memory/graph
    - AgentStateOperations: State creation/transitions with LTMC memory/graph
    - AgentStateRecovery: Recovery operations with LTMC chat/todo
    - AgentStatePersistenceManager: Checkpoints with LTMC cache optimization
    
    Maintains 100% LTMC tools integration across all modules with real functionality.
    """
    
    def __init__(self, coordination_id: str, conversation_id: str):
        """
        Initialize modular state management with ALL LTMC tools integration.
        
        Args:
            coordination_id: Unique coordination session identifier
            conversation_id: LTMC conversation context identifier
        """
        # Initialize core state management (memory_action, graph_action)
        self.core = AgentStateCore(coordination_id, conversation_id)
        
        # Initialize helper components
        self.validator = AgentStateValidator()
        self.persistence = AgentStatePersistence(coordination_id, conversation_id)
        self.observer = AgentStateObserver()
        self.logging = AgentStateLogging(coordination_id, conversation_id)
        
        # Initialize operations module (memory_action, graph_action)
        self.operations = AgentStateOperations(self.core, self.validator, self.logging)
        self.operations.observer = self.observer
        
        # Initialize recovery module (chat_action, todo_action)
        self.recovery = AgentStateRecovery(self.core, self.operations, self.observer)
        
        # Initialize persistence manager (cache_action)
        self.persistence_manager = AgentStatePersistenceManager(
            self.core, self.persistence, self.logging
        )
        
        # Performance metrics tracking (shared across modules)
        self.performance_metrics = {
            "state_transitions": 0,
            "validation_errors": 0,
            "recovery_attempts": 0,
            "successful_handoffs": 0,
            "average_transition_time": 0.0
        }
        
        # Share performance metrics with operations module
        self.operations.performance_metrics = self.performance_metrics
        
        # Expose core properties for compatibility
        self.coordination_id = self.core.coordination_id
        self.conversation_id = self.core.conversation_id
        self.agent_states = self.core.agent_states
    
    def create_agent_state(self, 
                          agent_id: str,
                          initial_status: AgentStatus,
                          state_data: Dict[str, Any]) -> bool:
        """
        Create initial state for an agent using operations module.
        
        Uses AgentStateOperations with memory_action and graph_action integration.
        
        Args:
            agent_id: Unique agent identifier
            initial_status: Starting agent status
            state_data: Initial state data
            
        Returns:
            bool: True if state created successfully
        """
        return self.operations.create_agent_state(agent_id, initial_status, state_data)
    
    def transition_agent_state(self,
                              agent_id: str,
                              new_status: AgentStatus,
                              transition_type: StateTransition,
                              transition_data: Dict[str, Any] = None) -> bool:
        """
        Transition agent to new state using operations module.
        
        Uses AgentStateOperations with memory_action and graph_action integration.
        
        Args:
            agent_id: Agent to transition
            new_status: Target status
            transition_type: Type of transition
            transition_data: Optional transition-specific data
            
        Returns:
            bool: True if transition successful
        """
        return self.operations.transition_agent_state(agent_id, new_status, transition_type, transition_data)
    
    def get_agent_state(self, agent_id: str) -> Optional[StateSnapshot]:
        """Get current state snapshot for an agent using core module."""
        return self.core.get_agent_state(agent_id)
    
    def get_all_agent_states(self) -> Dict[str, StateSnapshot]:
        """Get all current agent states using core module."""
        return self.core.get_all_agent_states()
    
    def get_agents_by_status(self, status: AgentStatus) -> List[str]:
        """Get list of agent IDs with specific status using core module."""
        return self.core.get_agents_by_status(status)
    
    def recover_agent_state(self, agent_id: str) -> bool:
        """
        Attempt to recover an agent from error state using recovery module.
        
        Uses AgentStateRecovery with chat_action and todo_action integration.
        
        Args:
            agent_id: Agent to recover
            
        Returns:
            bool: True if recovery successful
        """
        return self.recovery.recover_agent_state(agent_id)
    
    def register_state_observer(self, 
                               agent_id: str,
                               observer: Callable[[str, AgentStatus, AgentStatus], None]) -> None:
        """
        Register observer for agent state changes using recovery module.
        
        Args:
            agent_id: Agent to observe (or "*" for all agents)
            observer: Callback function
        """
        self.recovery.register_state_observer(agent_id, observer)
    
    def get_state_transition_history(self, agent_id: str) -> List[StateTransitionLog]:
        """Get state transition history for an agent using persistence manager."""
        return self.persistence_manager.get_state_transition_history(agent_id)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get state management performance metrics."""
        return self.performance_metrics.copy()
    
    def persist_state_checkpoint(self) -> bool:
        """
        Create checkpoint of all agent states using persistence manager.
        
        Uses AgentStatePersistenceManager with cache_action optimization.
        
        Returns:
            bool: True if checkpoint created successfully
        """
        return self.persistence_manager.persist_state_checkpoint(self.performance_metrics)
    
    def restore_from_checkpoint(self, checkpoint_timestamp: str) -> bool:
        """
        Restore agent states from LTMC checkpoint using persistence manager.
        
        Uses AgentStatePersistenceManager with cache_action optimization.
        
        Args:
            checkpoint_timestamp: Timestamp identifier for checkpoint to restore
            
        Returns:
            bool: True if restoration successful
        """
        return self.persistence_manager.restore_from_checkpoint(checkpoint_timestamp)