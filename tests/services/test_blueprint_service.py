"""
Test module for BlueprintService and related functionality.

Tests the BlueprintService system including:
- BlueprintManager CRUD operations
- Database schema integration
- Complexity analysis engine
- Dependency resolution algorithms
- Redis caching integration
- Performance requirements (<5ms blueprint creation)
- Security integration with Phase 1

Following TDD methodology - tests written first.
"""

import pytest
import tempfile
import os
import time
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

# Import existing LTMC infrastructure
from ltms.database.schema import create_tables
from ltms.database.connection import get_db_connection

# Import the services we're about to create (will fail initially - that's TDD!)
from ltms.services.blueprint_service import (
    BlueprintManager,
    BlueprintServiceError,
    BlueprintNotFoundError,
    DependencyResolutionError
)

# Import models we just created
from ltms.models.task_blueprint import (
    TaskBlueprint,
    TaskComplexity,
    TaskDependency,
    TaskMetadata,
    ComplexityScorer,
    BlueprintValidationError
)


class TestBlueprintManager:
    """Test BlueprintManager core functionality."""
    
    @pytest.fixture
    def setup_test_db(self):
        """Setup test database with blueprint tables."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        conn = get_db_connection(db_path)
        create_tables(conn)  # Create existing LTMC tables
        
        # Create blueprint-specific tables (to be implemented)
        BlueprintManager.create_blueprint_tables(conn)
        
        yield conn, db_path
        
        conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_blueprint_manager_initialization(self, setup_test_db):
        """Test BlueprintManager initialization with database connection."""
        conn, db_path = setup_test_db
        
        manager = BlueprintManager(conn)
        assert manager is not None
        assert manager.connection == conn
        assert hasattr(manager, 'complexity_scorer')
        assert isinstance(manager.complexity_scorer, ComplexityScorer)
    
    def test_create_blueprint_basic(self, setup_test_db):
        """Test creating a basic blueprint via BlueprintManager."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        metadata = TaskMetadata(
            estimated_duration_minutes=45,
            required_skills=["python", "fastapi"],
            priority_score=0.7,
            tags=["api", "backend"]
        )
        
        blueprint_data = {
            "title": "Create user authentication API",
            "description": "Implement JWT-based authentication with refresh tokens",
            "metadata": metadata,
            "project_id": "project_123"
        }
        
        # Test creation performance
        start_time = time.perf_counter()
        blueprint = manager.create_blueprint(**blueprint_data)
        creation_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify creation performance requirement
        assert creation_time_ms < 5.0, f"Blueprint creation took {creation_time_ms:.2f}ms, exceeds 5ms limit"
        
        # Verify blueprint properties
        assert blueprint.blueprint_id is not None
        assert blueprint.title == "Create user authentication API"
        assert blueprint.project_id == "project_123"
        assert blueprint.complexity in TaskComplexity
        assert blueprint.metadata.estimated_duration_minutes == 45
    
    def test_create_blueprint_with_auto_complexity(self, setup_test_db):
        """Test blueprint creation with automatic complexity scoring."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        # Complex task description should get high complexity
        complex_blueprint = manager.create_blueprint(
            title="Implement distributed microservices architecture",
            description="""
            Design and implement a complete microservices architecture with:
            - Event-driven communication using Apache Kafka
            - CQRS pattern with separate read/write databases
            - Circuit breaker pattern for fault tolerance
            - Distributed tracing with OpenTelemetry
            - OAuth2/JWT authentication and authorization
            """,
            metadata=TaskMetadata(
                required_skills=["kafka", "microservices", "oauth2", "distributed-systems", "cqrs"]
            )
        )
        
        # Simple task description should get low complexity
        simple_blueprint = manager.create_blueprint(
            title="Fix typo in README",
            description="Fix spelling error in documentation",
            metadata=TaskMetadata(required_skills=["documentation"])
        )
        
        # Verify complexity assignment
        assert complex_blueprint.complexity.score > simple_blueprint.complexity.score
        assert complex_blueprint.complexity in [TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]
        assert simple_blueprint.complexity in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]
    
    def test_get_blueprint_by_id(self, setup_test_db):
        """Test retrieving blueprint by ID."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        # Create a blueprint
        original = manager.create_blueprint(
            title="Test Blueprint",
            description="Testing blueprint retrieval",
            metadata=TaskMetadata(priority_score=0.8)
        )
        
        # Retrieve by ID
        retrieved = manager.get_blueprint(original.blueprint_id)
        
        assert retrieved is not None
        assert retrieved.blueprint_id == original.blueprint_id
        assert retrieved.title == original.title
        assert retrieved.description == original.description
        assert retrieved.complexity == original.complexity
    
    def test_get_blueprint_not_found(self, setup_test_db):
        """Test retrieving non-existent blueprint raises appropriate error."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        with pytest.raises(BlueprintNotFoundError):
            manager.get_blueprint("non_existent_blueprint_id")
    
    def test_update_blueprint(self, setup_test_db):
        """Test updating an existing blueprint."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        # Create original blueprint
        original = manager.create_blueprint(
            title="Original Title",
            description="Original description",
            metadata=TaskMetadata(priority_score=0.5)
        )
        
        # Update blueprint
        updated_data = {
            "title": "Updated Title",
            "description": "Updated description with more complexity",
            "metadata": TaskMetadata(
                priority_score=0.8,
                required_skills=["advanced_skill"]
            )
        }
        
        updated = manager.update_blueprint(original.blueprint_id, **updated_data)
        
        assert updated.blueprint_id == original.blueprint_id
        assert updated.title == "Updated Title"
        assert updated.description == "Updated description with more complexity"
        assert updated.metadata.priority_score == 0.8
        assert updated.updated_at > original.updated_at
    
    def test_delete_blueprint(self, setup_test_db):
        """Test deleting a blueprint."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        # Create blueprint
        blueprint = manager.create_blueprint(
            title="To Be Deleted",
            description="This blueprint will be deleted"
        )
        
        # Verify it exists
        retrieved = manager.get_blueprint(blueprint.blueprint_id)
        assert retrieved is not None
        
        # Delete it
        result = manager.delete_blueprint(blueprint.blueprint_id)
        assert result is True
        
        # Verify it's deleted
        with pytest.raises(BlueprintNotFoundError):
            manager.get_blueprint(blueprint.blueprint_id)
    
    def test_list_blueprints_with_filters(self, setup_test_db):
        """Test listing blueprints with various filters."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        # Create test blueprints
        bp1 = manager.create_blueprint(
            title="High Priority API",
            description="Critical API implementation",
            metadata=TaskMetadata(priority_score=0.9, tags=["api", "critical"]),
            project_id="project_a"
        )
        
        bp2 = manager.create_blueprint(
            title="Simple Documentation",
            description="Basic documentation update",
            metadata=TaskMetadata(priority_score=0.3, tags=["docs"]),
            project_id="project_a"
        )
        
        bp3 = manager.create_blueprint(
            title="Database Migration",
            description="Complex database schema changes",
            metadata=TaskMetadata(priority_score=0.8, tags=["database", "migration"]),
            project_id="project_b"
        )
        
        # Test project filter
        project_a_blueprints = manager.list_blueprints(project_id="project_a")
        assert len(project_a_blueprints) == 2
        assert all(bp.project_id == "project_a" for bp in project_a_blueprints)
        
        # Test complexity filter - use actual complexities assigned by ML scoring
        all_blueprints = manager.list_blueprints()
        
        # Since complexity is auto-assigned based on content, test with actual complexities present
        if all_blueprints:
            min_score = min(bp.complexity.score for bp in all_blueprints)
            max_score = max(bp.complexity.score for bp in all_blueprints)
            
            # Test with minimum complexity
            min_complexity_blueprints = manager.list_blueprints(
                min_complexity=TaskComplexity.from_score(min_score)
            )
            assert len(min_complexity_blueprints) == len(all_blueprints)  # Should include all
            
            # Test with maximum complexity
            max_complexity_blueprints = manager.list_blueprints(
                max_complexity=TaskComplexity.from_score(max_score)
            )
            assert len(max_complexity_blueprints) == len(all_blueprints)  # Should include all
        
        # Test tag filter
        api_blueprints = manager.list_blueprints(tags=["api"])
        assert len(api_blueprints) >= 1
        assert any("api" in bp.metadata.tags for bp in api_blueprints)
    
    def test_blueprint_dependency_management(self, setup_test_db):
        """Test adding and managing blueprint dependencies."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        # Create prerequisite blueprints
        bp_auth = manager.create_blueprint(
            title="Authentication System",
            description="Basic auth implementation"
        )
        
        bp_database = manager.create_blueprint(
            title="Database Setup",
            description="Initial database schema"
        )
        
        # Create dependent blueprint
        bp_api = manager.create_blueprint(
            title="User API",
            description="API requiring auth and database"
        )
        
        # Add dependencies
        manager.add_dependency(
            bp_api.blueprint_id,
            bp_auth.blueprint_id,
            "blocking",
            is_critical=True
        )
        
        manager.add_dependency(
            bp_api.blueprint_id,
            bp_database.blueprint_id,
            "blocking",
            is_critical=True
        )
        
        # Verify dependencies
        dependencies = manager.get_blueprint_dependencies(bp_api.blueprint_id)
        assert len(dependencies) == 2
        
        prerequisite_ids = [dep.prerequisite_task_id for dep in dependencies]
        assert bp_auth.blueprint_id in prerequisite_ids
        assert bp_database.blueprint_id in prerequisite_ids
    
    def test_dependency_resolution_ordering(self, setup_test_db):
        """Test dependency resolution and execution ordering."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        # Create a complex dependency graph
        bp_a = manager.create_blueprint(title="Task A", description="No dependencies")
        bp_b = manager.create_blueprint(title="Task B", description="Depends on A")
        bp_c = manager.create_blueprint(title="Task C", description="Depends on A")
        bp_d = manager.create_blueprint(title="Task D", description="Depends on B and C")
        
        # Add dependencies: B->A, C->A, D->B, D->C
        manager.add_dependency(bp_b.blueprint_id, bp_a.blueprint_id, "blocking")
        manager.add_dependency(bp_c.blueprint_id, bp_a.blueprint_id, "blocking")
        manager.add_dependency(bp_d.blueprint_id, bp_b.blueprint_id, "blocking")
        manager.add_dependency(bp_d.blueprint_id, bp_c.blueprint_id, "blocking")
        
        # Resolve execution order
        execution_order = manager.resolve_execution_order([
            bp_a.blueprint_id, bp_b.blueprint_id, bp_c.blueprint_id, bp_d.blueprint_id
        ])
        
        # Verify ordering constraints
        assert execution_order.index(bp_a.blueprint_id) < execution_order.index(bp_b.blueprint_id)
        assert execution_order.index(bp_a.blueprint_id) < execution_order.index(bp_c.blueprint_id)
        assert execution_order.index(bp_b.blueprint_id) < execution_order.index(bp_d.blueprint_id)
        assert execution_order.index(bp_c.blueprint_id) < execution_order.index(bp_d.blueprint_id)
    
    def test_circular_dependency_prevention(self, setup_test_db):
        """Test that circular dependencies are prevented."""
        conn, db_path = setup_test_db
        manager = BlueprintManager(conn)
        
        # Create blueprints
        bp_a = manager.create_blueprint(title="Task A", description="Test task")
        bp_b = manager.create_blueprint(title="Task B", description="Test task")
        bp_c = manager.create_blueprint(title="Task C", description="Test task")
        
        # Add dependencies to create a potential circle: A->B->C
        manager.add_dependency(bp_a.blueprint_id, bp_b.blueprint_id, "blocking")
        manager.add_dependency(bp_b.blueprint_id, bp_c.blueprint_id, "blocking")
        
        # Attempting to close the circle C->A should fail
        with pytest.raises(DependencyResolutionError, match="circular"):
            manager.add_dependency(bp_c.blueprint_id, bp_a.blueprint_id, "blocking")


class TestBlueprintDatabaseIntegration:
    """Test BlueprintManager database operations and schema."""
    
    def test_blueprint_table_creation(self):
        """Test that blueprint tables are created correctly."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            conn = get_db_connection(db_path)
            create_tables(conn)
            
            # Create blueprint tables
            BlueprintManager.create_blueprint_tables(conn)
            
            # Verify tables exist
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%blueprint%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['TaskBlueprints', 'BlueprintDependencies']
            for table in expected_tables:
                assert table in tables
            
            conn.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_blueprint_persistence(self):
        """Test that blueprints are properly persisted and retrieved."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            conn = get_db_connection(db_path)
            create_tables(conn)
            BlueprintManager.create_blueprint_tables(conn)
            
            manager = BlueprintManager(conn)
            
            # Create and save blueprint
            original = manager.create_blueprint(
                title="Persistence Test",
                description="Testing blueprint persistence",
                metadata=TaskMetadata(
                    estimated_duration_minutes=120,
                    required_skills=["testing", "persistence"],
                    priority_score=0.75,
                    tags=["test", "database"]
                ),
                project_id="test_project"
            )
            
            # Close and reopen connection
            conn.close()
            conn = get_db_connection(db_path)
            manager = BlueprintManager(conn)
            
            # Retrieve and verify
            retrieved = manager.get_blueprint(original.blueprint_id)
            
            assert retrieved.blueprint_id == original.blueprint_id
            assert retrieved.title == original.title
            assert retrieved.description == original.description
            assert retrieved.complexity == original.complexity
            assert retrieved.project_id == original.project_id
            assert retrieved.metadata.estimated_duration_minutes == 120
            assert "testing" in retrieved.metadata.required_skills
            
            conn.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestBlueprintServicePerformance:
    """Test performance requirements for BlueprintService."""
    
    def test_bulk_blueprint_creation_performance(self):
        """Test creating multiple blueprints meets performance requirements."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            conn = get_db_connection(db_path)
            create_tables(conn)
            BlueprintManager.create_blueprint_tables(conn)
            
            manager = BlueprintManager(conn)
            
            # Create 100 blueprints and measure time
            start_time = time.perf_counter()
            blueprints = []
            
            for i in range(100):
                blueprint = manager.create_blueprint(
                    title=f"Performance Test Blueprint {i}",
                    description=f"Testing performance with blueprint number {i}",
                    metadata=TaskMetadata(priority_score=0.5)
                )
                blueprints.append(blueprint)
            
            total_time_ms = (time.perf_counter() - start_time) * 1000
            avg_time_per_blueprint = total_time_ms / 100
            
            # Performance requirement: <5ms per blueprint
            assert avg_time_per_blueprint < 5.0, f"Average blueprint creation time {avg_time_per_blueprint:.2f}ms exceeds 5ms limit"
            
            # Verify all blueprints were created
            assert len(blueprints) == 100
            
            conn.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_large_dependency_graph_resolution(self):
        """Test dependency resolution performance with large graphs."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            conn = get_db_connection(db_path)
            create_tables(conn)
            BlueprintManager.create_blueprint_tables(conn)
            
            manager = BlueprintManager(conn)
            
            # Create a large dependency graph (50 blueprints)
            blueprints = []
            for i in range(50):
                bp = manager.create_blueprint(
                    title=f"Large Graph Blueprint {i}",
                    description=f"Part of large dependency graph"
                )
                blueprints.append(bp)
            
            # Create dependencies: each blueprint depends on the previous one
            for i in range(1, 50):
                manager.add_dependency(
                    blueprints[i].blueprint_id,
                    blueprints[i-1].blueprint_id,
                    "blocking"
                )
            
            # Test resolution performance
            start_time = time.perf_counter()
            execution_order = manager.resolve_execution_order([bp.blueprint_id for bp in blueprints])
            resolution_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Performance should be reasonable for 50 items
            assert resolution_time_ms < 100.0, f"Dependency resolution took {resolution_time_ms:.2f}ms, too slow"
            
            # Verify correct ordering
            assert len(execution_order) == 50
            assert execution_order[0] == blueprints[0].blueprint_id  # First has no dependencies
            assert execution_order[-1] == blueprints[-1].blueprint_id  # Last depends on all others
            
            conn.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestBlueprintServiceErrors:
    """Test error handling in BlueprintService."""
    
    def test_blueprint_service_error_hierarchy(self):
        """Test custom error classes."""
        # Test base error
        base_error = BlueprintServiceError("Base error")
        assert isinstance(base_error, Exception)
        
        # Test not found error
        not_found_error = BlueprintNotFoundError("Blueprint not found", blueprint_id="test_123")
        assert isinstance(not_found_error, BlueprintServiceError)
        assert hasattr(not_found_error, 'blueprint_id')
        
        # Test dependency resolution error
        dependency_error = DependencyResolutionError("Circular dependency", affected_blueprints=["a", "b"])
        assert isinstance(dependency_error, BlueprintServiceError)
        assert hasattr(dependency_error, 'affected_blueprints')
    
    def test_invalid_update_operations(self):
        """Test error handling for invalid update operations."""
        # This will test various invalid operations when service is implemented
        pytest.skip("Requires BlueprintService implementation")


# Integration tests requiring other system components
class TestBlueprintServiceIntegration:
    """Integration tests for BlueprintService with security and caching."""
    
    def test_blueprint_project_isolation(self):
        """Test blueprint project isolation (Phase 1 security integration)."""
        pytest.skip("Requires security integration implementation")
    
    def test_blueprint_redis_caching(self):
        """Test blueprint caching with Redis integration."""
        pytest.skip("Requires Redis caching implementation")
    
    def test_blueprint_mcp_tools_integration(self):
        """Test integration with MCP blueprint tools."""
        pytest.skip("Requires MCP tools implementation")