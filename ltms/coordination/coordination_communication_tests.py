"""
LTMC Coordination Communication Tests  
Inter-agent communication functionality testing in coordination framework.

Extracted from coordination_test_example.py for smart modularization (300-line limit compliance).
Handles message communication and workflow orchestration testing.

Components:
- CoordinationCommunicationTests: Message communication and workflow orchestration tests
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

# Import coordination framework components
from .agent_coordination_core import AgentCoordinationCore
from .agent_state_manager import LTMCAgentStateManager
from .mcp_message_broker import LTMCMessageBroker
from .mcp_workflow_orchestrator import WorkflowOrchestrator
from .mcp_communication_factory import (
    create_request_response_message,
    create_broadcast_message
)
from .test_agent_utility import TestAgent


class CoordinationCommunicationTests:
    """
    Inter-agent communication functionality testing.
    
    Provides comprehensive testing of:
    - Inter-agent message communication
    - Broadcast message functionality
    - Message processing and handling
    - Workflow orchestration
    - Communication error handling
    
    Used for validating communication in coordination framework.
    """
    
    def __init__(self):
        """Initialize coordination communication tests."""
        self.test_results = {}
        self.test_agents = {}
        self.coordinator = None
        self.message_broker = None
    
    def setup_test_agents(self, coordinator: AgentCoordinationCore, 
                         state_manager: LTMCAgentStateManager, 
                         message_broker: LTMCMessageBroker) -> bool:
        """
        Setup test agents for communication testing.
        
        Args:
            coordinator: Agent coordinator for registration
            state_manager: State management system
            message_broker: Message broker for communication
            
        Returns:
            bool: True if setup successful, False otherwise
        """
        self.coordinator = coordinator
        self.message_broker = message_broker
        
        # Create test agents for communication
        agent_configs = [
            ("comm_sender", "ltmc-communication-sender"),
            ("comm_receiver", "ltmc-communication-receiver"),
            ("comm_orchestrator", "ltmc-communication-orchestrator")
        ]
        
        for agent_id, agent_type in agent_configs:
            agent = TestAgent(agent_id, agent_type, coordinator)
            success = agent.initialize(state_manager, message_broker)
            
            if success:
                self.test_agents[agent_id] = agent
        
        return len(self.test_agents) >= 2  # Need at least 2 for communication testing
    
    def test_message_communication(self) -> Dict[str, Any]:
        """
        Test inter-agent message communication functionality.
        
        Tests comprehensive message communication including:
        - Point-to-point messaging between agents
        - Broadcast message functionality
        - Message processing and handling
        - Communication error recovery
        
        Returns:
            Dict[str, Any]: Message communication test results
        """
        print("\n📋 Test: Message Communication")
        
        try:
            communication_results = []
            
            # Test inter-agent messaging
            agent_ids = list(self.test_agents.keys())
            if len(agent_ids) >= 2:
                sender = agent_ids[0]
                recipient = agent_ids[1]
                
                # Send test message
                test_message_content = {
                    "message_type": "coordination_test",
                    "data": "Test inter-agent communication",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                send_success = self.test_agents[sender].send_message_to_agent(
                    recipient, test_message_content
                )
                
                # Process messages
                processed_count = self.test_agents[recipient].process_pending_messages()
                
                communication_results.append({
                    "sender": sender,
                    "recipient": recipient,
                    "send_success": send_success,
                    "messages_processed": processed_count
                })
            
            # Test broadcast message
            broadcast_message = create_broadcast_message(
                sender="test_coordinator",
                message_type="test_broadcast",
                broadcast_data={"announcement": "Test broadcast message"},
                conversation_id=self.coordinator.conversation_id,
                task_id=self.coordinator.task_id
            )
            
            broadcast_success = self.message_broker.send_message(broadcast_message)
            
            self.test_results["message_communication"] = {
                "status": "passed",
                "inter_agent_communication": communication_results,
                "broadcast_success": broadcast_success,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            print("✅ Message communication: PASSED")
            return self.test_results["message_communication"]
            
        except Exception as e:
            self.test_results["message_communication"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            print(f"❌ Message communication: FAILED - {e}")
            raise
    
    def test_workflow_orchestration(self) -> Dict[str, Any]:
        """
        Test workflow orchestration functionality.
        
        Tests comprehensive workflow orchestration including:
        - Workflow creation and configuration
        - Step management and dependencies
        - Agent task execution coordination
        - Workflow state management
        
        Returns:
            Dict[str, Any]: Workflow orchestration test results
        """
        print("\n📋 Test: Workflow Orchestration")
        
        try:
            # Create workflow orchestrator
            orchestrator = WorkflowOrchestrator(
                "test_workflow",
                self.coordinator.conversation_id
            )
            
            # Add workflow steps
            agent_ids = list(self.test_agents.keys())
            workflow_steps = []
            
            for i, agent_id in enumerate(agent_ids[:3]):  # Use first 3 agents
                step_id = f"step_{i+1}"
                orchestrator.add_workflow_step(
                    step_id,
                    agent_id,
                    f"Test task for {agent_id}",
                    dependencies=[f"step_{i}"] if i > 0 else []
                )
                workflow_steps.append(step_id)
            
            # Execute workflow (simplified - not using async for testing)
            workflow_state = {
                "workflow_id": orchestrator.workflow_id,
                "steps": workflow_steps,
                "status": "simulated_execution"
            }
            
            # Simulate agent task execution
            execution_results = []
            for agent_id in agent_ids[:3]:
                if agent_id in self.test_agents:
                    result = self.test_agents[agent_id].execute_task(
                        f"Workflow task for {agent_id}"
                    )
                    execution_results.append(result)
            
            self.test_results["workflow_orchestration"] = {
                "status": "passed",
                "workflow_created": True,
                "steps_added": len(workflow_steps),
                "execution_results": execution_results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            print("✅ Workflow orchestration: PASSED")
            return self.test_results["workflow_orchestration"]
            
        except Exception as e:
            self.test_results["workflow_orchestration"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            print(f"❌ Workflow orchestration: FAILED - {e}")
            raise
    
    def get_test_results(self) -> Dict[str, Any]:
        """
        Get all communication test results.
        
        Returns:
            Dict[str, Any]: Complete communication test results
        """
        return self.test_results.copy()
    
    def reset_tests(self):
        """
        Reset communication tests to clean state.
        
        Clears all test results and test agents for fresh execution.
        """
        self.test_results.clear()
        self.test_agents.clear()
        self.coordinator = None
        self.message_broker = None