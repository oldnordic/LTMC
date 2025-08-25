"""
LTMC Agent State Management System - Example Usage
Demonstrates the modularized agent state management components.

Extracted from agent_state_manager.py for smart modularization.
Shows practical usage of the state management system with real examples.
"""

import json
from ltms.coordination.agent_state_manager import LTMCAgentStateManager
from ltms.coordination.agent_coordination_framework import AgentStatus
from ltms.coordination.agent_state_models import StateTransition


def main():
    """Demonstrate LTMC Agent State Management System functionality."""
    print("🧪 Testing LTMC Agent State Management System")
    
    # Create state manager
    state_manager = LTMCAgentStateManager("test_coordination", "test_conversation")
    
    # Test agent state creation
    test_state_data = {
        "agent_id": "test_agent",
        "task_scope": ["analysis", "reporting"],
        "current_task": "architectural_analysis"
    }
    
    success = state_manager.create_agent_state(
        "test_agent",
        AgentStatus.INITIALIZING,
        test_state_data
    )
    
    if success:
        print("✅ Agent state created successfully")
        
        # Test state transition
        print("🔄 Testing state transition...")
        state_manager.transition_agent_state(
            "test_agent",
            AgentStatus.ACTIVE,
            StateTransition.ACTIVATE,
            {"state_updates": {"current_task": "dependency_mapping"}}
        )
        
        # Test checkpoint functionality
        print("💾 Testing checkpoint functionality...")
        state_manager.persist_state_checkpoint()
        
        # Get current state
        current_state = state_manager.get_agent_state("test_agent")
        print(f"📊 Current state: {current_state.status.value} at {current_state.timestamp}")
        
        # Get performance metrics
        metrics = state_manager.get_performance_metrics()
        print(f"📈 Performance metrics: {json.dumps(metrics, indent=2)}")
        
        # Test transition history
        history = state_manager.get_state_transition_history("test_agent")
        print(f"📋 Transition history: {len(history)} entries")
        
        # Test observer system
        def state_change_observer(agent_id, from_status, to_status):
            print(f"🔔 Observer: {agent_id} transitioned {from_status.value} → {to_status.value}")
        
        state_manager.register_state_observer("test_agent", state_change_observer)
        
        # Trigger another transition to test observer
        state_manager.transition_agent_state(
            "test_agent",
            AgentStatus.COMPLETED,
            StateTransition.COMPLETE,
            {"state_updates": {"final_status": "success"}}
        )
        
    else:
        print("❌ Failed to create agent state")
    
    print("✅ State management system test completed")


if __name__ == "__main__":
    main()