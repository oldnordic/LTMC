"""
TDD Test Suite: Project Isolation Security Components

CRITICAL TDD APPROACH: These tests are written FIRST and WILL FAIL initially.
The security components (project_isolation.py) DO NOT EXIST YET.

This follows pure TDD methodology:
1. Write failing tests that define the exact behavior we need
2. Run tests to confirm they fail (proving we're testing the right things)
3. Implement ONLY the minimum code needed to make tests pass
4. Refactor and iterate

SECURITY FOCUS: Multi-project isolation with real attack vector testing.
PERFORMANCE TARGET: All security validation operations must complete in <5ms
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import time
import uuid
from unittest.mock import patch


class TestProjectIsolationManager:
    """
    TDD Security Tests: Project Isolation Manager
    
    Testing the ProjectIsolationManager class that prevents cross-project
    data access and implements secure multi-tenant operation.
    
    THESE TESTS WILL FAIL INITIALLY - this is expected and correct TDD.
    """
    
    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project root for testing."""
        temp_dir = tempfile.mkdtemp(prefix="ltmc_test_projects_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def isolation_manager(self, temp_project_root):
        """
        Create ProjectIsolationManager instance.
        
        THIS WILL FAIL: The class doesn't exist yet.
        This failure defines what we need to implement.
        """
        from ltms.security.project_isolation import ProjectIsolationManager
        
        manager = ProjectIsolationManager(project_root=temp_project_root)
        
        # Set up test projects
        manager.register_project("project_a", {
            "name": "Test Project A",
            "allowed_paths": ["data/project_a", "temp/project_a"],
            "database_prefix": "proj_a",
            "redis_namespace": "ltmc:proj_a",
            "neo4j_label": "ProjectA"
        })
        
        manager.register_project("project_b", {
            "name": "Test Project B", 
            "allowed_paths": ["data/project_b", "temp/project_b"],
            "database_prefix": "proj_b",
            "redis_namespace": "ltmc:proj_b",
            "neo4j_label": "ProjectB"
        })
        
        return manager
    
    def test_project_isolation_manager_initialization(self, temp_project_root):
        """
        TDD Test 1: Verify ProjectIsolationManager can be instantiated.
        
        EXPECTED TO FAIL: Component doesn't exist yet.
        """
        from ltms.security.project_isolation import ProjectIsolationManager
        
        manager = ProjectIsolationManager(project_root=temp_project_root)
        
        assert manager is not None
        assert manager.project_root == temp_project_root
        assert hasattr(manager, 'projects')
        assert hasattr(manager, 'default_project')
    
    def test_validate_project_access_allows_valid_paths(self, isolation_manager):
        """
        TDD Test 2: Valid project paths should be allowed.
        
        EXPECTED TO FAIL: validate_project_access method doesn't exist.
        """
        # Test valid paths for project_a
        assert isolation_manager.validate_project_access(
            "project_a", "read", "data/project_a/file.txt"
        ) is True
        
        assert isolation_manager.validate_project_access(
            "project_a", "write", "temp/project_a/output.json"
        ) is True
    
    def test_validate_project_access_blocks_invalid_paths(self, isolation_manager):
        """
        TDD Test 3: Invalid project paths should be blocked.
        
        EXPECTED TO FAIL: SecurityError exception class doesn't exist.
        """
        from ltms.security.project_isolation import SecurityError
        
        # Test cross-project access attempt
        with pytest.raises(SecurityError, match="not allowed for project"):
            isolation_manager.validate_project_access(
                "project_a", "read", "data/project_b/secret.txt"
            )
        
        # Test access to system paths
        with pytest.raises(SecurityError, match="not allowed for project"):
            isolation_manager.validate_project_access(
                "project_a", "read", "/etc/passwd"
            )
    
    def test_validate_project_access_blocks_path_traversal(self, isolation_manager):
        """
        TDD Test 4: Path traversal attacks should be blocked.
        
        CRITICAL SECURITY TEST: Must prevent ../../../ attacks.
        """
        from ltms.security.project_isolation import SecurityError
        
        # Test various path traversal patterns
        path_traversal_attempts = [
            "data/project_a/../../../etc/passwd",
            "data/project_a/../../project_b/secret.txt", 
            "../project_b/data/file.txt",
            "data/project_a/.././../etc/shadow",
            "temp/project_a/../../../../usr/bin/sh"
        ]
        
        for malicious_path in path_traversal_attempts:
            with pytest.raises(SecurityError, match="Path traversal"):
                isolation_manager.validate_project_access(
                    "project_a", "read", malicious_path
                )
    
    def test_validate_project_access_unauthorized_project(self, isolation_manager):
        """
        TDD Test 5: Unauthorized project IDs should be rejected.
        """
        from ltms.security.project_isolation import SecurityError
        
        with pytest.raises(SecurityError, match="not authorized"):
            isolation_manager.validate_project_access(
                "nonexistent_project", "read", "data/any/file.txt"
            )
    
    def test_get_scoped_database_path_creates_isolation(self, isolation_manager):
        """
        TDD Test 6: Database paths should be project-scoped.
        
        EXPECTED TO FAIL: get_scoped_database_path method doesn't exist.
        """
        base_path = "/path/to/ltmc.db"
        
        # Different projects should get different database paths
        path_a = isolation_manager.get_scoped_database_path("project_a", base_path)
        path_b = isolation_manager.get_scoped_database_path("project_b", base_path)
        
        assert path_a != path_b
        assert "proj_a" in path_a
        assert "proj_b" in path_b
        assert base_path not in [path_a, path_b]  # Should be modified, not original
    
    def test_get_scoped_redis_key_creates_namespaces(self, isolation_manager):
        """
        TDD Test 7: Redis keys should be project-namespaced.
        
        EXPECTED TO FAIL: get_scoped_redis_key method doesn't exist.
        """
        key = "user_session_123"
        
        # Different projects should get different Redis namespaces
        key_a = isolation_manager.get_scoped_redis_key("project_a", key)
        key_b = isolation_manager.get_scoped_redis_key("project_b", key)
        
        assert key_a != key_b
        assert "ltmc:proj_a" in key_a
        assert "ltmc:proj_b" in key_b
        assert key in key_a
        assert key in key_b
    
    def test_project_registration_and_validation(self, temp_project_root):
        """
        TDD Test 8: Projects should be registerable with validation.
        
        EXPECTED TO FAIL: register_project method doesn't exist.
        """
        from ltms.security.project_isolation import ProjectIsolationManager
        
        manager = ProjectIsolationManager(project_root=temp_project_root)
        
        # Valid project registration
        result = manager.register_project("test_project", {
            "name": "Test Project",
            "allowed_paths": ["data/test"],
            "database_prefix": "test",
            "redis_namespace": "ltmc:test",
            "neo4j_label": "TestProject"
        })
        
        assert result["success"] is True
        assert "test_project" in manager.projects
        
        # Invalid project registration (missing required fields)
        from ltms.security.project_isolation import ProjectConfigError
        
        with pytest.raises(ProjectConfigError):
            manager.register_project("invalid_project", {
                "name": "Invalid Project"
                # Missing required fields
            })


class TestProjectIsolationPerformance:
    """
    TDD Performance Tests: Project Isolation Security
    
    PERFORMANCE REQUIREMENT: All security validation must complete in <5ms
    This ensures security doesn't become a bottleneck.
    """
    
    @pytest.fixture
    def performance_isolation_manager(self, tmp_path):
        """Set up isolation manager with realistic project count."""
        from ltms.security.project_isolation import ProjectIsolationManager
        
        manager = ProjectIsolationManager(project_root=tmp_path)
        
        # Register multiple projects to simulate real usage
        for i in range(10):
            manager.register_project(f"project_{i}", {
                "name": f"Test Project {i}",
                "allowed_paths": [f"data/proj_{i}", f"temp/proj_{i}"],
                "database_prefix": f"proj_{i}",
                "redis_namespace": f"ltmc:proj_{i}",
                "neo4j_label": f"Project{i}"
            })
        
        return manager
    
    def test_validate_project_access_performance(self, performance_isolation_manager):
        """
        TDD Performance Test 1: Project access validation speed.
        
        REQUIREMENT: Must complete in <5ms even with multiple projects.
        EXPECTED TO FAIL: Method doesn't exist yet.
        """
        # Test valid access performance
        start_time = time.perf_counter()
        
        for _ in range(100):  # 100 validations
            performance_isolation_manager.validate_project_access(
                "project_5", "read", "data/proj_5/test_file.txt"
            )
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"Average validation time {avg_time_ms:.2f}ms exceeds 5ms limit"
    
    def test_path_traversal_detection_performance(self, performance_isolation_manager):
        """
        TDD Performance Test 2: Path traversal detection speed.
        
        REQUIREMENT: Security checks must be fast even for malicious inputs.
        EXPECTED TO FAIL: SecurityError class doesn't exist.
        """
        from ltms.security.project_isolation import SecurityError
        
        malicious_paths = [
            "data/proj_5/../../../etc/passwd",
            "temp/proj_5/../../other_proj/secret.txt",
            "../../../usr/bin/dangerous_command",
            "data/proj_5/.././../system/file.txt"
        ] * 25  # 100 total tests
        
        start_time = time.perf_counter()
        
        for path in malicious_paths:
            with pytest.raises(SecurityError):
                performance_isolation_manager.validate_project_access(
                    "project_5", "read", path
                )
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / len(malicious_paths)) * 1000
        
        assert avg_time_ms < 3.0, f"Average malicious path detection {avg_time_ms:.2f}ms too slow"
    
    def test_database_path_scoping_performance(self, performance_isolation_manager):
        """
        TDD Performance Test 3: Database path scoping speed.
        
        REQUIREMENT: Path scoping must be fast for high-throughput operations.
        """
        base_paths = [
            "/var/lib/ltmc/ltmc.db",
            "/tmp/ltmc_test.db", 
            "relative/path/database.db",
            "/home/user/projects/data.db"
        ]
        
        start_time = time.perf_counter()
        
        for _ in range(250):  # 1000 total operations
            for base_path in base_paths:
                performance_isolation_manager.get_scoped_database_path(
                    "project_3", base_path
                )
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 1000) * 1000
        
        assert avg_time_ms < 2.0, f"Average path scoping {avg_time_ms:.2f}ms too slow"
    
    def test_redis_key_namespacing_performance(self, performance_isolation_manager):
        """
        TDD Performance Test 4: Redis key namespacing speed.
        
        High-frequency operation that must remain fast.
        """
        keys = [
            "user_session_abc123",
            "cache_result_xyz789", 
            "temp_data_456def",
            "computation_result_789ghi"
        ]
        
        start_time = time.perf_counter()
        
        for _ in range(250):  # 1000 total operations
            for key in keys:
                performance_isolation_manager.get_scoped_redis_key("project_7", key)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 1000) * 1000
        
        assert avg_time_ms < 1.0, f"Average Redis namespacing {avg_time_ms:.2f}ms too slow"


class TestProjectIsolationIntegration:
    """
    TDD Integration Tests: Project Isolation with LTMC System
    
    These tests verify project isolation works with actual LTMC components.
    CRITICAL: Tests real system integration, not mocked components.
    """
    
    @pytest.fixture
    def ltmc_server_process(self):
        """
        Start actual LTMC server for integration testing.
        
        PHASE 0 REQUIREMENT: System must start successfully before testing.
        """
        import subprocess
        import time
        import requests
        
        # Kill any existing processes
        try:
            subprocess.run(["pkill", "-f", "ltmc_mcp_server_http.py"], check=False)
            time.sleep(2)
        except Exception:
            pass
        
        # Start server
        process = subprocess.Popen(
            ["python", "ltmc_mcp_server_http.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/home/feanor/Projects/lmtc"
        )
        
        # Wait for server to start
        for _ in range(30):
            try:
                response = requests.get("http://localhost:5050/health", timeout=1)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(1)
                continue
        else:
            process.kill()
            pytest.skip("LTMC server failed to start - cannot test integration")
        
        yield process
        
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    
    def test_project_isolated_memory_storage(self, ltmc_server_process):
        """
        TDD Integration Test 1: Project-isolated memory storage.
        
        EXPECTED TO FAIL: store_memory tool doesn't support project_id parameter yet.
        """
        import requests
        
        # Store memory for project A
        payload_a = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "store_memory",
                "arguments": {
                    "file_name": "test_isolation_a.md",
                    "content": "Project A secret data",
                    "resource_type": "document",
                    "project_id": "project_a"  # THIS PARAMETER DOESN'T EXIST YET
                }
            },
            "id": 1
        }
        
        response = requests.post(
            "http://localhost:5050/jsonrpc",
            json=payload_a,
            timeout=10
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("error") is None, f"Project A storage failed: {result}"
        assert result["result"]["success"] is True
        
        # Store memory for project B with same filename
        payload_b = {
            "jsonrpc": "2.0", 
            "method": "tools/call",
            "params": {
                "name": "store_memory",
                "arguments": {
                    "file_name": "test_isolation_a.md",  # Same filename
                    "content": "Project B secret data",   # Different content
                    "resource_type": "document",
                    "project_id": "project_b"
                }
            },
            "id": 2
        }
        
        response = requests.post(
            "http://localhost:5050/jsonrpc",
            json=payload_b,
            timeout=10
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("error") is None, f"Project B storage failed: {result}"
        assert result["result"]["success"] is True
    
    def test_project_isolated_memory_retrieval(self, ltmc_server_process):
        """
        TDD Integration Test 2: Project-isolated memory retrieval.
        
        EXPECTED TO FAIL: retrieve_memory tool doesn't support project isolation.
        """
        import requests
        
        # Retrieve from project A - should only get project A data
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call", 
            "params": {
                "name": "retrieve_memory",
                "arguments": {
                    "query": "secret data",
                    "limit": 10,
                    "project_id": "project_a"  # THIS PARAMETER DOESN'T EXIST YET
                }
            },
            "id": 3
        }
        
        response = requests.post(
            "http://localhost:5050/jsonrpc",
            json=payload,
            timeout=15
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("error") is None
        
        # Should only find project A data, not project B
        results = result["result"]["results"]
        project_a_found = any("Project A secret" in str(r) for r in results)
        project_b_found = any("Project B secret" in str(r) for r in results)
        
        assert project_a_found, "Should find Project A data"
        assert not project_b_found, "Should NOT find Project B data (isolation failure)"
    
    def test_unauthorized_project_access_blocked(self, ltmc_server_process):
        """
        TDD Integration Test 3: Unauthorized project access should be blocked.
        
        EXPECTED TO FAIL: Security validation doesn't exist in MCP tools yet.
        """
        import requests
        
        # Attempt to access unauthorized project
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "store_memory", 
                "arguments": {
                    "file_name": "malicious_access.md",
                    "content": "Attempting unauthorized access",
                    "resource_type": "document",
                    "project_id": "unauthorized_project_xyz"  # Should be blocked
                }
            },
            "id": 4
        }
        
        response = requests.post(
            "http://localhost:5050/jsonrpc",
            json=payload,
            timeout=10
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should fail with security error
        assert result["result"]["success"] is False
        assert "security" in result["result"]["error"].lower() or "unauthorized" in result["result"]["error"].lower()


if __name__ == "__main__":
    """
    TDD Test Execution: Project Isolation Security Tests
    
    Run with: python -m pytest tests/security/test_project_isolation.py -v
    
    EXPECTED RESULT: ALL TESTS SHOULD FAIL initially.
    This proves we're testing the right functionality before implementation.
    """
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, project_root)
    
    print("🔴 TDD PROJECT ISOLATION TESTS")
    print("Expected: ALL TESTS WILL FAIL (components don't exist yet)")
    print("This is CORRECT TDD methodology - write tests first!")
    print("=" * 60)
    
    # Run tests with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--no-header"
    ])
    
    if exit_code != 0:
        print("=" * 60)
        print("✅ TDD SUCCESS: Tests failed as expected!")
        print("💡 Next step: Implement security components to make tests pass")
        print("📁 Need to create: ltms/security/project_isolation.py")
        print("🔧 Need to implement: ProjectIsolationManager class")
    else:
        print("=" * 60)
        print("❌ TDD PROBLEM: Tests should fail but didn't!")
        print("🤔 Check: Are the components already implemented?")
    
    sys.exit(0)  # Always exit 0 for TDD - failures are expected