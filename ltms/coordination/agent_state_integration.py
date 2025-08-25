"""
LTMC Agent State Integration Utilities
Integration functions for connecting state manager with coordination framework.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Provides utility functions for integrating state management with existing coordination systems.

Components:
- Integration functions for coordinator-to-state-manager mapping
"""

from typing import Dict, List, Any
from .agent_coordination_core import AgentCoordinationCore
from .agent_state_manager import LTMCAgentStateManager


def integrate_state_manager_with_coordinator(coordinator: AgentCoordinationCore) -> LTMCAgentStateManager:
    """
    Integrate state manager with existing coordination framework.
    
    Creates a new state manager instance and initializes agent states for all
    agents currently registered in the coordination framework. Maps agent
    registry data to state snapshots with proper status conversion and
    task scope initialization.
    
    Args:
        coordinator: Existing coordination framework instance with registered agents
        
    Returns:
        LTMCAgentStateManager: Fully integrated state manager with initialized agent states
        
    Example:
        >>> coordinator = LTMCAgentCoordinator("task123", "conversation456")
        >>> # ... register agents in coordinator ...
        >>> state_manager = integrate_state_manager_with_coordinator(coordinator)
        >>> print(f"Integrated {len(state_manager.get_all_agent_states())} agents")
    """
    # Create state manager with same IDs as coordinator
    state_manager = LTMCAgentStateManager(
        coordinator.task_id,
        coordinator.conversation_id
    )
    
    # Initialize states for all existing agents in coordinator
    for agent_id, registration in coordinator.agent_registry.items():
        # Create standardized state data structure from registration
        state_data = {
            "agent_id": agent_id,
            "task_scope": registration.task_scope,
            "current_task": None,  # Will be set when agent begins work
            "outputs_produced": [],  # Track agent outputs
            "dependencies_satisfied": []  # Track dependency resolution
        }
        
        # Create agent state with current registration status
        success = state_manager.create_agent_state(
            agent_id,
            registration.status,
            state_data
        )
        
        if not success:
            print(f"⚠️ Failed to create state for agent: {agent_id}")
    
    integrated_count = len(state_manager.get_all_agent_states())
    print(f"✅ State manager integrated with {integrated_count} agents")
    
    return state_manager


def sync_coordinator_with_state_manager(coordinator: AgentCoordinationCore, 
                                       state_manager: LTMCAgentStateManager) -> bool:
    """
    Synchronize coordinator agent registry with current state manager states.
    
    Updates the coordination framework's agent registry to match the current
    agent states in the state manager. Useful for keeping coordinator and
    state manager in sync during long-running operations.
    
    Args:
        coordinator: Coordination framework to update
        state_manager: State manager with current agent states
        
    Returns:
        bool: True if synchronization successful, False otherwise
        
    Example:
        >>> success = sync_coordinator_with_state_manager(coordinator, state_manager)
        >>> if success:
        ...     print("Coordinator synchronized with current states")
    """
    try:
        synced_count = 0
        
        for agent_id, state_snapshot in state_manager.get_all_agent_states().items():
            if agent_id in coordinator.agent_registry:
                # Update existing agent registration status
                coordinator.agent_registry[agent_id].status = state_snapshot.status
                synced_count += 1
            else:
                print(f"⚠️ Agent {agent_id} in state manager but not in coordinator registry")
        
        print(f"✅ Synchronized {synced_count} agent states with coordinator")
        return True
        
    except Exception as e:
        print(f"❌ Failed to synchronize coordinator with state manager: {e}")
        return False