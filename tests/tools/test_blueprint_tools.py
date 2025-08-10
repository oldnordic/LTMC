"""
Test module for Blueprint MCP Tools.

Tests the Blueprint MCP tools including:
- create_task_blueprint MCP tool
- analyze_task_complexity MCP tool  
- get_task_dependencies MCP tool
- update_blueprint_metadata MCP tool
- list_project_blueprints MCP tool
- Phase 1 security integration
- Performance requirements (<5ms tool execution)

Following TDD methodology - tests written first.
"""

import pytest
import tempfile
import os
import time
import json
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch

# Import existing LTMC infrastructure
from ltms.database.schema import create_tables
from ltms.database.connection import get_db_connection

# Import security components (Phase 1 integration)
from ltms.security.project_isolation import ProjectIsolationManager
from ltms.security.path_security import SecurePathValidator

# Import the tools we're about to create (will fail initially - that's TDD!)
from ltms.tools.blueprint_tools import (
    create_task_blueprint,
    analyze_task_complexity,
    get_task_dependencies,
    update_blueprint_metadata,
    list_project_blueprints,
    resolve_blueprint_execution_order,
    delete_task_blueprint,
    add_blueprint_dependency,
    BlueprintToolError
)

# Import models and services we've created
from ltms.models.task_blueprint import (
    TaskBlueprint,
    TaskComplexity,
    TaskMetadata,
    ComplexityScorer
)
from ltms.services.blueprint_service import BlueprintManager


class TestCreateTaskBlueprintTool:
    """Test create_task_blueprint MCP tool."""
    
    @pytest.fixture
    def setup_test_environment(self):
        """Setup test database and security context."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        BlueprintManager.create_blueprint_tables(conn)
        
        # Setup security context
        project_manager = ProjectIsolationManager()
        path_validator = SecurePathValidator()
        
        yield conn, db_path, project_manager, path_validator
        
        conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_create_task_blueprint_basic(self, setup_test_environment):
        """Test creating a basic task blueprint via MCP tool."""
        conn, db_path, project_manager, path_validator = setup_test_environment
        
        # Tool parameters
        args = {
            "title": "Implement user authentication",
            "description": "Create JWT-based authentication system with refresh tokens",
            "estimated_duration_minutes": 120,
            "required_skills": ["python", "jwt", "security"],
            "priority_score": 0.8,
            "tags": ["authentication", "security", "backend"],
            "project_id": "test_project_123"
        }
        
        # Test tool execution performance
        start_time = time.perf_counter()
        result = create_task_blueprint(**args)
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Performance requirement: <5ms
        assert execution_time_ms < 5.0, f"Tool execution took {execution_time_ms:.2f}ms, exceeds 5ms limit"
        
        # Verify result structure
        assert result["success"] is True
        assert "blueprint_id" in result
        assert "complexity" in result
        assert "complexity_score" in result
        assert result["title"] == args["title"]
        assert result["project_id"] == args["project_id"]
        
        # Verify complexity assignment
        assert result["complexity"] in ["TRIVIAL", "SIMPLE", "MODERATE", "COMPLEX", "CRITICAL"]
        assert 0.0 <= result["complexity_score"] <= 1.0
    
    def test_create_task_blueprint_with_security_validation(self, setup_test_environment):
        """Test blueprint creation with Phase 1 security validation."""
        conn, db_path, project_manager, path_validator = setup_test_environment
        
        # Valid project_id should work
        valid_args = {
            "title": "Secure Task",
            "description": "Testing security validation",
            "project_id": "valid_project_123"
        }
        
        result = create_task_blueprint(**valid_args)
        assert result["success"] is True
        assert result["project_id"] == "valid_project_123"
        
        # Invalid project_id should be sanitized or rejected
        invalid_args = {
            "title": "Potentially Unsafe Task",
            "description": "Testing security validation",
            "project_id": "../../../etc/passwd"  # Path traversal attempt
        }
        
        # Should either sanitize the project_id or fail gracefully
        result = create_task_blueprint(**invalid_args)
        
        if result["success"]:
            # If it succeeds, project_id should be sanitized
            assert "../" not in result["project_id"]
            assert "etc" not in result["project_id"]
        else:
            # If it fails, should have appropriate error
            assert "error" in result
            assert "security" in result["error"].lower() or "invalid" in result["error"].lower()
    
    def test_create_task_blueprint_input_validation(self, setup_test_environment):
        """Test input validation for create_task_blueprint tool."""
        conn, db_path, project_manager, path_validator = setup_test_environment
        
        # Test missing required fields
        invalid_args = {
            "description": "Missing title"
        }
        
        result = create_task_blueprint(**invalid_args)
        assert result["success"] is False
        assert "error" in result
        assert "title" in result["error"].lower()
        
        # Test invalid priority_score
        invalid_priority_args = {
            "title": "Test Task",
            "description": "Test description",
            "priority_score": 1.5  # Invalid - should be <= 1.0
        }
        
        result = create_task_blueprint(**invalid_priority_args)
        assert result["success"] is False
        assert "error" in result
        assert "priority" in result["error"].lower()
    
    def test_create_task_blueprint_with_metadata(self, setup_test_environment):
        """Test creating blueprint with comprehensive metadata."""
        conn, db_path, project_manager, path_validator = setup_test_environment
        
        args = {
            "title": "Complex API Implementation",
            "description": "Implement RESTful API with advanced features",
            "estimated_duration_minutes": 480,
            "required_skills": ["python", "fastapi", "postgresql", "redis", "docker"],
            "priority_score": 0.9,
            "tags": ["api", "backend", "microservices", "critical"],
            "resource_requirements": {
                "memory": "4GB",
                "cpu": "4 cores",
                "storage": "20GB"
            },
            "project_id": "complex_project"
        }
        
        result = create_task_blueprint(**args)
        
        assert result["success"] is True
        assert result["estimated_duration_minutes"] == 480
        assert "python" in result["required_skills"]
        assert "api" in result["tags"]
        assert result["priority_score"] == 0.9
        
        # Verify resource requirements are stored
        if "resource_requirements" in result:
            assert result["resource_requirements"]["memory"] == "4GB"


class TestAnalyzeTaskComplexityTool:
    """Test analyze_task_complexity MCP tool."""
    
    def test_analyze_task_complexity_basic(self):
        """Test basic complexity analysis."""
        args = {
            "title": "Fix documentation typo",
            "description": "Correct spelling error in README file",
            "required_skills": ["documentation"]
        }
        
        start_time = time.perf_counter()
        result = analyze_task_complexity(**args)
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Performance requirement
        assert execution_time_ms < 50.0, f"Complexity analysis took {execution_time_ms:.2f}ms, too slow"
        
        # Verify result structure
        assert result["success"] is True
        assert "complexity" in result
        assert "complexity_score" in result
        assert "reasoning" in result
        
        # Simple task should have low complexity
        assert result["complexity"] in ["TRIVIAL", "SIMPLE"]
        assert result["complexity_score"] < 0.4
    
    def test_analyze_task_complexity_complex_task(self):
        """Test complexity analysis for complex task."""
        args = {
            "title": "Implement distributed microservices architecture",
            "description": """
            Design and implement a complete microservices architecture including:
            - Event-driven communication using Apache Kafka
            - CQRS pattern with separate read/write databases
            - Circuit breaker pattern for fault tolerance
            - Distributed tracing with OpenTelemetry
            - OAuth2/JWT authentication and authorization
            - Real-time data streaming and processing
            """,
            "required_skills": [
                "kafka", "microservices", "cqrs", "circuit-breaker",
                "oauth2", "distributed-systems", "kubernetes", "docker"
            ]
        }
        
        result = analyze_task_complexity(**args)
        
        assert result["success"] is True
        
        # Complex task should have high complexity
        assert result["complexity"] in ["COMPLEX", "CRITICAL"]
        assert result["complexity_score"] > 0.6
        
        # Should include reasoning
        assert len(result["reasoning"]) > 50  # Non-trivial explanation
        assert any(skill in result["reasoning"].lower() for skill in ["kafka", "microservices", "complex"])
    
    def test_analyze_task_complexity_with_caching(self):
        """Test that complexity analysis uses caching for performance."""
        args = {
            "title": "Test caching",
            "description": "Testing complexity analysis caching",
            "required_skills": ["testing"]
        }
        
        # First call
        start_time = time.perf_counter()
        result1 = analyze_task_complexity(**args)
        first_time = time.perf_counter() - start_time
        
        # Second identical call
        start_time = time.perf_counter()
        result2 = analyze_task_complexity(**args)
        second_time = time.perf_counter() - start_time
        
        # Results should be identical
        assert result1["complexity_score"] == result2["complexity_score"]
        assert result1["complexity"] == result2["complexity"]
        
        # Second call should be faster (or at least not significantly slower)
        assert second_time <= first_time * 2.0, "Caching not working effectively"


class TestGetTaskDependenciesTool:
    """Test get_task_dependencies MCP tool."""
    
    @pytest.fixture
    def setup_with_dependencies(self):
        """Setup test environment with blueprint dependencies."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        BlueprintManager.create_blueprint_tables(conn)
        
        manager = BlueprintManager(conn)
        
        # Create test blueprints with dependencies
        bp_auth = manager.create_blueprint(
            title="Authentication System",
            description="Basic auth implementation"
        )
        
        bp_database = manager.create_blueprint(
            title="Database Setup", 
            description="Initial database schema"
        )
        
        bp_api = manager.create_blueprint(
            title="User API",
            description="API requiring auth and database"
        )
        
        # Add dependencies
        manager.add_dependency(bp_api.blueprint_id, bp_auth.blueprint_id, "blocking", True)
        manager.add_dependency(bp_api.blueprint_id, bp_database.blueprint_id, "blocking", True)
        
        yield conn, db_path, {
            "auth": bp_auth.blueprint_id,
            "database": bp_database.blueprint_id,
            "api": bp_api.blueprint_id
        }
        
        conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_get_task_dependencies_basic(self, setup_with_dependencies):
        """Test getting task dependencies."""
        conn, db_path, blueprint_ids = setup_with_dependencies
        
        result = get_task_dependencies(blueprint_id=blueprint_ids["api"])
        
        assert result["success"] is True
        assert "dependencies" in result
        assert len(result["dependencies"]) == 2
        
        # Verify dependency structure
        for dep in result["dependencies"]:
            assert "prerequisite_task_id" in dep
            assert "dependency_type" in dep
            assert "is_critical" in dep
            assert dep["prerequisite_task_id"] in [blueprint_ids["auth"], blueprint_ids["database"]]
    
    def test_get_task_dependencies_not_found(self, setup_with_dependencies):
        """Test getting dependencies for non-existent blueprint."""
        conn, db_path, blueprint_ids = setup_with_dependencies
        
        result = get_task_dependencies(blueprint_id="non_existent_blueprint")
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_get_task_dependencies_no_dependencies(self, setup_with_dependencies):
        """Test getting dependencies for blueprint with no dependencies."""
        conn, db_path, blueprint_ids = setup_with_dependencies
        
        result = get_task_dependencies(blueprint_id=blueprint_ids["auth"])
        
        assert result["success"] is True
        assert "dependencies" in result
        assert len(result["dependencies"]) == 0


class TestUpdateBlueprintMetadataTool:
    """Test update_blueprint_metadata MCP tool."""
    
    @pytest.fixture
    def setup_with_blueprint(self):
        """Setup test environment with a blueprint to update."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        BlueprintManager.create_blueprint_tables(conn)
        
        manager = BlueprintManager(conn)
        
        # Create test blueprint
        blueprint = manager.create_blueprint(
            title="Test Blueprint",
            description="Testing metadata updates",
            metadata=TaskMetadata(
                estimated_duration_minutes=60,
                required_skills=["python"],
                priority_score=0.5,
                tags=["test"]
            )
        )
        
        yield conn, db_path, blueprint.blueprint_id
        
        conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_update_blueprint_metadata_basic(self, setup_with_blueprint):
        """Test updating blueprint metadata."""
        conn, db_path, blueprint_id = setup_with_blueprint
        
        args = {
            "blueprint_id": blueprint_id,
            "estimated_duration_minutes": 120,
            "required_skills": ["python", "fastapi", "postgresql"],
            "priority_score": 0.8,
            "tags": ["test", "api", "database"]
        }
        
        result = update_blueprint_metadata(**args)
        
        assert result["success"] is True
        assert result["estimated_duration_minutes"] == 120
        assert "fastapi" in result["required_skills"]
        assert result["priority_score"] == 0.8
        assert "api" in result["tags"]
    
    def test_update_blueprint_metadata_partial(self, setup_with_blueprint):
        """Test partial metadata updates."""
        conn, db_path, blueprint_id = setup_with_blueprint
        
        # Update only priority score
        args = {
            "blueprint_id": blueprint_id,
            "priority_score": 0.9
        }
        
        result = update_blueprint_metadata(**args)
        
        assert result["success"] is True
        assert result["priority_score"] == 0.9
        # Other fields should remain unchanged
        assert result["estimated_duration_minutes"] == 60  # Original value
        assert "python" in result["required_skills"]  # Original value
    
    def test_update_blueprint_metadata_validation(self, setup_with_blueprint):
        """Test metadata validation during updates."""
        conn, db_path, blueprint_id = setup_with_blueprint
        
        # Invalid priority score
        args = {
            "blueprint_id": blueprint_id,
            "priority_score": 1.5  # Invalid
        }
        
        result = update_blueprint_metadata(**args)
        
        assert result["success"] is False
        assert "error" in result
        assert "priority" in result["error"].lower()


class TestListProjectBlueprintsTool:
    """Test list_project_blueprints MCP tool."""
    
    @pytest.fixture
    def setup_with_multiple_blueprints(self):
        """Setup test environment with multiple blueprints."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        BlueprintManager.create_blueprint_tables(conn)
        
        manager = BlueprintManager(conn)
        
        # Create blueprints for different projects
        project_a_blueprints = []
        for i in range(3):
            bp = manager.create_blueprint(
                title=f"Project A Task {i}",
                description=f"Task {i} for project A",
                project_id="project_a"
            )
            project_a_blueprints.append(bp.blueprint_id)
        
        project_b_blueprints = []
        for i in range(2):
            bp = manager.create_blueprint(
                title=f"Project B Task {i}",
                description=f"Task {i} for project B",
                project_id="project_b"
            )
            project_b_blueprints.append(bp.blueprint_id)
        
        yield conn, db_path, {
            "project_a": project_a_blueprints,
            "project_b": project_b_blueprints
        }
        
        conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_list_project_blueprints_basic(self, setup_with_multiple_blueprints):
        """Test listing blueprints for a specific project."""
        conn, db_path, blueprint_data = setup_with_multiple_blueprints
        
        result = list_project_blueprints(project_id="project_a")
        
        assert result["success"] is True
        assert "blueprints" in result
        assert len(result["blueprints"]) == 3
        
        # Verify all blueprints belong to project_a
        for bp in result["blueprints"]:
            assert bp["project_id"] == "project_a"
            assert "Project A Task" in bp["title"]
    
    def test_list_project_blueprints_with_filters(self, setup_with_multiple_blueprints):
        """Test listing blueprints with complexity and tag filters."""
        conn, db_path, blueprint_data = setup_with_multiple_blueprints
        
        # Test with limit
        result = list_project_blueprints(project_id="project_a", limit=2)
        
        assert result["success"] is True
        assert len(result["blueprints"]) == 2
    
    def test_list_project_blueprints_empty_project(self, setup_with_multiple_blueprints):
        """Test listing blueprints for project with no blueprints."""
        conn, db_path, blueprint_data = setup_with_multiple_blueprints
        
        result = list_project_blueprints(project_id="empty_project")
        
        assert result["success"] is True
        assert "blueprints" in result
        assert len(result["blueprints"]) == 0


class TestBlueprintToolSecurity:
    """Test security integration for all blueprint tools."""
    
    def test_blueprint_tools_project_isolation(self):
        """Test that all blueprint tools respect project isolation."""
        # This will test Phase 1 security integration
        pytest.skip("Requires complete security integration")
    
    def test_blueprint_tools_input_sanitization(self):
        """Test input sanitization for all blueprint tools."""
        # Test various injection attacks and malformed inputs
        pytest.skip("Requires security testing implementation")


class TestBlueprintToolPerformance:
    """Test performance requirements for blueprint tools."""
    
    def test_blueprint_tools_performance_requirements(self):
        """Test that all blueprint tools meet <5ms performance requirement."""
        # Simple operations for performance testing
        test_cases = [
            ("create_task_blueprint", {
                "title": "Performance Test",
                "description": "Testing tool performance"
            }),
            ("analyze_task_complexity", {
                "title": "Performance Test",
                "description": "Testing complexity analysis performance"
            })
        ]
        
        for tool_name, args in test_cases:
            start_time = time.perf_counter()
            
            if tool_name == "create_task_blueprint":
                result = create_task_blueprint(**args)
            elif tool_name == "analyze_task_complexity":
                result = analyze_task_complexity(**args)
            
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            assert execution_time_ms < 5.0, f"{tool_name} took {execution_time_ms:.2f}ms, exceeds 5ms limit"
            assert result["success"] is True, f"{tool_name} failed: {result.get('error', 'Unknown error')}"


class TestBlueprintToolErrors:
    """Test error handling for blueprint tools."""
    
    def test_blueprint_tool_error_hierarchy(self):
        """Test custom error classes for blueprint tools."""
        error = BlueprintToolError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_blueprint_tools_graceful_error_handling(self):
        """Test that all tools handle errors gracefully."""
        # Test various error conditions and ensure tools return proper error responses
        pytest.skip("Requires complete tool implementation")


# Integration tests requiring full system
class TestBlueprintToolsIntegration:
    """Integration tests for blueprint tools with complete system."""
    
    def test_blueprint_tools_mcp_protocol_compliance(self):
        """Test that blueprint tools follow MCP protocol standards."""
        pytest.skip("Requires MCP server integration")
    
    def test_blueprint_tools_redis_caching_integration(self):
        """Test blueprint tools with Redis caching."""
        pytest.skip("Requires Redis integration")
    
    def test_blueprint_tools_end_to_end_workflow(self):
        """Test complete blueprint workflow using all tools."""
        pytest.skip("Requires complete system integration")