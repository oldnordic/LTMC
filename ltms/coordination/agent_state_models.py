"""
LTMC Agent State Models
Core data structures for agent state management and transitions.

Extracted from agent_state_manager.py for smart modularization (300-line limit compliance).
Contains the foundational data models used throughout the coordination framework.

Components:
- StateTransition: Enum defining valid agent state transitions
- StateSnapshot: Point-in-time snapshot of agent state  
- StateTransitionLog: Log entry for state transitions with full audit trail
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Import coordination framework types
from .agent_coordination_models import AgentStatus


class StateTransition(Enum):
    """
    Valid agent state transitions for coordination framework.
    
    Defines the allowed transition types that agents can undergo
    during their lifecycle within the coordination framework.
    """
    INITIALIZE = "initialize"
    ACTIVATE = "activate"
    PAUSE = "pause"
    RESUME = "resume"
    COMPLETE = "complete"
    FAIL = "fail"
    HANDOFF = "handoff"
    RETRY = "retry"


@dataclass
class StateSnapshot:
    """
    Point-in-time snapshot of agent state.
    
    Captures the complete state of an agent at a specific moment,
    including status, data, and metadata. Used for state persistence
    and recovery mechanisms.
    
    Attributes:
        agent_id: Unique identifier for the agent
        status: Current AgentStatus enum value
        state_data: Agent-specific state information
        timestamp: ISO timestamp of snapshot creation
        task_id: ID of the coordination task
        conversation_id: ID of the conversation context
        snapshot_id: Unique identifier for this snapshot (auto-generated)
        metadata: Additional metadata dictionary (optional)
    """
    agent_id: str
    status: AgentStatus
    state_data: Dict[str, Any]
    timestamp: str
    task_id: str
    conversation_id: str
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateTransitionLog:
    """
    Log entry for agent state transitions with full audit trail.
    
    Records all state changes for debugging, monitoring, and compliance.
    Includes transition details, success/failure status, and contextual data.
    
    Attributes:
        agent_id: Agent that underwent transition
        from_status: Previous AgentStatus
        to_status: New AgentStatus
        transition_type: StateTransition enum describing transition
        timestamp: ISO timestamp of transition
        success: Whether transition completed successfully
        error_message: Error details if transition failed (optional)
        transition_data: Additional transition context (optional)
        log_id: Unique identifier for this log entry (auto-generated)
    """
    agent_id: str
    from_status: AgentStatus
    to_status: AgentStatus
    transition_type: StateTransition
    timestamp: str
    success: bool
    error_message: Optional[str] = None
    transition_data: Dict[str, Any] = field(default_factory=dict)
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))