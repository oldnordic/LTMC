"""
LTMC Agent Coordination Models
Data models and core structures for agent coordination framework.

Extracted from agent_coordination_framework.py for smart modularization (300-line limit compliance).
Contains enums, TypedDict, and dataclasses for coordination system.

Components:
- AgentStatus: Enum for agent operational states
- CoordinationState: TypedDict for shared coordination state  
- AgentMessage: Dataclass for inter-agent communication
- AgentRegistration: Dataclass for agent registry information
"""

import operator
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from dataclasses import dataclass
from enum import Enum


class AgentStatus(Enum):
    """
    Agent operational states for coordination framework.
    
    Defines the complete lifecycle states that agents can be in
    during coordination processes.
    """
    INITIALIZING = "initializing"
    ACTIVE = "active"
    WAITING = "waiting" 
    COMPLETED = "completed"
    ERROR = "error"
    HANDOFF = "handoff"


class CoordinationState(TypedDict):
    """
    Shared state structure for multi-agent coordination.
    
    Defines the complete state information shared across all agents
    in a coordination session, including task tracking, agent status,
    and shared context information.
    """
    task_id: str
    conversation_id: str
    primary_task: str
    active_agents: Annotated[List[str], operator.add]
    agent_findings: Annotated[List[Dict[str, Any]], operator.add]
    shared_context: Dict[str, Any]
    current_agent: Optional[str]
    next_agent: Optional[str]
    completion_status: Dict[str, bool]
    coordination_metadata: Dict[str, Any]


@dataclass
class AgentMessage:
    """
    Standardized inter-agent communication message.
    
    Provides structured format for all communication between agents
    in the coordination framework, supporting both point-to-point
    and broadcast messaging patterns.
    """
    sender_agent: str
    recipient_agent: Optional[str]  # None for broadcast messages
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    conversation_id: str
    task_id: str
    requires_response: bool = False


@dataclass 
class AgentRegistration:
    """
    Agent registration information for coordination registry.
    
    Contains complete registration details for agents participating
    in coordination, including capabilities, dependencies, and
    operational tracking information.
    """
    agent_id: str
    agent_type: str
    status: AgentStatus
    task_scope: List[str]
    dependencies: List[str]
    outputs: List[str]
    start_time: str
    last_activity: str
    conversation_id: str
    task_id: str