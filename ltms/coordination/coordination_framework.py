"""
LTMC Coordination Framework - Main Entry Point
Clean public API for the modularized agent coordination framework.

Provides unified interface to all coordination functionality through modular components:
- AgentCoordinationCore: Main coordination orchestrator
- AgentCoordinationModels: Data models and structures
- Supporting components: Registration, messaging, testing utilities

This is the primary interface for using the LTMC agent coordination system.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Import core coordination components
from .agent_coordination_core import AgentCoordinationCore
from .agent_coordination_models import (
    AgentStatus,
    CoordinationState, 
    AgentMessage,
    AgentRegistration
)

# Import supporting components for advanced usage
from .agent_registration_manager import AgentRegistrationManager
from .agent_message_handler import AgentMessageHandler

# Import testing utilities
from .test_agent_utility import TestAgent

# Main coordination class alias for clean API
LTMCAgentCoordinator = AgentCoordinationCore


def create_agent_coordinator(task_description: str, coordination_id: Optional[str] = None) -> AgentCoordinationCore:
    """
    Create a new LTMC agent coordinator.
    
    Factory function for creating agent coordination instances with
    complete LTMC integration and modular component orchestration.
    
    Args:
        task_description: Description of the coordination task
        coordination_id: Optional custom coordination identifier
        
    Returns:
        AgentCoordinationCore: Fully initialized coordinator
    """
    return AgentCoordinationCore(task_description, coordination_id)


def create_agent_message(sender_agent: str, 
                        recipient_agent: Optional[str],
                        message_type: str,
                        content: Dict[str, Any],
                        conversation_id: str,
                        task_id: str,
                        requires_response: bool = False) -> AgentMessage:
    """
    Create a standardized agent message.
    
    Factory function for creating properly formatted agent messages
    with automatic timestamp generation.
    
    Args:
        sender_agent: Agent sending the message
        recipient_agent: Agent receiving the message (None for broadcast)
        message_type: Type/category of the message
        content: Message content data
        conversation_id: Coordination conversation ID
        task_id: Coordination task ID
        requires_response: Whether message requires a response
        
    Returns:
        AgentMessage: Properly formatted message
    """
    return AgentMessage(
        sender_agent=sender_agent,
        recipient_agent=recipient_agent,
        message_type=message_type,
        content=content,
        timestamp=datetime.now(timezone.utc).isoformat(),
        conversation_id=conversation_id,
        task_id=task_id,
        requires_response=requires_response
    )


def create_sample_coordination() -> AgentCoordinationCore:
    """
    Create a sample coordination for testing and demonstration.
    
    Creates a coordinator with sample agents registered for
    testing coordination functionality.
    
    Returns:
        AgentCoordinationCore: Coordinator with sample agents
    """
    coordinator = create_agent_coordinator("Sample multi-agent task coordination")
    
    # Register sample agents
    coordinator.register_agent(
        agent_id="sample_planner",
        agent_type="ltmc-architectural-planner",
        task_scope=["architectural_analysis", "dependency_mapping"],
        outputs=["analysis_report", "dependency_graph"]
    )
    
    coordinator.register_agent(
        agent_id="sample_enforcer", 
        agent_type="ltmc-quality-enforcer",
        task_scope=["quality_validation", "safety_checks"],
        dependencies=["sample_planner"],
        outputs=["quality_report", "safety_validation"]
    )
    
    return coordinator


def demonstrate_coordination_framework():
    """
    Demonstrate coordination framework capabilities.
    
    Runs a complete demonstration of the modularized coordination
    framework including agent registration, messaging, handoffs,
    and finalization.
    """
    print("🧪 Demonstrating LTMC Agent Coordination Framework")
    print("=" * 60)
    
    # Create coordinator
    coordinator = create_sample_coordination()
    print(f"✅ Coordinator created: {coordinator.task_id}")
    
    # Test message sending
    test_message = create_agent_message(
        sender_agent="sample_planner",
        recipient_agent="sample_enforcer", 
        message_type="analysis_complete",
        content={
            "analysis": "architectural_analysis_complete", 
            "next_step": "quality_validation"
        },
        conversation_id=coordinator.conversation_id,
        task_id=coordinator.task_id
    )
    
    message_result = coordinator.send_agent_message(test_message)
    print(f"✅ Message sent successfully: {message_result}")
    
    # Test status updates
    status_result = coordinator.registration_manager.update_agent_status(
        "sample_planner", 
        AgentStatus.COMPLETED, 
        {"analysis": "complete"}
    )
    print(f"✅ Status updated successfully: {status_result}")
    
    # Test handoff
    handoff_result = coordinator.coordinate_agent_handoff(
        "sample_planner", 
        "sample_enforcer",
        {"analysis_results": "passed", "ready_for_validation": True}
    )
    print(f"✅ Handoff completed successfully: {handoff_result}")
    
    # Get final summary
    summary = coordinator.get_coordination_summary()
    print(f"📊 Registered agents: {len(summary['registered_agents'])}")
    print(f"📊 LTMC documents: {summary['ltmc_documents']}")
    
    # Finalize coordination
    final_report = coordinator.finalize_coordination()
    print(f"✅ Coordination finalized: {final_report['coordination_completed']}")
    print(f"📋 Total agents: {final_report['total_agents']}")
    print(f"📋 Successful agents: {final_report['successful_agents']}")
    
    print("=" * 60)
    print("🎉 Coordination framework demonstration completed")
    
    return final_report


# Export main interface components
__all__ = [
    # Main coordination class
    'LTMCAgentCoordinator',
    'AgentCoordinationCore',
    
    # Data models
    'AgentStatus',
    'CoordinationState',
    'AgentMessage', 
    'AgentRegistration',
    
    # Component managers
    'AgentRegistrationManager',
    'AgentMessageHandler',
    
    # Testing utilities
    'TestAgent',
    
    # Factory functions
    'create_agent_coordinator',
    'create_agent_message',
    'create_sample_coordination',
    
    # Demonstration
    'demonstrate_coordination_framework'
]


# Main execution for testing
if __name__ == "__main__":
    demonstrate_coordination_framework()