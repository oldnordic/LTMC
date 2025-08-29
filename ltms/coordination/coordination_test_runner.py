"""
LTMC Coordination Test Runner
Main orchestrator for comprehensive coordination framework testing.

Extracted from coordination_test_example.py for smart modularization (300-line limit compliance).
Orchestrates all modular test components into complete testing workflow.

Components:
- CoordinationTestRunner: Main test orchestration and execution
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

# Import all modular test components
from .coordination_framework_tests import CoordinationFrameworkTests
from .coordination_state_tests import CoordinationStateTests
from .coordination_communication_tests import CoordinationCommunicationTests
from .coordination_integration_tests import CoordinationIntegrationTests

# LTMC MCP tool imports
from ltms.tools.memory.memory_actions import memory_action


class CoordinationTestRunner:
    """
    Main orchestrator for comprehensive coordination framework testing.
    
    Coordinates execution of all modular test components:
    - Framework initialization testing
    - Agent registration and state management testing
    - Message communication and workflow testing
    - LTMC integration validation testing
    - Complete test reporting and documentation
    
    Provides unified interface for complete coordination framework validation.
    """
    
    def __init__(self):
        """Initialize coordination test runner."""
        self.test_results = {}
        self.framework_tests = CoordinationFrameworkTests()
        self.state_tests = CoordinationStateTests()
        self.communication_tests = CoordinationCommunicationTests()
        self.integration_tests = CoordinationIntegrationTests()
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """
        Run complete coordination framework test suite.
        
        Executes all modular test components in proper sequence:
        1. Framework initialization tests
        2. Agent registration and state management tests
        3. Message communication and workflow tests
        4. LTMC integration validation tests
        5. Complete test report generation
        
        Returns:
            Dict[str, Any]: Comprehensive test suite results
        """
        print("🧪 Starting LTMC Agent Coordination Framework Test Suite")
        print("==" * 40)
        
        try:
            # Test 1: Framework initialization
            print("\n📋 Phase 1: Framework Initialization Testing")
            framework_result = self.framework_tests.test_framework_initialization()
            self.test_results["framework_initialization"] = framework_result
            
            # Test 2: Agent registration and state management
            print("\n📋 Phase 2: Agent Registration and State Management Testing")
            
            # Setup test agents using framework components
            state_setup_success = self.state_tests.setup_test_agents(
                self.framework_tests.coordinator,
                self.framework_tests.state_manager,
                self.framework_tests.message_broker
            )
            
            if not state_setup_success:
                raise Exception("Failed to setup test agents for state testing")
            
            state_result = self.state_tests.test_state_management()
            self.test_results["state_management"] = state_result
            
            # Test 3: Message communication and workflow orchestration
            print("\n📋 Phase 3: Message Communication and Workflow Testing")
            
            # Setup communication testing agents
            comm_setup_success = self.communication_tests.setup_test_agents(
                self.framework_tests.coordinator,
                self.framework_tests.state_manager,
                self.framework_tests.message_broker
            )
            
            if not comm_setup_success:
                raise Exception("Failed to setup test agents for communication testing")
            
            message_result = self.communication_tests.test_message_communication()
            self.test_results["message_communication"] = message_result
            
            workflow_result = self.communication_tests.test_workflow_orchestration()
            self.test_results["workflow_orchestration"] = workflow_result
            
            # Test 4: LTMC integration validation
            print("\n📋 Phase 4: LTMC Integration Validation Testing")
            
            # Setup integration testing components
            integration_setup_success = self.integration_tests.setup_integration_components(
                self.framework_tests.coordinator,
                self.framework_tests.state_manager
            )
            
            if not integration_setup_success:
                raise Exception("Failed to setup components for integration testing")
            
            integration_result = await self.integration_tests.test_integration_validation()
            self.test_results["integration_validation"] = integration_result
            
            # Generate final report
            return await self.generate_test_report()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            return {"error": str(e), "test_results": self.test_results}
    
    async def generate_test_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive test report.
        
        Creates detailed test report with:
        - Test execution summary and statistics
        - Individual test results and metrics
        - Success/failure analysis
        - Performance metrics
        - LTMC integration validation results
        
        Returns:
            Dict[str, Any]: Complete test report
        """
        print("\n📊 Generating Comprehensive Test Report")
        
        # Count passed/failed tests
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result.get("status") == "passed")
        failed_tests = total_tests - passed_tests
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Finalize coordination (using framework coordinator)
        final_report = self.framework_tests.coordinator.finalize_coordination()
        
        test_report = {
            "test_suite": "LTMC Agent Coordination Framework",
            "execution_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{success_rate:.1f}%",
                "overall_status": "PASSED" if failed_tests == 0 else "FAILED"
            },
            "test_results": self.test_results,
            "coordination_final_report": final_report,
            "validation_complete": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store complete test report in LTMC
        task_id = self.framework_tests.coordinator.task_id
        conversation_id = self.framework_tests.coordinator.conversation_id
        
        # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
        # Generate dynamic file name based on test report context and execution results
        report_timestamp = test_report["timestamp"].replace(':', '_').replace('-', '_')
        overall_status = test_report["execution_summary"]["overall_status"].lower()
        success_rate_clean = test_report["execution_summary"]["success_rate"].replace('.', '_').replace('%', 'pct')
        total_tests = test_report["execution_summary"]["total_tests"]
        passed_tests = test_report["execution_summary"]["passed_tests"]
        dynamic_test_report_file_name = f"coordination_test_report_{task_id}_{overall_status}_{success_rate_clean}_{passed_tests}of{total_tests}passed_{report_timestamp}.json"
        
        await memory_action(
            action="store",
            file_name=dynamic_test_report_file_name,
            content=json.dumps(test_report, indent=2),
            tags=["coordination_test", "framework_validation", "test_report"],
            conversation_id=conversation_id,
            role="system"
        )
        
        print("=" * 80)
        print(f"🎯 TEST SUITE COMPLETE: {test_report['execution_summary']['overall_status']}")
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        print("=" * 80)
        
        return test_report
    
    def get_test_results(self) -> Dict[str, Any]:
        """
        Get all test results from modular components.
        
        Returns:
            Dict[str, Any]: Complete test results from all components
        """
        return {
            "framework_tests": self.framework_tests.get_test_results(),
            "state_tests": self.state_tests.get_test_results(),
            "communication_tests": self.communication_tests.get_test_results(),
            "integration_tests": self.integration_tests.get_test_results(),
            "runner_results": self.test_results.copy()
        }
    
    def reset_all_tests(self):
        """
        Reset all modular test components to clean state.
        
        Resets all test components for fresh execution.
        """
        self.test_results.clear()
        self.framework_tests.reset_tests()
        self.state_tests.reset_tests()
        self.communication_tests.reset_tests()
        self.integration_tests.reset_tests()


# Main test execution function
def run_coordination_tests() -> Dict[str, Any]:
    """
    Main entry point for coordination framework testing.
    
    Creates and executes complete coordination test suite.
    
    Returns:
        Dict[str, Any]: Complete test suite results
    """
    print("🚀 LTMC Agent Coordination Framework - Complete Test Suite")
    print("Testing all components: Coordination, Communication, State Management")
    
    # Run complete test suite
    test_runner = CoordinationTestRunner()
    final_report = test_runner.run_complete_test_suite()
    
    # Display summary
    if final_report.get("execution_summary", {}).get("overall_status") == "PASSED":
        print("✅ All tests passed - Framework ready for production use")
    else:
        print("❌ Some tests failed - Review test results for issues")
    
    print("📋 Complete test report stored in LTMC memory")
    
    return final_report


# Main test execution
if __name__ == "__main__":
    run_coordination_tests()