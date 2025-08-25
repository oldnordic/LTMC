"""
Coordination Core State Management
Core coordination state initialization and management.

Extracted from agent_coordination_core.py for 300-line limit compliance.
Handles coordination state setup and LTMC storage initialization.

Components:
- CoordinationCoreState: Core state management with LTMC integration
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Optional

# Import coordination models
from .agent_coordination_models import CoordinationState

# LTMC MCP tool imports for real functionality
from ltms.tools.consolidated import memory_action


class CoordinationCoreState:
    """
    Core coordination state management with LTMC integration.
    
    Handles core coordination operations:
    - Coordination state initialization and management
    - LTMC memory storage setup for coordination persistence
    - Task and conversation ID management
    - Coordination metadata tracking
    
    Uses MANDATORY LTMC tools:
    - memory_action (Tool 1): Coordination storage and persistence
    """
    
    def __init__(self, task_description: str, coordination_id: Optional[str] = None):
        """
        Initialize coordination core state.
        
        Args:
            task_description: Description of coordination task
            coordination_id: Optional custom coordination ID
        """
        self.task_id = coordination_id or f"coordination_{int(time.time())}"
        self.conversation_id = f"agent_coord_{self.task_id}"
        self.task_description = task_description
        
        # Initialize coordination state
        self.state: CoordinationState = {
            "task_id": self.task_id,
            "conversation_id": self.conversation_id,
            "primary_task": task_description,
            "active_agents": [],
            "agent_findings": [],
            "shared_context": {},
            "current_agent": None,
            "next_agent": None,  
            "completion_status": {},
            "coordination_metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "framework_version": "1.0.0"
            }
        }
        
        # Initialize LTMC storage for coordination
        self._initialize_coordination_storage()
    
    def _initialize_coordination_storage(self) -> None:
        """
        Initialize LTMC memory storage for agent coordination.
        
        Sets up persistent storage for coordination state and metadata
        using LTMC memory_action tool for real functionality.
        
        Uses MANDATORY LTMC tools:
        - memory_action for coordination storage initialization
        """
        try:
            # Store initial coordination state
            coordination_doc = {
                "framework": "LTMC Agent Coordination",
                "task_id": self.task_id,
                "task_description": self.task_description,
                "initialization": "success",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Use actual LTMC memory_action tool (Tool 1) - MANDATORY
            memory_action(
                action="store",
                file_name=f"coordination_init_{self.task_id}.md",
                content=f"# Agent Coordination Initialized\n\n{json.dumps(coordination_doc, indent=2)}",
                tags=["coordination", "initialization", self.task_id],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            print(f"✅ LTMC coordination storage initialized for task: {self.task_id}")
            
        except Exception as e:
            print(f"❌ Failed to initialize LTMC coordination storage: {e}")
            raise
    
    def update_coordination_state(self, key: str, value: any) -> None:
        """
        Update coordination state with new values.
        
        Args:
            key: State key to update
            value: New value for the key
        """
        if key in self.state:
            self.state[key] = value
            print(f"✅ Coordination state updated: {key}")
        else:
            print(f"⚠️ Unknown coordination state key: {key}")
    
    def add_active_agent(self, agent_id: str) -> None:
        """
        Add agent to active agents list.
        
        Args:
            agent_id: Agent ID to add to active list
        """
        if agent_id not in self.state["active_agents"]:
            self.state["active_agents"].append(agent_id)
            print(f"✅ Agent {agent_id} added to active agents")
    
    def set_current_agent(self, agent_id: str) -> None:
        """
        Set current active agent in coordination state.
        
        Args:
            agent_id: Agent ID to set as current
        """
        self.state["current_agent"] = agent_id
        print(f"✅ Current agent set to: {agent_id}")
    
    def add_agent_finding(self, finding: Dict) -> None:
        """
        Add agent finding to coordination state.
        
        Args:
            finding: Agent finding data to store
        """
        self.state["agent_findings"].append(finding)
        print(f"✅ Agent finding added (total: {len(self.state['agent_findings'])})")
    
    def get_coordination_state(self) -> CoordinationState:
        """
        Get complete coordination state.
        
        Returns:
            CoordinationState: Current coordination state
        """
        return self.state.copy()
    
    def get_task_info(self) -> Dict[str, str]:
        """
        Get basic task information.
        
        Returns:
            Dict containing task_id, conversation_id, and task_description
        """
        return {
            "task_id": self.task_id,
            "conversation_id": self.conversation_id,
            "task_description": self.task_description
        }