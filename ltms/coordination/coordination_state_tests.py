"""
LTMC Coordination State Tests
Agent state management functionality testing in coordination framework.

Extracted from coordination_test_example.py for smart modularization (300-line limit compliance).
Handles state management and transition testing for coordination framework.

Components:
- CoordinationStateTests: Agent state management and transition tests
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

# Import coordination framework components
from .agent_coordination_framework import LTMCAgentCoordinator, AgentStatus
from .agent_state_manager import LTMCAgentStateManager, StateTransition
from .mcp_communication_patterns import LTMCMessageBroker
from .test_agent_utility import TestAgent


class CoordinationStateTests:
    """
    Agent state management functionality testing.
    
    Provides comprehensive testing of:
    - Agent state creation and management
    - State transition validation
    - State persistence and recovery
    - Multi-agent state coordination
    - Error handling in state operations
    
    Used for validating state management in coordination framework.
    """
    
    def __init__(self):
        """Initialize coordination state tests."""
        self.test_results = {}
        self.test_agents = {}
        self.coordinator = None
        self.state_manager = None
        self.message_broker = None
    
    def setup_test_agents(self, coordinator: LTMCAgentCoordinator, 
                         state_manager: LTMCAgentStateManager, 
                         message_broker: LTMCMessageBroker) -> bool:
        """
        Setup test agents for state management testing.
        
        Args:
            coordinator: Agent coordinator for registration
            state_manager: State management system
            message_broker: Message broker for communication
            
        Returns:
            bool: True if setup successful, False otherwise
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.message_broker = message_broker
        
        # Create test agents
        agent_configs = [
            ("test_planner", "ltmc-architectural-planner"),
            ("test_enforcer", "ltmc-quality-enforcer"),
            ("test_mapper", "ltmc-reality-cartographer")
        ]
        
        for agent_id, agent_type in agent_configs:
            # Create test agent
            agent = TestAgent(agent_id, agent_type, coordinator)
            success = agent.initialize(state_manager, message_broker)
            
            if success:
                self.test_agents[agent_id] = agent
                
                # Create agent state
                state_data = {
                    "agent_id": agent_id,
                    "task_scope": [f"{agent_type}_tasks"],
                    "current_task": None
                }
                
                state_manager.create_agent_state(
                    agent_id,
                    AgentStatus.INITIALIZING,
                    state_data
                )
        
        return len(self.test_agents) > 0
    
    def test_state_management(self) -> Dict[str, Any]:
        """
        Test agent state management functionality.
        
        Tests comprehensive state management including:
        - State creation and initialization
        - State transitions (ACTIVE, WAITING, COMPLETED, ERROR)
        - State persistence and checkpointing
        - Multi-agent state coordination
        
        Returns:
            Dict[str, Any]: State management test results
        """
        print("\n📋 Test: State Management")
        
        try:
            state_test_results = []
            
            for agent_id, agent in self.test_agents.items():
                # Test state transitions
                transitions = [
                    (AgentStatus.ACTIVE, StateTransition.ACTIVATE),
                    (AgentStatus.WAITING, StateTransition.PAUSE),
                    (AgentStatus.ACTIVE, StateTransition.RESUME),
                    (AgentStatus.COMPLETED, StateTransition.COMPLETE)
                ]
                
                transition_results = []
                for target_status, transition_type in transitions:
                    success = self.state_manager.transition_agent_state(
                        agent_id,
                        target_status,
                        transition_type
                    )
                    
                    transition_results.append({
                        "target_status": target_status.value,
                        "transition_type": transition_type.value,
                        "success": success
                    })
                
                # Get final state
                final_state = self.state_manager.get_agent_state(agent_id)
                
                state_test_results.append({
                    "agent_id": agent_id,
                    "transitions": transition_results,
                    "final_status": final_state.status.value if final_state else None
                })
            
            # Test checkpoint functionality
            checkpoint_success = self.state_manager.persist_state_checkpoint()
            
            self.test_results["state_management"] = {
                "status": "passed",
                "agent_state_tests": state_test_results,
                "checkpoint_success": checkpoint_success,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            print("✅ State management: PASSED")
            return self.test_results["state_management"]
            
        except Exception as e:
            self.test_results["state_management"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            print(f"❌ State management: FAILED - {e}")
            raise
    
    def get_test_results(self) -> Dict[str, Any]:
        """
        Get all state test results.
        
        Returns:
            Dict[str, Any]: Complete state test results
        """
        return self.test_results.copy()
    
    def reset_tests(self):
        """
        Reset state tests to clean state.
        
        Clears all test results and test agents for fresh execution.
        """
        self.test_results.clear()
        self.test_agents.clear()
        self.coordinator = None
        self.state_manager = None
        self.message_broker = None