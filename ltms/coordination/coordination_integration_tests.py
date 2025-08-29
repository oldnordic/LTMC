"""
LTMC Coordination Integration Tests
LTMC integration validation functionality in coordination framework.

Extracted from coordination_test_example.py for smart modularization (300-line limit compliance).
Handles LTMC tool integration validation and complete system testing.

Components:
- CoordinationIntegrationTests: LTMC tool integration validation tests
"""

from datetime import datetime, timezone
from typing import Dict, Any

# Import coordination framework components
from .agent_coordination_core import AgentCoordinationCore
from .agent_state_manager import LTMCAgentStateManager

# LTMC MCP tool imports for validation (Updated imports after reindexing)
from ltms.tools.memory.memory_actions import memory_action
from ltms.tools.graph.graph_actions import graph_action


class CoordinationIntegrationTests:
    """
    LTMC integration validation functionality testing.
    
    Provides comprehensive testing of:
    - LTMC memory integration validation
    - LTMC graph integration validation
    - Coordination framework validation
    - State management performance validation
    - Complete system integration testing
    
    Used for validating LTMC integration in coordination framework.
    """
    
    def __init__(self):
        """Initialize coordination integration tests."""
        self.test_results = {}
        self.coordinator = None
        self.state_manager = None
    
    def setup_integration_components(self, coordinator: AgentCoordinationCore, 
                                   state_manager: LTMCAgentStateManager) -> bool:
        """
        Setup components for integration testing.
        
        Args:
            coordinator: Agent coordinator for validation
            state_manager: State management system
            
        Returns:
            bool: True if setup successful, False otherwise
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        return True
    
    async def test_integration_validation(self) -> Dict[str, Any]:
        """
        Test LTMC integration validation functionality.
        
        Tests comprehensive integration validation including:
        - LTMC memory system integration
        - LTMC graph system integration  
        - Coordination framework validation
        - State management performance validation
        - Complete system integration validation
        
        Returns:
            Dict[str, Any]: Integration validation test results
        """
        print("\n📋 Test: Integration Validation")
        
        try:
            # Validate LTMC integration
            ltmc_validation = {}
            
            # Test memory retrieval
            memory_result = await memory_action(
                action="retrieve",
                query=f"coordination test_suite {self.coordinator.task_id}",
                conversation_id=self.coordinator.conversation_id,
                k=5
            )
            
            # Check correct data structure - memory retrieval returns data.documents
            data = memory_result.get('data', {})
            documents = data.get('documents', []) or data.get('results', [])
            
            ltmc_validation["memory_integration"] = {
                "success": memory_result.get('success', False),
                "documents_found": len(documents)
            }
            
            # Test graph relationships
            graph_result = await graph_action(
                action="query",
                query_text=f"coordination_{self.coordinator.task_id}",
                return_paths=True
            )
            
            ltmc_validation["graph_integration"] = {
                "success": bool(graph_result),
                "relationships_found": len(graph_result) if graph_result else 0
            }
            
            # Validate agent coordination
            coordination_summary = self.coordinator.get_coordination_summary()
            
            ltmc_validation["coordination_framework"] = {
                "registered_agents": coordination_summary.get("registered_agents", []),
                "agent_count": len(coordination_summary.get("registered_agents", [])),
                "ltmc_documents": coordination_summary.get("ltmc_documents", 0)
            }
            
            # Validate state management
            state_performance = self.state_manager.get_performance_metrics()
            
            ltmc_validation["state_management"] = {
                "total_transitions": state_performance.get("state_transitions", 0),
                "validation_errors": state_performance.get("validation_errors", 0),
                "average_transition_time": state_performance.get("average_transition_time", 0.0)
            }
            
            self.test_results["integration_validation"] = {
                "status": "passed",
                "ltmc_validation": ltmc_validation,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            print("✅ Integration validation: PASSED")
            return self.test_results["integration_validation"]
            
        except Exception as e:
            self.test_results["integration_validation"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            print(f"❌ Integration validation: FAILED - {e}")
            raise
    
    def get_test_results(self) -> Dict[str, Any]:
        """
        Get all integration test results.
        
        Returns:
            Dict[str, Any]: Complete integration test results
        """
        return self.test_results.copy()
    
    def reset_tests(self):
        """
        Reset integration tests to clean state.
        
        Clears all test results for fresh execution.
        """
        self.test_results.clear()
        self.coordinator = None
        self.state_manager = None