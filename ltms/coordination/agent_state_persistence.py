"""
LTMC Agent State Persistence System
Checkpoint and restore functionality for agent states using LTMC memory system.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Provides persistent storage and recovery capabilities for the agent coordination framework.

Components:
- AgentStatePersistence: Handles checkpoint creation and state restoration
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# LTMC MCP tool imports
from ltms.tools.consolidated import memory_action

# Import state models
from .agent_state_models import StateSnapshot
from .agent_coordination_models import AgentStatus


class AgentStatePersistence:
    """
    Agent state persistence system using LTMC memory storage.
    
    Provides checkpoint and restore functionality for agent coordination framework:
    - Creates comprehensive checkpoints of all agent states
    - Stores checkpoints in LTMC memory with structured metadata
    - Restores agent states from checkpoints for recovery scenarios
    - Maintains data integrity and handles partial restoration failures
    
    Used by LTMCAgentStateManager for state persistence and recovery operations.
    """
    
    def __init__(self, coordination_id: str, conversation_id: str):
        """
        Initialize agent state persistence system.
        
        Args:
            coordination_id: Unique identifier for the coordination session
            conversation_id: Conversation context identifier for LTMC storage
        """
        self.coordination_id = coordination_id
        self.conversation_id = conversation_id
    
    def persist_state_checkpoint(self, 
                                agent_states: Dict[str, StateSnapshot], 
                                performance_metrics: Dict[str, Any]) -> bool:
        """
        Create checkpoint of all agent states in LTMC.
        
        Creates a comprehensive checkpoint containing all current agent states,
        performance metrics, and metadata. Stores in LTMC memory system with
        structured JSON format for reliable restoration.
        
        Args:
            agent_states: Dictionary mapping agent_id to StateSnapshot
            performance_metrics: Current performance metrics dictionary
            
        Returns:
            bool: True if checkpoint created successfully, False otherwise
            
        Example:
            >>> agent_states = {"agent1": snapshot1, "agent2": snapshot2}
            >>> metrics = {"transitions": 5, "errors": 0}
            >>> success = persistence.persist_state_checkpoint(agent_states, metrics)
            >>> print(f"Checkpoint: {'SUCCESS' if success else 'FAILED'}")
        """
        try:
            # Create comprehensive checkpoint data structure
            checkpoint_data = {
                "checkpoint_action": "state_checkpoint",
                "coordination_id": self.coordination_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_agents": len(agent_states),
                "agent_states": {
                    agent_id: {
                        "agent_id": snapshot.agent_id,
                        "status": snapshot.status.value,
                        "state_data": snapshot.state_data,
                        "timestamp": snapshot.timestamp,
                        "task_id": snapshot.task_id,
                        "conversation_id": snapshot.conversation_id,
                        "snapshot_id": snapshot.snapshot_id,
                        "metadata": snapshot.metadata
                    }
                    for agent_id, snapshot in agent_states.items()
                },
                "performance_metrics": performance_metrics,
                "checkpoint_id": str(uuid.uuid4())
            }
            
            # Store checkpoint in LTMC memory
            result = memory_action(
                action="store",
                file_name=f"state_checkpoint_{self.coordination_id}_{int(time.time())}.json",
                content=json.dumps(checkpoint_data, indent=2),
                tags=["state_checkpoint", self.coordination_id, "checkpoint"],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            if result.get('success'):
                print(f"✅ State checkpoint created for {len(agent_states)} agents")
                return True
            else:
                print(f"❌ Failed to store checkpoint: {result.get('error', 'Unknown error')}")
                return False
            
        except Exception as e:
            print(f"❌ Failed to create state checkpoint: {e}")
            return False
    
    def restore_from_checkpoint(self, checkpoint_timestamp: str) -> Optional[Dict[str, StateSnapshot]]:
        """
        Restore agent states from LTMC checkpoint.
        
        Queries LTMC memory for checkpoint data and reconstructs StateSnapshot
        objects for all agents. Handles partial restoration scenarios gracefully
        by returning successfully restored states and logging failures.
        
        Args:
            checkpoint_timestamp: Timestamp identifier for checkpoint (currently uses most recent)
            
        Returns:
            Optional[Dict[str, StateSnapshot]]: Dictionary of restored agent states,
            or None if restoration failed completely. May contain partial results
            if some agents failed to restore.
            
        Example:
            >>> restored = persistence.restore_from_checkpoint("2025-08-24T10:30:00Z")
            >>> if restored:
            ...     print(f"Restored {len(restored)} agents")
            ...     for agent_id, snapshot in restored.items():
            ...         print(f"  {agent_id}: {snapshot.status.value}")
        """
        try:
            # Query LTMC for checkpoint documents
            result = memory_action(
                action="retrieve",
                query=f"state_checkpoint coordination_id:{self.coordination_id}",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            if not result.get('success') or not result.get('documents'):
                print("❌ No checkpoints found")
                return None
            
            # Use most recent checkpoint (simplified - could implement proper timestamp matching)
            checkpoint_doc = result['documents'][0]
            checkpoint_data = json.loads(checkpoint_doc['content'])
            
            # Restore agent states from checkpoint data
            restored_states = {}
            restored_count = 0
            failed_count = 0
            
            for agent_id, state_data in checkpoint_data['agent_states'].items():
                try:
                    # Convert status string back to enum
                    status_value = state_data['status']
                    agent_status = None
                    for status in AgentStatus:
                        if status.value == status_value:
                            agent_status = status
                            break
                    
                    if agent_status is None:
                        raise ValueError(f"Unknown agent status: {status_value}")
                    
                    # Create StateSnapshot with restored status enum
                    restored_snapshot = StateSnapshot(
                        agent_id=state_data['agent_id'],
                        status=agent_status,
                        state_data=state_data['state_data'],
                        timestamp=state_data['timestamp'],
                        task_id=state_data['task_id'],
                        conversation_id=state_data['conversation_id'],
                        snapshot_id=state_data['snapshot_id'],
                        metadata=state_data['metadata']
                    )
                    
                    restored_states[agent_id] = restored_snapshot
                    restored_count += 1
                    
                except Exception as restore_error:
                    print(f"⚠️ Failed to restore state for {agent_id}: {restore_error}")
                    failed_count += 1
            
            if restored_count > 0:
                print(f"✅ Restored {restored_count} agent states from checkpoint")
                if failed_count > 0:
                    print(f"⚠️ {failed_count} agents failed to restore")
                return restored_states
            else:
                print("❌ No agents could be restored from checkpoint")
                return None
            
        except json.JSONDecodeError as json_error:
            print(f"❌ Failed to parse checkpoint JSON: {json_error}")
            return None
        except Exception as e:
            print(f"❌ Failed to restore from checkpoint: {e}")
            return None