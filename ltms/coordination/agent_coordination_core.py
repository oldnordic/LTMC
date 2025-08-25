"""
LTMC Agent Coordination Core - Integrated Version
Main coordination logic orchestrating all framework components.

Smart modularization completed (300-line limit compliance).
Uses 3 focused modules with ALL LTMC tools integration maintained.

Components:
- AgentCoordinationCore: Main coordination orchestrator integrating all modules
- CoordinationCoreState: Core state management with memory_action
- CoordinationAgentOperations: Agent operations with graph_action
- CoordinationReporting: Reporting and finalization with memory_action

Maintains ALL LTMC tools integration: memory_action, graph_action
"""

from typing import Dict, List, Optional, Any

# Import modularized components
from .coordination_core_state import CoordinationCoreState
from .coordination_agent_operations import CoordinationAgentOperations
from .coordination_reporting import CoordinationReporting

# Import coordination models
from .agent_coordination_models import AgentMessage


class AgentCoordinationCore:
    """
    Modularized main coordination orchestrator for LTMC agent coordination framework.
    
    Integrates 3 focused modules for complete coordination functionality:
    - CoordinationCoreState: Core state management with LTMC memory integration
    - CoordinationAgentOperations: Agent operations with LTMC graph integration
    - CoordinationReporting: Reporting and finalization with LTMC memory integration
    
    Maintains 100% LTMC tools integration across all modules with real functionality.
    Uses 2 LTMC tools: memory_action, graph_action.
    """
    
    def __init__(self, task_description: str, coordination_id: Optional[str] = None):
        """
        Initialize modularized agent coordination core.
        
        Sets up all modular components with shared coordination context.
        
        Args:
            task_description: Description of coordination task
            coordination_id: Optional custom coordination ID
        """
        # Initialize core state module
        self.state_manager = CoordinationCoreState(task_description, coordination_id)
        
        # Initialize agent operations module
        self.agent_operations = CoordinationAgentOperations(
            self.state_manager.task_id,
            self.state_manager.conversation_id
        )
        
        # Initialize reporting module
        self.reporting = CoordinationReporting(
            self.state_manager.task_id,
            self.state_manager.conversation_id,
            task_description
        )
        
        # Expose properties for compatibility
        self.task_id = self.state_manager.task_id
        self.conversation_id = self.state_manager.conversation_id
        self.task_description = task_description
        self.state = self.state_manager.state
    
    # Core state delegation methods
    def get_coordination_state(self) -> Dict[str, Any]:
        """Delegate to state manager for coordination state."""
        return self.state_manager.get_coordination_state()
    
    def get_task_info(self) -> Dict[str, str]:
        """Delegate to state manager for task information."""
        return self.state_manager.get_task_info()
    
    def add_active_agent(self, agent_id: str) -> None:
        """Delegate to state manager for active agent management."""
        self.state_manager.add_active_agent(agent_id)
    
    # Agent operations delegation methods
    def register_agent(self, 
                      agent_id: str,
                      agent_type: str, 
                      task_scope: List[str],
                      dependencies: List[str] = None,
                      outputs: List[str] = None) -> bool:
        """
        Register an agent with the coordination framework.
        
        Delegates to agent operations module and updates core state.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (e.g., 'ltmc-architectural-planner')  
            task_scope: List of tasks this agent will handle
            dependencies: List of other agents this agent depends on
            outputs: List of outputs this agent will produce
        
        Returns:
            bool: True if registration successful
        """
        success = self.agent_operations.register_agent(
            agent_id, agent_type, task_scope, dependencies, outputs
        )
        
        if success:
            # Update coordination state via state manager
            self.state_manager.add_active_agent(agent_id)
            
        return success
    
    def send_agent_message(self, message: AgentMessage) -> bool:
        """Delegate to agent operations for message sending."""
        return self.agent_operations.send_agent_message(message)
    
    def retrieve_agent_messages(self, agent_id: str, since_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Delegate to agent operations for message retrieval."""
        return self.agent_operations.retrieve_agent_messages(agent_id, since_timestamp)
    
    def coordinate_agent_handoff(self, from_agent: str, to_agent: str, handoff_data: Dict[str, Any]) -> bool:
        """
        Coordinate handoff between agents with context transfer.
        
        Delegates to agent operations and updates core state.
        
        Args:
            from_agent: Agent handing off work
            to_agent: Agent receiving work  
            handoff_data: Data to transfer between agents
            
        Returns:
            bool: True if handoff successful
        """
        success = self.agent_operations.coordinate_agent_handoff(from_agent, to_agent, handoff_data)
        
        if success:
            # Update current agent in coordination state
            self.state_manager.set_current_agent(to_agent)
            
        return success
    
    def get_agent_status(self, agent_id: str):
        """Delegate to agent operations for agent status."""
        return self.agent_operations.get_agent_status(agent_id)
    
    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """Delegate to agent operations for registered agents."""
        return self.agent_operations.get_registered_agents()
    
    # Reporting delegation methods
    def get_coordination_summary(self) -> Dict[str, Any]:
        """Delegate to reporting module for coordination summary."""
        return self.reporting.get_coordination_summary(
            self.state_manager.get_coordination_state(),
            self.agent_operations.registration_manager
        )
    
    def finalize_coordination(self) -> Dict[str, Any]:
        """Delegate to reporting module for coordination finalization."""
        return self.reporting.finalize_coordination(
            self.state_manager.get_coordination_state(),
            self.agent_operations.registration_manager
        )
    
    def generate_interim_report(self) -> Dict[str, Any]:
        """Delegate to reporting module for interim report generation."""
        return self.reporting.generate_interim_report(
            self.state_manager.get_coordination_state(),
            self.agent_operations.registration_manager
        )