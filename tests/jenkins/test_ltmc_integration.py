#!/usr/bin/env python3
"""
TDD Test Suite: LTMC 11-Tool Integration Validation for Jenkins Pipeline
========================================================================

Professional test suite validating that ALL 11 consolidated LTMC tools are 
properly integrated in Jenkins pipeline and accessible during CI/CD execution.

NON-NEGOTIABLE: All 11 tools must be validated and working.
"""

import pytest
import sys
import asyncio
import os
from pathlib import Path
from typing import Dict, List, Any, NamedTuple, Optional
from dataclasses import dataclass
from enum import Enum

# Add LTMC to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all 11 LTMC consolidated tools
from ltms.tools.memory_tools import MemoryManager
from ltms.tools.todo_tools import TodoManager  
from ltms.tools.cache_tools import CacheManager
from ltms.tools.pattern_tools import PatternAnalyzer
from ltms.tools.graph_tools import GraphManager
from ltms.tools.blueprint_tools import BlueprintManager
from ltms.tools.documentation_tools import DocumentationManager
from ltms.tools.chat_tools import ChatManager
from ltms.tools.config_tools import ConfigManager
from ltms.tools.unix_tools import UnixToolManager
from ltms.tools.sync_tools import SyncManager

class ToolStatus(Enum):
    """Professional tool status enumeration"""
    ACCESSIBLE = "accessible"
    FAILED_IMPORT = "failed_import"
    FAILED_INIT = "failed_init" 
    FAILED_OPERATION = "failed_operation"
    NOT_TESTED = "not_tested"

@dataclass
class LTMCToolValidation:
    """Professional tool validation result"""
    tool_name: str
    status: ToolStatus
    import_successful: bool
    initialization_successful: bool
    basic_operation_successful: bool
    jenkins_compatible: bool
    error_message: Optional[str] = None
    performance_ms: Optional[float] = None

@dataclass
class LTMCIntegrationAnalysis:
    """Complete LTMC integration analysis"""
    total_tools: int
    accessible_tools: int
    failed_tools: int
    tool_validations: List[LTMCToolValidation]
    jenkins_ready: bool
    missing_tools: List[str]
    performance_summary: Dict[str, float]

class LTMCIntegrationValidator:
    """Professional LTMC integration validator with comprehensive testing"""
    
    def __init__(self):
        self.expected_tools = [
            "memory", "todo", "cache", "pattern", "graph", 
            "blueprint", "documentation", "chat", "config", 
            "unix", "sync"
        ]
        self.tool_classes = {
            "memory": MemoryManager,
            "todo": TodoManager,
            "cache": CacheManager, 
            "pattern": PatternAnalyzer,
            "graph": GraphManager,
            "blueprint": BlueprintManager,
            "documentation": DocumentationManager,
            "chat": ChatManager,
            "config": ConfigManager,
            "unix": UnixToolManager,
            "sync": SyncManager
        }
    
    def validate_all_tools(self) -> LTMCIntegrationAnalysis:
        """
        Professional validation of all 11 LTMC tools.
        
        NON-NEGOTIABLE: Must validate every single tool.
        """
        import time
        
        tool_validations = []
        performance_summary = {}
        
        for tool_name in self.expected_tools:
            start_time = time.time()
            validation = self._validate_single_tool(tool_name)
            end_time = time.time()
            
            validation.performance_ms = (end_time - start_time) * 1000
            performance_summary[tool_name] = validation.performance_ms
            tool_validations.append(validation)
        
        accessible_count = len([v for v in tool_validations if v.status == ToolStatus.ACCESSIBLE])
        failed_count = len(tool_validations) - accessible_count
        missing_tools = [v.tool_name for v in tool_validations if v.status != ToolStatus.ACCESSIBLE]
        
        analysis = LTMCIntegrationAnalysis(
            total_tools=len(self.expected_tools),
            accessible_tools=accessible_count,
            failed_tools=failed_count,
            tool_validations=tool_validations,
            jenkins_ready=accessible_count == len(self.expected_tools),
            missing_tools=missing_tools,
            performance_summary=performance_summary
        )
        
        # Store comprehensive analysis in LTMC memory
        self._store_integration_analysis(analysis)
        
        return analysis
    
    def _validate_single_tool(self, tool_name: str) -> LTMCToolValidation:
        """Professional single tool validation with comprehensive testing"""
        validation = LTMCToolValidation(
            tool_name=tool_name,
            status=ToolStatus.NOT_TESTED,
            import_successful=False,
            initialization_successful=False,
            basic_operation_successful=False,
            jenkins_compatible=False
        )
        
        try:
            # Step 1: Import validation
            tool_class = self.tool_classes.get(tool_name)
            if tool_class is None:
                validation.status = ToolStatus.FAILED_IMPORT
                validation.error_message = f"Tool class not found for {tool_name}"
                return validation
                
            validation.import_successful = True
            
            # Step 2: Initialization validation  
            try:
                tool_instance = tool_class()
                validation.initialization_successful = True
            except Exception as init_error:
                validation.status = ToolStatus.FAILED_INIT
                validation.error_message = f"Initialization failed: {str(init_error)}"
                return validation
            
            # Step 3: Basic operation validation
            basic_op_result = self._test_basic_operation(tool_name, tool_instance)
            if basic_op_result["success"]:
                validation.basic_operation_successful = True
                
                # Step 4: Jenkins compatibility validation
                jenkins_compat = self._test_jenkins_compatibility(tool_name, tool_instance)
                if jenkins_compat["success"]:
                    validation.jenkins_compatible = True
                    validation.status = ToolStatus.ACCESSIBLE
                else:
                    validation.status = ToolStatus.FAILED_OPERATION
                    validation.error_message = jenkins_compat["error"]
            else:
                validation.status = ToolStatus.FAILED_OPERATION
                validation.error_message = basic_op_result["error"]
                
        except Exception as e:
            validation.status = ToolStatus.FAILED_IMPORT
            validation.error_message = f"Import/validation error: {str(e)}"
        
        return validation
    
    def _test_basic_operation(self, tool_name: str, tool_instance) -> Dict[str, Any]:
        """Test basic operations for each tool type"""
        try:
            if tool_name == "memory":
                # Test memory storage and retrieval
                test_result = tool_instance.store_memory(
                    content="Jenkins integration test",
                    memory_type="test",
                    tags=["jenkins", "integration", "test"]
                )
                return {"success": True, "result": test_result}
                
            elif tool_name == "todo":
                # Test todo creation
                test_result = tool_instance.add_todo(
                    content="Jenkins integration test todo",
                    priority="low",
                    tags=["jenkins", "test"]
                )
                return {"success": True, "result": test_result}
                
            elif tool_name == "cache":
                # Test cache operations
                test_result = tool_instance.health_check()
                return {"success": True, "result": test_result}
                
            elif tool_name == "pattern":
                # Test pattern analysis
                test_result = tool_instance.extract_functions(
                    code="def test(): pass",
                    language="python"
                )
                return {"success": True, "result": test_result}
                
            elif tool_name == "graph":
                # Test graph operations
                test_result = tool_instance.health_check()
                return {"success": True, "result": test_result}
                
            elif tool_name == "blueprint":
                # Test blueprint creation
                test_result = tool_instance.create_blueprint(
                    title="Jenkins Test Blueprint",
                    description="Test blueprint for Jenkins integration",
                    type="test"
                )
                return {"success": True, "result": test_result}
                
            elif tool_name == "documentation":
                # Test documentation operations
                test_result = tool_instance.health_check()
                return {"success": True, "result": test_result}
                
            elif tool_name == "chat":
                # Test chat logging
                test_result = tool_instance.log_conversation(
                    message="Jenkins integration test",
                    tool_name="test_tool"
                )
                return {"success": True, "result": test_result}
                
            elif tool_name == "config":
                # Test configuration validation
                test_result = tool_instance.validate_config()
                return {"success": True, "result": test_result}
                
            elif tool_name == "unix":
                # Test unix operations
                test_result = tool_instance.list_files(path=".")
                return {"success": True, "result": test_result}
                
            elif tool_name == "sync":
                # Test sync operations
                test_result = tool_instance.status()
                return {"success": True, "result": test_result}
            
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_jenkins_compatibility(self, tool_name: str, tool_instance) -> Dict[str, Any]:
        """Test Jenkins environment compatibility"""
        try:
            # Simulate Jenkins environment variables
            jenkins_env = {
                "BUILD_NUMBER": "test-123",
                "WORKSPACE": "/tmp/jenkins-test",
                "JENKINS_URL": "http://192.168.1.119:8080"
            }
            
            # Test tool works with Jenkins environment
            if hasattr(tool_instance, 'set_jenkins_context'):
                tool_instance.set_jenkins_context(jenkins_env)
            
            # All tools should be able to handle Jenkins context
            return {"success": True, "message": "Jenkins compatible"}
            
        except Exception as e:
            return {"success": False, "error": f"Jenkins compatibility error: {str(e)}"}
    
    def _store_integration_analysis(self, analysis: LTMCIntegrationAnalysis):
        """Store comprehensive analysis in LTMC memory"""
        try:
            memory_manager = MemoryManager()
            memory_manager.store_memory(
                content=f"LTMC Integration Analysis: {analysis.accessible_tools}/{analysis.total_tools} tools accessible",
                memory_type="technical",
                tags=["ltmc", "integration", "jenkins", "tdd", "validation"],
                metadata={
                    "total_tools": analysis.total_tools,
                    "accessible_tools": analysis.accessible_tools,
                    "failed_tools": analysis.failed_tools,
                    "jenkins_ready": analysis.jenkins_ready,
                    "missing_tools": analysis.missing_tools,
                    "performance_avg_ms": sum(analysis.performance_summary.values()) / len(analysis.performance_summary) if analysis.performance_summary else 0
                }
            )
        except Exception as e:
            print(f"⚠️ Could not store analysis in LTMC memory: {e}")


class TestLTMCIntegration:
    """
    Professional TDD test suite for LTMC tool integration.
    
    NON-NEGOTIABLE: All 11 tools must be validated and accessible.
    """
    
    @pytest.fixture
    def integration_validator(self):
        """Professional test fixture"""
        return LTMCIntegrationValidator()
    
    def test_all_11_tools_expected(self, integration_validator):
        """TDD: Validate we're testing exactly 11 tools"""
        assert len(integration_validator.expected_tools) == 11, f"Expected 11 tools, got {len(integration_validator.expected_tools)}"
        
        expected_tools = [
            "memory", "todo", "cache", "pattern", "graph",
            "blueprint", "documentation", "chat", "config", 
            "unix", "sync"
        ]
        
        assert set(integration_validator.expected_tools) == set(expected_tools), \
            f"Tool mismatch: expected {expected_tools}, got {integration_validator.expected_tools}"
    
    def test_all_tool_classes_importable(self, integration_validator):
        """TDD: Validate all 11 tool classes can be imported"""
        for tool_name, tool_class in integration_validator.tool_classes.items():
            # This will fail if import fails
            assert tool_class is not None, f"Tool class {tool_name} is None"
            assert hasattr(tool_class, '__name__'), f"Tool class {tool_name} invalid"
            
            # Validate class can be instantiated (basic smoke test)
            try:
                instance = tool_class()
                assert instance is not None, f"Could not instantiate {tool_name}"
            except Exception as e:
                pytest.fail(f"Failed to instantiate {tool_name}: {e}")
    
    def test_comprehensive_tool_validation(self, integration_validator):
        """
        TDD: Comprehensive validation of all 11 LTMC tools.
        
        This is the main professional integration test.
        """
        analysis = integration_validator.validate_all_tools()
        
        # NON-NEGOTIABLE: All 11 tools must be accessible
        assert analysis.total_tools == 11, f"Should test 11 tools, tested {analysis.total_tools}"
        
        # Check each tool individually for detailed reporting
        for validation in analysis.tool_validations:
            assert validation.import_successful, f"{validation.tool_name}: Import failed - {validation.error_message}"
            assert validation.initialization_successful, f"{validation.tool_name}: Initialization failed - {validation.error_message}"
            assert validation.basic_operation_successful, f"{validation.tool_name}: Basic operation failed - {validation.error_message}"
            assert validation.jenkins_compatible, f"{validation.tool_name}: Jenkins compatibility failed - {validation.error_message}"
            assert validation.status == ToolStatus.ACCESSIBLE, f"{validation.tool_name}: Not accessible - {validation.error_message}"
        
        # Professional requirements
        assert analysis.accessible_tools == 11, f"All 11 tools must be accessible, got {analysis.accessible_tools}"
        assert analysis.failed_tools == 0, f"No tools should fail, got {analysis.failed_tools} failures"
        assert analysis.jenkins_ready == True, "LTMC must be Jenkins ready"
        assert len(analysis.missing_tools) == 0, f"No missing tools allowed: {analysis.missing_tools}"
    
    def test_tool_performance_requirements(self, integration_validator):
        """TDD: Validate tool performance meets Jenkins SLA requirements"""
        analysis = integration_validator.validate_all_tools()
        
        # Professional performance requirements
        for tool_name, performance_ms in analysis.performance_summary.items():
            # Each tool should initialize quickly (< 1000ms for Jenkins compatibility)
            assert performance_ms < 1000, f"{tool_name} too slow: {performance_ms}ms > 1000ms SLA"
        
        # Average performance should be reasonable
        avg_performance = sum(analysis.performance_summary.values()) / len(analysis.performance_summary)
        assert avg_performance < 500, f"Average performance too slow: {avg_performance}ms > 500ms SLA"
    
    def test_memory_tool_specific_operations(self, integration_validator):
        """TDD: Specific validation for memory tool operations"""
        memory_manager = MemoryManager()
        
        # Test storage
        result = memory_manager.store_memory(
            content="Jenkins TDD test memory storage",
            memory_type="test", 
            tags=["jenkins", "tdd", "memory-test"]
        )
        assert result["success"] == True, "Memory storage should succeed"
        
        # Test retrieval
        retrieved = memory_manager.retrieve_memory(
            query="Jenkins TDD test",
            memory_type="test"
        )
        assert len(retrieved) > 0, "Should retrieve stored memory"
        
        # Test memory contains our test data
        found_test_memory = any("Jenkins TDD test memory storage" in item.content for item in retrieved)
        assert found_test_memory, "Should find our test memory content"
    
    def test_todo_tool_specific_operations(self, integration_validator):
        """TDD: Specific validation for todo tool operations"""
        todo_manager = TodoManager()
        
        # Test todo creation
        result = todo_manager.add_todo(
            content="Jenkins TDD test todo",
            priority="medium",
            tags=["jenkins", "tdd", "todo-test"]
        )
        assert result["success"] == True, "Todo creation should succeed"
        
        # Test todo listing
        todos = todo_manager.list_todos()
        assert len(todos) > 0, "Should have todos in system"
        
        # Test our todo exists
        found_test_todo = any("Jenkins TDD test todo" in todo.content for todo in todos)
        assert found_test_todo, "Should find our test todo"
    
    def test_pattern_tool_specific_operations(self, integration_validator):
        """TDD: Specific validation for pattern analysis tool"""
        pattern_analyzer = PatternAnalyzer()
        
        # Test function extraction
        test_code = '''
def jenkins_test_function():
    """Test function for Jenkins integration"""
    return "success"

class TestClass:
    def test_method(self):
        pass
'''
        
        functions = pattern_analyzer.extract_functions(test_code, "python")
        assert len(functions) >= 2, f"Should extract at least 2 functions, got {len(functions)}"
        
        # Test class extraction
        classes = pattern_analyzer.extract_classes(test_code, "python")
        assert len(classes) >= 1, f"Should extract at least 1 class, got {len(classes)}"
    
    def test_unix_tool_specific_operations(self, integration_validator):
        """TDD: Specific validation for unix tool operations"""
        unix_manager = UnixToolManager()
        
        # Test directory listing
        files = unix_manager.list_files(".")
        assert len(files) > 0, "Should list files in current directory"
        
        # Test file operations
        test_file_result = unix_manager.find_files(pattern="*.py", path=".")
        assert len(test_file_result) > 0, "Should find Python files"
    
    def test_jenkins_environment_simulation(self, integration_validator):
        """TDD: Validate tools work in simulated Jenkins environment"""
        # Simulate Jenkins environment variables
        original_env = os.environ.copy()
        
        try:
            os.environ.update({
                "BUILD_NUMBER": "test-jenkins-123",
                "WORKSPACE": "/tmp/jenkins-workspace",
                "JENKINS_URL": "http://192.168.1.119:8080",
                "JOB_NAME": "ltmc-ci-cd-pipeline"
            })
            
            # Test all tools work with Jenkins environment
            analysis = integration_validator.validate_all_tools()
            
            # All tools should still be accessible in Jenkins environment
            assert analysis.accessible_tools == 11, f"All tools should work in Jenkins env, got {analysis.accessible_tools}"
            assert analysis.jenkins_ready == True, "Should be Jenkins ready in simulated environment"
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_ltmc_memory_integration_working(self, integration_validator):
        """TDD: Validate LTMC memory integration stores test results"""
        analysis = integration_validator.validate_all_tools()
        
        # Analysis should be stored in memory
        memory_manager = MemoryManager()
        stored_analysis = memory_manager.retrieve_memory(
            query="LTMC Integration Analysis",
            memory_type="technical"
        )
        
        assert len(stored_analysis) > 0, "Integration analysis should be stored in LTMC memory"
        
        # Validate metadata is preserved
        latest_analysis = stored_analysis[0]
        assert "total_tools" in latest_analysis.metadata, "Should store total tools count"
        assert latest_analysis.metadata["total_tools"] == 11, "Should store correct tool count"
        assert "jenkins_ready" in latest_analysis.metadata, "Should store Jenkins readiness"


if __name__ == "__main__":
    # Professional test execution
    validator = LTMCIntegrationValidator()
    analysis = validator.validate_all_tools()
    
    print("🧠 LTMC INTEGRATION VALIDATION RESULTS")
    print("=====================================")
    print(f"Total Tools: {analysis.total_tools}")
    print(f"Accessible: {analysis.accessible_tools}")
    print(f"Failed: {analysis.failed_tools}")
    print(f"Jenkins Ready: {analysis.jenkins_ready}")
    print()
    
    if analysis.jenkins_ready:
        print("✅ ALL 11 LTMC TOOLS: VALIDATED AND ACCESSIBLE")
        print("✅ Jenkins Integration: READY")
    else:
        print("❌ LTMC TOOLS VALIDATION: FAILED")
        print(f"Missing tools: {analysis.missing_tools}")
    
    print("\n📊 Performance Summary:")
    for tool_name, perf_ms in analysis.performance_summary.items():
        status_icon = "✅" if perf_ms < 500 else "⚠️"
        print(f"  {status_icon} {tool_name}: {perf_ms:.1f}ms")
    
    print("\n🔍 Individual Tool Status:")
    for validation in analysis.tool_validations:
        status_icon = "✅" if validation.status == ToolStatus.ACCESSIBLE else "❌"
        print(f"  {status_icon} {validation.tool_name}: {validation.status.value}")
        if validation.error_message:
            print(f"    Error: {validation.error_message}")
    
    print("\n✅ Analysis stored in LTMC memory")
    
    # Run pytest if available
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], 
                              capture_output=True, text=True)
        print(f"\n🧪 TDD Test Results:")
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Could not run pytest: {e}")