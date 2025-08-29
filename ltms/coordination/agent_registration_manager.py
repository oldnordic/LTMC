"""
LTMC Agent Registration Manager
Agent registration and status management for coordination framework.

Extracted from agent_coordination_framework.py for smart modularization (300-line limit compliance).
Handles agent lifecycle management including registration, status updates, and registry maintenance.

Components:
- AgentRegistrationManager: Complete agent registration and status management
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Import coordination models
from .agent_coordination_models import AgentStatus, AgentRegistration

# LTMC MCP tool imports for real functionality
from ltms.tools.memory.memory_actions import memory_action
from ltms.tools.graph.graph_actions import graph_action


class AgentRegistrationManager:
    """
    Agent registration and status management for coordination framework.
    
    Provides comprehensive management of agent lifecycle including:
    - Agent registration and deregistration
    - Status tracking and updates
    - LTMC storage integration for persistence
    - Agent registry maintenance and queries
    - Dependency tracking and validation
    
    Used by coordination framework for complete agent lifecycle management.
    """
    
    def __init__(self, task_id: str, conversation_id: str):
        """
        Initialize agent registration manager.
        
        Args:
            task_id: Unique identifier for coordination task
            conversation_id: Unique identifier for coordination conversation
        """
        self.task_id = task_id
        self.conversation_id = conversation_id
        self.agent_registry: Dict[str, AgentRegistration] = {}
    
    def register_agent(self, 
                      agent_id: str,
                      agent_type: str, 
                      task_scope: List[str],
                      dependencies: Optional[List[str]] = None,
                      outputs: Optional[List[str]] = None) -> bool:
        """
        Register an agent with the coordination framework.
        
        Creates complete agent registration with LTMC storage integration
        for persistence and graph relationship management.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (e.g., 'ltmc-architectural-planner')  
            task_scope: List of tasks this agent will handle
            dependencies: List of other agents this agent depends on
            outputs: List of outputs this agent will produce
        
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            registration = AgentRegistration(
                agent_id=agent_id,
                agent_type=agent_type,
                status=AgentStatus.INITIALIZING,
                task_scope=task_scope or [],
                dependencies=dependencies or [],
                outputs=outputs or [],
                start_time=datetime.now(timezone.utc).isoformat(),
                last_activity=datetime.now(timezone.utc).isoformat(),
                conversation_id=self.conversation_id,
                task_id=self.task_id
            )
            
            self.agent_registry[agent_id] = registration
            
            # Store registration in LTMC
            registration_doc = {
                "action": "agent_registration",
                "agent_id": agent_id,
                "agent_type": agent_type,
                "registration_data": {
                    "agent_id": registration.agent_id,
                    "agent_type": registration.agent_type,
                    "status": registration.status.value,
                    "task_scope": registration.task_scope,
                    "dependencies": registration.dependencies,
                    "outputs": registration.outputs,
                    "start_time": registration.start_time,
                    "last_activity": registration.last_activity,
                    "conversation_id": registration.conversation_id,
                    "task_id": registration.task_id
                }
            }
            
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic file name based on agent registration context and capabilities
            start_timestamp = registration.start_time.replace(':', '_').replace('-', '_')
            task_count = len(registration.task_scope)
            dependency_count = len(registration.dependencies)
            output_count = len(registration.outputs)
            agent_type_clean = agent_type.replace('-', '_').replace(' ', '_').lower()
            dynamic_registration_file_name = f"agent_registration_{agent_id}_{agent_type_clean}_task{self.task_id}_{task_count}tasks_{dependency_count}deps_{output_count}outputs_{start_timestamp}.md"
            
            memory_action(
                action="store",
                file_name=dynamic_registration_file_name,
                content=f"# Agent Registration: {agent_id}\n\n{json.dumps(registration_doc, indent=2)}",
                tags=["agent_registration", agent_id, self.task_id],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Create graph relationship for agent coordination
            graph_action(
                action="link",
                source_entity=f"coordination_task_{self.task_id}",
                target_entity=f"agent_{agent_id}",
                relationship="manages",
                properties={"agent_type": agent_type, "registration_time": registration.start_time}
            )
            
            print(f"✅ Agent {agent_id} registered successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register agent {agent_id}: {e}")
            return False
    
    def update_agent_status(self, agent_id: str, status: AgentStatus, findings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update agent status and optionally store findings.
        
        Updates agent status with LTMC integration for persistence
        and optional findings storage for coordination tracking.
        
        Args:
            agent_id: Agent ID to update
            status: New agent status
            findings: Optional findings to store
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            if agent_id not in self.agent_registry:
                raise ValueError(f"Agent {agent_id} not registered")
            
            # Update registry
            self.agent_registry[agent_id].status = status
            self.agent_registry[agent_id].last_activity = datetime.now(timezone.utc).isoformat()
            
            # Store status update in LTMC
            status_doc = {
                "action": "status_update",
                "agent_id": agent_id,
                "new_status": status.value,
                "timestamp": self.agent_registry[agent_id].last_activity,
                "findings": findings
            }
            
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic file name based on agent status update context and activity timestamp
            activity_timestamp = self.agent_registry[agent_id].last_activity.replace(':', '_').replace('-', '_')
            status_value_clean = status.value.lower()
            has_findings = "with_findings" if findings else "no_findings"
            dynamic_status_file_name = f"agent_status_{agent_id}_{status_value_clean}_task{self.task_id}_{has_findings}_{activity_timestamp}.md"
            
            memory_action(
                action="store",
                file_name=dynamic_status_file_name, 
                content=f"# Agent Status Update: {agent_id}\n\n{json.dumps(status_doc, indent=2)}",
                tags=["agent_status", agent_id, status.value, self.task_id],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Store findings if provided
            if findings:
                # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
                # Generate dynamic file name based on agent findings context and data structure
                findings_timestamp = datetime.now(timezone.utc).isoformat().replace(':', '_').replace('-', '_')
                findings_keys = list(findings.keys())[:3] if isinstance(findings, dict) else []
                findings_summary = '_'.join(findings_keys).lower() if findings_keys else 'data'
                findings_count = len(findings) if isinstance(findings, (dict, list)) else 1
                dynamic_findings_file_name = f"agent_findings_{agent_id}_task{self.task_id}_{findings_summary}_{findings_count}items_{findings_timestamp}.md"
                
                memory_action(
                    action="store",
                    file_name=dynamic_findings_file_name,
                    content=f"# Agent Findings: {agent_id}\n\n{json.dumps(findings, indent=2)}",
                    tags=["agent_findings", agent_id, self.task_id],
                    conversation_id=self.conversation_id,
                    role="system"
                )
            
            print(f"✅ Agent {agent_id} status updated to {status.value}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update agent status: {e}")
            return False
    
    def get_agent_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """
        Get agent registration information.
        
        Args:
            agent_id: Agent ID to retrieve registration for
            
        Returns:
            AgentRegistration if found, None otherwise
        """
        return self.agent_registry.get(agent_id)
    
    def get_all_registrations(self) -> Dict[str, AgentRegistration]:
        """
        Get all agent registrations.
        
        Returns:
            Dictionary of all agent registrations
        """
        return self.agent_registry.copy()
    
    def get_active_agents(self) -> Dict[str, AgentRegistration]:
        """
        Get only currently active agents.
        
        Returns:
            Dictionary of active agent registrations
        """
        return {
            agent_id: registration
            for agent_id, registration in self.agent_registry.items()
            if registration.status == AgentStatus.ACTIVE
        }
    
    def get_agents_by_status(self, status: AgentStatus) -> Dict[str, AgentRegistration]:
        """
        Get agents filtered by specific status.
        
        Args:
            status: AgentStatus to filter by
            
        Returns:
            Dictionary of agent registrations with specified status
        """
        return {
            agent_id: registration
            for agent_id, registration in self.agent_registry.items()
            if registration.status == status
        }
    
    def get_agents_by_type(self, agent_type: str) -> Dict[str, AgentRegistration]:
        """
        Get agents filtered by type.
        
        Args:
            agent_type: Agent type to filter by
            
        Returns:
            Dictionary of agent registrations with specified type
        """
        return {
            agent_id: registration
            for agent_id, registration in self.agent_registry.items()
            if registration.agent_type == agent_type
        }
    
    def get_registration_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of all registrations.
        
        Returns:
            Dictionary containing registration statistics and summaries
        """
        total_agents = len(self.agent_registry)
        status_counts = {}
        type_counts = {}
        
        for registration in self.agent_registry.values():
            # Count by status
            status_value = registration.status.value
            status_counts[status_value] = status_counts.get(status_value, 0) + 1
            
            # Count by type
            agent_type = registration.agent_type
            type_counts[agent_type] = type_counts.get(agent_type, 0) + 1
        
        return {
            "task_id": self.task_id,
            "conversation_id": self.conversation_id,
            "total_agents": total_agents,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "active_agent_ids": [
                agent_id for agent_id, reg in self.agent_registry.items()
                if reg.status == AgentStatus.ACTIVE
            ],
            "completed_agent_ids": [
                agent_id for agent_id, reg in self.agent_registry.items()
                if reg.status == AgentStatus.COMPLETED
            ]
        }