"""
Agent State Operations  
State creation and transitions with comprehensive LTMC tools integration.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Handles create_agent_state and transition_agent_state with memory_action and graph_action.

Components:
- AgentStateOperations: State creation and transitions with ALL LTMC tools integration
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Import coordination models
from .agent_coordination_models import AgentStatus
from .agent_state_models import StateTransition, StateSnapshot

# Import LTMC tools - MANDATORY
from ltms.tools.memory.memory_actions import memory_action      # Tool 1 - Memory operations - MANDATORY
from ltms.tools.graph.graph_actions import graph_action        # Tool 8 - Knowledge graph - MANDATORY


class AgentStateOperations:
    """
    Agent state operations with comprehensive LTMC integration.
    
    Handles core state operations:
    - Agent state creation with validation and storage
    - State transitions with validation and logging
    - LTMC memory persistence with memory_action
    - Knowledge graph updates with graph_action
    - Performance metrics tracking
    
    Uses MANDATORY LTMC tools:
    - memory_action (Tool 1): State and transition storage
    - graph_action (Tool 8): State relationship management
    """
    
    def __init__(self, core, validator, logging):
        """
        Initialize state operations with dependencies.
        
        Args:
            core: AgentStateCore instance for state storage
            validator: AgentStateValidator for validation logic
            logging: AgentStateLogging for transition logging
        """
        self.core = core
        self.validator = validator
        self.logging = logging
        
        # Performance metrics tracking
        self.performance_metrics = {
            "state_transitions": 0,
            "validation_errors": 0,
            "average_transition_time": 0.0
        }
        
        # Observer for state change notifications
        self.observer = None
    
    def create_agent_state(self, 
                          agent_id: str,
                          initial_status: AgentStatus,
                          state_data: Dict[str, Any]) -> bool:
        """
        Create initial state for an agent with LTMC integration.
        
        Uses MANDATORY LTMC tools for complete state creation:
        - Validates state data structure
        - Creates StateSnapshot with metadata
        - Stores in LTMC memory with memory_action
        - Creates knowledge graph relationships with graph_action
        
        Args:
            agent_id: Unique agent identifier
            initial_status: Starting agent status
            state_data: Initial state data
            
        Returns:
            bool: True if state created successfully
        """
        try:
            # Validate state data structure
            is_valid, error_msg = self.validator.validate_state_data(state_data)
            if not is_valid:
                print(f"❌ Invalid state data for {agent_id}: {error_msg}")
                return False
            
            # Create comprehensive state snapshot
            snapshot = StateSnapshot(
                agent_id=agent_id,
                status=initial_status,
                state_data=state_data.copy(),
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_id=self.core.coordination_id,
                conversation_id=self.core.conversation_id,
                metadata={
                    "created_by": "state_manager",
                    "version": "1.0"
                }
            )
            
            # Store in core state storage
            self.core.agent_states[agent_id] = snapshot
            
            # Prepare state document for LTMC storage
            state_doc = {
                "action": "create_agent_state",
                "agent_id": agent_id,
                "snapshot": {
                    "agent_id": snapshot.agent_id,
                    "status": snapshot.status.value,
                    "state_data": snapshot.state_data,
                    "timestamp": snapshot.timestamp,
                    "task_id": snapshot.task_id,
                    "conversation_id": snapshot.conversation_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "metadata": snapshot.metadata
                }
            }
            
            # Store in LTMC memory (Tool 1) - MANDATORY
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic file name based on agent state creation context and status
            state_timestamp = snapshot.timestamp.replace(':', '_').replace('-', '_')
            dynamic_agent_state_file_name = f"agent_state_create_{agent_id}_{initial_status.value.lower()}_{snapshot.snapshot_id}_{state_timestamp}.json"
            
            memory_action(
                action="store",
                file_name=dynamic_agent_state_file_name,
                content=json.dumps(state_doc, indent=2),
                tags=["agent_state", agent_id, initial_status.value, self.core.coordination_id],
                conversation_id=self.core.conversation_id,
                role="system"
            )
            
            # Create knowledge graph relationship (Tool 8) - MANDATORY
            graph_action(
                action="link",
                source_entity=f"state_manager_{self.core.coordination_id}",
                target_entity=f"agent_{agent_id}",
                relationship="manages_state",
                properties={
                    "initial_status": initial_status.value,
                    "creation_time": snapshot.timestamp
                }
            )
            
            print(f"✅ Agent state created: {agent_id} [{initial_status.value}]")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create agent state for {agent_id}: {e}")
            return False
    
    def transition_agent_state(self,
                              agent_id: str,
                              new_status: AgentStatus,
                              transition_type: StateTransition,
                              transition_data: Dict[str, Any] = None) -> bool:
        """
        Transition agent to new state with comprehensive LTMC integration.
        
        Uses MANDATORY LTMC tools for complete state transition:
        - Validates transition legality
        - Creates new StateSnapshot with transition metadata
        - Stores transition in LTMC memory with memory_action
        - Updates knowledge graph with graph_action
        - Tracks performance metrics and notifies observers
        
        Args:
            agent_id: Agent to transition
            new_status: Target status
            transition_type: Type of transition
            transition_data: Optional transition-specific data
            
        Returns:
            bool: True if transition successful
        """
        start_time = time.time()
        
        try:
            # Check if agent exists in core storage
            if agent_id not in self.core.agent_states:
                print(f"❌ Agent {agent_id} not found in state manager")
                return False
            
            current_snapshot = self.core.agent_states[agent_id]
            current_status = current_snapshot.status
            
            # Validate transition legality
            if not self.validator.validate_transition(current_status, new_status):
                error_msg = f"Invalid transition: {current_status.value} → {new_status.value}"
                print(f"❌ {error_msg}")
                
                # Log failed transition
                self.logging.log_transition(
                    agent_id, current_status, new_status, 
                    transition_type, False, error_msg, transition_data
                )
                
                self.performance_metrics["validation_errors"] += 1
                return False
            
            # Create new state snapshot with transition data
            new_state_data = current_snapshot.state_data.copy()
            if transition_data:
                new_state_data.update(transition_data.get("state_updates", {}))
            
            new_snapshot = StateSnapshot(
                agent_id=agent_id,
                status=new_status,
                state_data=new_state_data,
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_id=self.core.coordination_id,
                conversation_id=self.core.conversation_id,
                metadata={
                    "previous_snapshot": current_snapshot.snapshot_id,
                    "transition_type": transition_type.value,
                    "updated_by": "state_manager"
                }
            )
            
            # Update core state storage
            self.core.agent_states[agent_id] = new_snapshot
            
            # Prepare transition document for LTMC storage
            transition_doc = {
                "action": "state_transition",
                "agent_id": agent_id,
                "from_status": current_status.value,
                "to_status": new_status.value,
                "transition_type": transition_type.value,
                "new_snapshot": {
                    "agent_id": new_snapshot.agent_id,
                    "status": new_snapshot.status.value,
                    "state_data": new_snapshot.state_data,
                    "timestamp": new_snapshot.timestamp,
                    "task_id": new_snapshot.task_id,
                    "conversation_id": new_snapshot.conversation_id,
                    "snapshot_id": new_snapshot.snapshot_id,
                    "metadata": new_snapshot.metadata
                },
                "transition_data": transition_data or {}
            }
            
            # Store transition in LTMC memory (Tool 1) - MANDATORY
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic file name based on state transition context and type
            transition_timestamp = new_snapshot.timestamp.replace(':', '_').replace('-', '_')
            dynamic_transition_file_name = f"state_transition_{agent_id}_{current_status.value.lower()}_to_{new_status.value.lower()}_{transition_type.value.lower()}_{new_snapshot.snapshot_id}_{transition_timestamp}.json"
            
            memory_action(
                action="store",
                file_name=dynamic_transition_file_name,
                content=json.dumps(transition_doc, indent=2),
                tags=["state_transition", agent_id, new_status.value, transition_type.value, self.core.coordination_id],
                conversation_id=self.core.conversation_id,
                role="system"
            )
            
            # Update knowledge graph relationship (Tool 8) - MANDATORY
            graph_action(
                action="link",
                source_entity=f"agent_{agent_id}",
                target_entity=f"state_{new_status.value}",
                relationship="transitions_to",
                properties={
                    "transition_time": new_snapshot.timestamp,
                    "transition_type": transition_type.value
                }
            )
            
            # Log successful transition
            self.logging.log_transition(
                agent_id, current_status, new_status,
                transition_type, True, None, transition_data
            )
            
            # Update performance metrics
            transition_time = time.time() - start_time
            self.performance_metrics["state_transitions"] += 1
            self.performance_metrics["average_transition_time"] = (
                (self.performance_metrics["average_transition_time"] * (self.performance_metrics["state_transitions"] - 1) + transition_time) /
                self.performance_metrics["state_transitions"]
            )
            
            # Notify observers if available
            if self.observer:
                self.observer.notify_observers(agent_id, current_status, new_status)
            
            print(f"✅ State transition: {agent_id} [{current_status.value}] → [{new_status.value}]")
            return True
            
        except Exception as e:
            print(f"❌ Failed state transition for {agent_id}: {e}")
            # Log exception in transition history
            self.logging.log_transition(
                agent_id, current_snapshot.status, new_status,
                transition_type, False, str(e), transition_data
            )
            return False