"""
Coordination Agent Operations
Agent registration, messaging, and handoff operations.

Extracted from agent_coordination_core.py for 300-line limit compliance.
Handles all agent-related coordination operations.

Components:
- CoordinationAgentOperations: Agent operations with LTMC graph integration
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Import coordination models
from .agent_coordination_models import AgentStatus, AgentMessage

# Import modular components
from .agent_registration_manager import AgentRegistrationManager
from .agent_message_handler import AgentMessageHandler

# LTMC MCP tool imports for real functionality
from ltms.tools.consolidated import graph_action


class CoordinationAgentOperations:
    """
    Agent operations management with comprehensive LTMC integration.
    
    Handles agent operation coordination:
    - Agent registration and status management via AgentRegistrationManager
    - Inter-agent communication via AgentMessageHandler
    - Agent handoff and workflow orchestration
    - LTMC graph relationships for agent coordination tracking
    
    Uses MANDATORY LTMC tools:
    - graph_action (Tool 8): Agent relationship tracking and handoff mapping
    """
    
    def __init__(self, task_id: str, conversation_id: str):
        """
        Initialize agent operations coordinator.
        
        Args:
            task_id: Task identifier for coordination context
            conversation_id: Conversation context identifier
        """
        self.task_id = task_id
        self.conversation_id = conversation_id
        
        # Initialize integrated components
        self.registration_manager = AgentRegistrationManager(task_id, conversation_id)
        self.message_handler = AgentMessageHandler(task_id, conversation_id)
    
    def register_agent(self, 
                      agent_id: str,
                      agent_type: str, 
                      task_scope: List[str],
                      dependencies: List[str] = None,
                      outputs: List[str] = None) -> bool:
        """
        Register an agent with the coordination framework.
        
        Delegates to AgentRegistrationManager for agent registration.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (e.g., 'ltmc-architectural-planner')  
            task_scope: List of tasks this agent will handle
            dependencies: List of other agents this agent depends on
            outputs: List of outputs this agent will produce
        
        Returns:
            bool: True if registration successful
        """
        try:
            # Use registration manager for agent registration
            success = self.registration_manager.register_agent(
                agent_id, agent_type, task_scope, dependencies, outputs
            )
            
            if success:
                print(f"✅ Agent {agent_id} registered successfully in operations")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to register agent {agent_id} in operations: {e}")
            return False
    
    def send_agent_message(self, message: AgentMessage) -> bool:
        """
        Send message between agents using integrated message handler.
        
        Args:
            message: AgentMessage to send
            
        Returns:
            bool: True if message sent successfully
        """
        try:
            # Get registered agents from registration manager
            registered_agents = set(self.registration_manager.get_all_registrations().keys())
            
            # Use message handler for message sending
            success = self.message_handler.send_agent_message(message, registered_agents)
            
            if success:
                # Update last activity for sender
                self.registration_manager.update_agent_status(
                    message.sender_agent, 
                    self.registration_manager.get_agent_registration(message.sender_agent).status
                )
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to send agent message in operations: {e}")
            return False
    
    def retrieve_agent_messages(self, agent_id: str, since_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve messages for a specific agent using integrated message handler.
        
        Args:
            agent_id: Agent ID to retrieve messages for
            since_timestamp: Optional timestamp to filter messages
            
        Returns:
            List of messages for the agent
        """
        return self.message_handler.retrieve_agent_messages(agent_id, since_timestamp)
    
    def coordinate_agent_handoff(self, from_agent: str, to_agent: str, handoff_data: Dict[str, Any]) -> bool:
        """
        Coordinate handoff between agents with context transfer.
        
        Uses MANDATORY LTMC tools for handoff tracking:
        - graph_action for agent relationship mapping
        
        Args:
            from_agent: Agent handing off work
            to_agent: Agent receiving work  
            handoff_data: Data to transfer between agents
            
        Returns:
            bool: True if handoff successful
        """
        try:
            # Create handoff message
            handoff_message = AgentMessage(
                sender_agent=from_agent,
                recipient_agent=to_agent,
                message_type="handoff",
                content=handoff_data,
                timestamp=datetime.now(timezone.utc).isoformat(),
                conversation_id=self.conversation_id,
                task_id=self.task_id,
                requires_response=True
            )
            
            # Send handoff message
            if not self.send_agent_message(handoff_message):
                return False
            
            # Update agent statuses
            self.registration_manager.update_agent_status(from_agent, AgentStatus.COMPLETED)
            self.registration_manager.update_agent_status(to_agent, AgentStatus.ACTIVE)
            
            # Create graph relationship for handoff using graph_action (Tool 8) - MANDATORY
            graph_action(
                action="link",
                source_entity=f"agent_{from_agent}",
                target_entity=f"agent_{to_agent}",
                relationship="hands_off_to",
                properties={"handoff_time": handoff_message.timestamp, "task_id": self.task_id}
            )
            
            print(f"✅ Handoff completed: {from_agent} → {to_agent}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to coordinate agent handoff: {e}")
            return False
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """
        Get current status of an agent.
        
        Args:
            agent_id: Agent ID to get status for
            
        Returns:
            Optional[AgentStatus]: Agent status or None if not found
        """
        try:
            registration = self.registration_manager.get_agent_registration(agent_id)
            return registration.status if registration else None
            
        except Exception as e:
            print(f"❌ Failed to get agent status for {agent_id}: {e}")
            return None
    
    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered agents with their details.
        
        Returns:
            Dict mapping agent IDs to their registration details
        """
        try:
            registrations = self.registration_manager.get_all_registrations()
            
            return {
                agent_id: {
                    "type": reg.agent_type,
                    "status": reg.status.value,
                    "task_scope": reg.task_scope,
                    "dependencies": reg.dependencies,
                    "outputs": reg.outputs,
                    "start_time": reg.start_time,
                    "last_activity": reg.last_activity
                } for agent_id, reg in registrations.items()
            }
            
        except Exception as e:
            print(f"❌ Failed to get registered agents: {e}")
            return {}
    
    def get_operations_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive operations summary.
        
        Returns:
            Dict containing agent operations statistics and summaries
        """
        try:
            # Get registration summary from registration manager
            registration_summary = self.registration_manager.get_registration_summary()
            
            return {
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "registered_agents": registration_summary["active_agent_ids"] + registration_summary["completed_agent_ids"],
                "agent_statuses": {
                    agent_id: reg.status.value 
                    for agent_id, reg in self.registration_manager.get_all_registrations().items()
                },
                "registration_summary": registration_summary,
                "total_agents": registration_summary["total_agents"]
            }
            
        except Exception as e:
            print(f"❌ Failed to get operations summary: {e}")
            return {"error": str(e)}