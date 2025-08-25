"""
LTMC Agent State Observer System
Observer pattern implementation for agent state change notifications.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Provides decoupled notification system for agent state transitions.

Components:
- AgentStateObserver: Manages observer registration and notifications
"""

from typing import Callable, List, Dict
from collections import defaultdict

# Import coordination framework types
from .agent_coordination_models import AgentStatus


class AgentStateObserver:
    """
    Agent state observer system implementing the Observer pattern.
    
    Provides decoupled notification system for agent state changes:
    - Register observers for specific agents or global notifications
    - Notify observers when agent states transition
    - Handle observer failures gracefully without affecting state management
    - Support multiple observers per agent with proper error isolation
    
    Used by LTMCAgentStateManager to notify interested parties of state changes
    without tight coupling between state management and notification logic.
    """
    
    def __init__(self):
        """
        Initialize agent state observer system.
        
        Creates storage for observers using defaultdict to automatically
        handle new agent registrations without explicit initialization.
        """
        # Storage for observers: agent_id -> list of callback functions
        # Special key "*" is used for global observers that receive all notifications
        self.observers: Dict[str, List[Callable[[str, AgentStatus, AgentStatus], None]]] = defaultdict(list)
    
    def register_observer(self, 
                         agent_id: str,
                         observer: Callable[[str, AgentStatus, AgentStatus], None]) -> None:
        """
        Register observer for agent state changes.
        
        Observers are callback functions that receive notifications when agent
        states change. Supports both specific agent observers and global observers.
        
        Args:
            agent_id: Agent to observe, or "*" for all agents (global observer)
            observer: Callback function with signature (agent_id, from_status, to_status)
                     
        Example:
            >>> def my_observer(agent_id, from_status, to_status):
            ...     print(f"{agent_id}: {from_status.value} → {to_status.value}")
            
            >>> observer_system.register_observer("agent_1", my_observer)
            >>> observer_system.register_observer("*", my_observer)  # Global observer
        """
        self.observers[agent_id].append(observer)
        print(f"✅ State observer registered for: {agent_id}")
    
    def notify_observers(self,
                        agent_id: str,
                        from_status: AgentStatus,
                        to_status: AgentStatus) -> None:
        """
        Notify registered observers of state changes.
        
        Notifies both specific agent observers and global observers ("*").
        Handles observer callback failures gracefully by logging errors
        but continuing to notify other observers.
        
        Args:
            agent_id: Agent that underwent state transition
            from_status: Previous AgentStatus
            to_status: New AgentStatus
            
        Example:
            >>> observer_system.notify_observers(
            ...     "agent_1",
            ...     AgentStatus.INITIALIZING,
            ...     AgentStatus.ACTIVE
            ... )
        """
        try:
            # Notify specific agent observers
            for observer in self.observers.get(agent_id, []):
                try:
                    observer(agent_id, from_status, to_status)
                except Exception as observer_error:
                    print(f"⚠️ Observer failed for {agent_id}: {observer_error}")
            
            # Notify global observers (registered with "*")
            for observer in self.observers.get("*", []):
                try:
                    observer(agent_id, from_status, to_status)
                except Exception as observer_error:
                    print(f"⚠️ Global observer failed for {agent_id}: {observer_error}")
                
        except Exception as e:
            print(f"⚠️ Failed to notify state observers: {e}")
    
    def get_observer_count(self, agent_id: str = None) -> int:
        """
        Get count of registered observers.
        
        Args:
            agent_id: Specific agent to count observers for, or None for total count
            
        Returns:
            int: Number of observers registered
            
        Example:
            >>> total = observer_system.get_observer_count()
            >>> agent_specific = observer_system.get_observer_count("agent_1")
        """
        if agent_id is not None:
            return len(self.observers.get(agent_id, []))
        else:
            return sum(len(observers) for observers in self.observers.values())
    
    def has_observers(self, agent_id: str = None) -> bool:
        """
        Check if any observers are registered.
        
        Args:
            agent_id: Specific agent to check, or None to check if any observers exist
            
        Returns:
            bool: True if observers are registered, False otherwise
            
        Example:
            >>> if observer_system.has_observers("agent_1"):
            ...     print("Agent has observers")
        """
        if agent_id is not None:
            return len(self.observers.get(agent_id, [])) > 0
        else:
            return len(self.observers) > 0 and any(len(obs) > 0 for obs in self.observers.values())
    
    def clear_observers(self, agent_id: str = None) -> None:
        """
        Clear observers for specific agent or all observers.
        
        Args:
            agent_id: Specific agent to clear observers for, or None to clear all observers
            
        Example:
            >>> observer_system.clear_observers("agent_1")  # Clear specific agent
            >>> observer_system.clear_observers()  # Clear all observers
        """
        if agent_id is not None:
            if agent_id in self.observers:
                del self.observers[agent_id]
                print(f"✅ Cleared observers for: {agent_id}")
        else:
            self.observers.clear()
            print("✅ Cleared all observers")
    
    def get_observer_summary(self) -> Dict[str, int]:
        """
        Get summary of observer registrations.
        
        Returns:
            Dict[str, int]: Dictionary mapping agent_id to observer count
            
        Example:
            >>> summary = observer_system.get_observer_summary()
            >>> print(f"Agent 1 has {summary.get('agent_1', 0)} observers")
        """
        return {agent_id: len(observers) for agent_id, observers in self.observers.items()}