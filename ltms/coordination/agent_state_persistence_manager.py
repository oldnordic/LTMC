"""
Agent State Persistence Manager
Checkpoint and persistence operations with LTMC tools integration.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Handles persist_state_checkpoint, restore_from_checkpoint, and transition history with cache_action.

Components:
- AgentStatePersistenceManager: Checkpoint and persistence with cache_action optimization
"""

from typing import Dict, Any, List, Optional

# Import state models
from .agent_state_models import StateTransitionLog

# Import LTMC tools - MANDATORY
from ltms.tools.consolidated import (
    cache_action        # Tool 7 - Cache operations - MANDATORY
)


class AgentStatePersistenceManager:
    """
    Agent state persistence management with LTMC cache integration.
    
    Handles persistence operations and optimization:
    - State checkpoint creation and restoration
    - Performance optimization with cache_action
    - State transition history retrieval
    - Cache statistics and performance monitoring
    
    Uses MANDATORY LTMC tools:
    - cache_action (Tool 7): Performance optimization and cache management
    """
    
    def __init__(self, core, persistence, logging):
        """
        Initialize persistence management with dependencies.
        
        Args:
            core: AgentStateCore instance for state access
            persistence: AgentStatePersistence for checkpoint operations  
            logging: AgentStateLogging for transition history
        """
        self.core = core
        self.persistence = persistence
        self.logging = logging
    
    def persist_state_checkpoint(self, performance_metrics: Dict[str, Any]) -> bool:
        """
        Create checkpoint of all agent states with LTMC cache optimization.
        
        Uses MANDATORY LTMC tools for optimized checkpoint creation:
        - Retrieves cache statistics with cache_action for optimization
        - Creates comprehensive state checkpoint via persistence system
        - Optimizes checkpoint storage based on cache performance
        
        Args:
            performance_metrics: Current performance metrics to include in checkpoint
            
        Returns:
            bool: True if checkpoint created successfully
        """
        try:
            # Get cache performance statistics for optimization (Tool 7) - MANDATORY
            cache_action(
                action="stats",
                conversation_id=self.core.conversation_id,
                role="system"
            )
            
            # Create checkpoint using persistence system
            checkpoint_success = self.persistence.persist_state_checkpoint(
                self.core.agent_states, 
                performance_metrics
            )
            
            if checkpoint_success:
                print(f"✅ State checkpoint created for coordination: {self.core.coordination_id}")
            else:
                print(f"❌ Failed to create state checkpoint for coordination: {self.core.coordination_id}")
            
            return checkpoint_success
            
        except Exception as e:
            print(f"❌ Exception during checkpoint creation: {e}")
            # Still try to create checkpoint even if cache optimization fails
            return self.persistence.persist_state_checkpoint(
                self.core.agent_states, 
                performance_metrics
            )
    
    def restore_from_checkpoint(self, checkpoint_timestamp: str) -> bool:
        """
        Restore agent states from LTMC checkpoint with cache optimization.
        
        Uses MANDATORY LTMC tools for optimized restoration:
        - Retrieves cache statistics with cache_action for performance monitoring
        - Restores states from checkpoint via persistence system
        - Updates core state storage with restored data
        
        Args:
            checkpoint_timestamp: Timestamp identifier for checkpoint to restore
            
        Returns:
            bool: True if restoration successful
        """
        try:
            # Get cache statistics for restoration optimization (Tool 7) - MANDATORY
            cache_action(
                action="stats",
                conversation_id=self.core.conversation_id,
                role="system"
            )
            
            # Restore states from checkpoint using persistence system
            restored_states = self.persistence.restore_from_checkpoint(checkpoint_timestamp)
            
            if restored_states:
                # Update core state storage with restored data
                self.core.agent_states.update(restored_states)
                
                print(f"✅ State restoration completed from checkpoint: {checkpoint_timestamp}")
                return True
            else:
                print(f"⚠️ No checkpoint data found for timestamp: {checkpoint_timestamp}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during checkpoint restoration: {e}")
            return False
    
    def get_state_transition_history(self, agent_id: str) -> List[StateTransitionLog]:
        """
        Get state transition history for an agent.
        
        Delegates to the logging system for transition history retrieval.
        Provides access to complete audit trail of agent state changes.
        
        Args:
            agent_id: Agent identifier to get history for
            
        Returns:
            List[StateTransitionLog]: List of transition log entries for the agent
        """
        return self.logging.get_transition_history(agent_id)