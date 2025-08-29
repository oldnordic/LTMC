"""
Agent State Core
Core state management and initialization with LTMC tools integration.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Handles core state storage, retrieval, and LTMC initialization with memory_action and graph_action.

Components:
- AgentStateCore: Core state management with LTMC memory and graph integration
"""

import json
from datetime import datetime, timezone
from typing import Dict, Optional, List

# Import coordination models
from .agent_coordination_models import AgentStatus
from .agent_state_models import StateSnapshot

# Import LTMC tools - MANDATORY
from ltms.tools.memory.memory_actions import memory_action      # Tool 1 - Memory operations - MANDATORY
from ltms.tools.graph.graph_actions import graph_action        # Tool 8 - Knowledge graph - MANDATORY


class AgentStateCore:
    """
    Core agent state management with LTMC integration.
    
    Provides foundational state management operations:
    - State storage and retrieval
    - LTMC memory integration with memory_action
    - Knowledge graph relationships with graph_action
    - Agent state queries and filtering
    
    Uses MANDATORY LTMC tools:
    - memory_action (Tool 1): State initialization and storage
    - graph_action (Tool 8): Coordination relationship management
    """
    
    def __init__(self, coordination_id: str, conversation_id: str):
        """
        Initialize core state management with LTMC integration.
        
        Args:
            coordination_id: Unique coordination session identifier
            conversation_id: LTMC conversation context identifier
        """
        self.coordination_id = coordination_id
        self.conversation_id = conversation_id
        
        # Core state storage
        self.agent_states: Dict[str, StateSnapshot] = {}
        
        # Initialize LTMC storage and graph relationships
        self._initialize_state_storage()
    
    def _initialize_state_storage(self) -> None:
        """
        Initialize LTMC storage for state management.
        
        Uses MANDATORY LTMC tools:
        - memory_action (Tool 1): Store initialization record
        - graph_action (Tool 8): Create coordination relationships
        """
        try:
            # Create state management initialization record
            init_doc = {
                "state_management": "initialized",
                "coordination_id": self.coordination_id,
                "conversation_id": self.conversation_id,
                "initialization_time": datetime.now(timezone.utc).isoformat(),
                "framework_version": "1.0.0"
            }
            
            # Store initialization in LTMC memory (Tool 1) - MANDATORY
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic file name based on state manager initialization context and version
            initialization_timestamp = init_doc["initialization_time"].replace(':', '_').replace('-', '_')
            framework_version = init_doc["framework_version"].replace('.', '_')
            dynamic_state_manager_init_file_name = f"state_manager_init_{self.coordination_id}_v{framework_version}_{initialization_timestamp}.json"
            
            memory_action(
                action="store",
                file_name=dynamic_state_manager_init_file_name,
                content=json.dumps(init_doc, indent=2),
                tags=["state_management", "initialization", self.coordination_id],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Create knowledge graph entity for state management (Tool 8) - MANDATORY
            graph_action(
                action="link",
                source_entity=f"coordination_{self.coordination_id}",
                target_entity=f"state_manager_{self.coordination_id}",
                relationship="uses_state_manager",
                properties={"initialization_time": init_doc["initialization_time"]}
            )
            
            print(f"✅ LTMC state management initialized for coordination: {self.coordination_id}")
            
        except Exception as e:
            print(f"❌ Failed to initialize state storage: {e}")
            raise
    
    def get_agent_state(self, agent_id: str) -> Optional[StateSnapshot]:
        """
        Get current state snapshot for a specific agent.
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            Optional[StateSnapshot]: Current state snapshot or None if not found
        """
        return self.agent_states.get(agent_id)
    
    def get_all_agent_states(self) -> Dict[str, StateSnapshot]:
        """
        Get all current agent states.
        
        Returns:
            Dict[str, StateSnapshot]: Copy of all current agent state snapshots
        """
        return self.agent_states.copy()
    
    def get_agents_by_status(self, status: AgentStatus) -> List[str]:
        """
        Get list of agent IDs with specific status.
        
        Args:
            status: Target agent status to filter by
            
        Returns:
            List[str]: List of agent IDs matching the specified status
        """
        return [
            agent_id for agent_id, snapshot in self.agent_states.items()
            if snapshot.status == status
        ]