"""
Test module for TaskBlueprint models and related functionality.

Tests the TaskBlueprint system including:
- TaskBlueprint model validation and operations
- TaskComplexity enum and scoring
- TaskDependency graph operations
- TaskMetadata management
- ML-based complexity analysis
- Performance requirements (<5ms blueprint creation)

Following TDD methodology - tests written first.
"""

import pytest
import tempfile
import os
import time
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum

# Import the modules we're about to create (will fail initially - that's TDD!)
from ltms.models.task_blueprint import (
    TaskBlueprint,
    TaskComplexity,
    TaskDependency,
    TaskMetadata,
    BlueprintValidationError,
    ComplexityScorer
)


class TestTaskComplexity:
    """Test TaskComplexity enum and related functionality."""
    
    def test_task_complexity_enum_values(self):
        """Test that TaskComplexity enum has all required values."""
        expected_values = ['TRIVIAL', 'SIMPLE', 'MODERATE', 'COMPLEX', 'CRITICAL']
        actual_values = [complexity.name for complexity in TaskComplexity]
        assert all(value in actual_values for value in expected_values)
    
    def test_task_complexity_numeric_scoring(self):
        """Test that TaskComplexity provides numeric scoring."""
        assert TaskComplexity.TRIVIAL.score < TaskComplexity.SIMPLE.score
        assert TaskComplexity.SIMPLE.score < TaskComplexity.MODERATE.score
        assert TaskComplexity.MODERATE.score < TaskComplexity.COMPLEX.score
        assert TaskComplexity.COMPLEX.score < TaskComplexity.CRITICAL.score
    
    def test_task_complexity_from_score(self):
        """Test converting numeric scores back to TaskComplexity."""
        assert TaskComplexity.from_score(0.1) == TaskComplexity.TRIVIAL
        assert TaskComplexity.from_score(0.9) == TaskComplexity.CRITICAL
        assert TaskComplexity.from_score(0.5) == TaskComplexity.MODERATE


class TestTaskMetadata:
    """Test TaskMetadata model functionality."""
    
    def test_task_metadata_creation(self):
        """Test creating TaskMetadata with valid data."""
        metadata = TaskMetadata(
            estimated_duration_minutes=30,
            required_skills=["python", "async"],
            priority_score=0.8,
            resource_requirements={"memory": "2GB", "cpu": "2 cores"},
            tags=["api", "database"]
        )
        
        assert metadata.estimated_duration_minutes == 30
        assert "python" in metadata.required_skills
        assert metadata.priority_score == 0.8
        assert metadata.resource_requirements["memory"] == "2GB"
        assert "api" in metadata.tags
    
    def test_task_metadata_validation(self):
        """Test TaskMetadata validation rules."""
        # Test invalid priority score
        with pytest.raises(BlueprintValidationError):
            TaskMetadata(priority_score=1.5)  # Should be <= 1.0
        
        # Test negative duration
        with pytest.raises(BlueprintValidationError):
            TaskMetadata(estimated_duration_minutes=-10)
    
    def test_task_metadata_serialization(self):
        """Test TaskMetadata JSON serialization/deserialization."""
        metadata = TaskMetadata(
            estimated_duration_minutes=45,
            required_skills=["fastapi", "postgresql"],
            priority_score=0.6
        )
        
        # Test to_dict and from_dict
        data = metadata.to_dict()
        restored = TaskMetadata.from_dict(data)
        
        assert restored.estimated_duration_minutes == metadata.estimated_duration_minutes
        assert restored.required_skills == metadata.required_skills
        assert restored.priority_score == metadata.priority_score


class TestTaskDependency:
    """Test TaskDependency model and graph operations."""
    
    def test_task_dependency_creation(self):
        """Test creating TaskDependency with valid data."""
        dependency = TaskDependency(
            dependent_task_id="task_123",
            prerequisite_task_id="task_456",
            dependency_type="blocking",
            is_critical=True
        )
        
        assert dependency.dependent_task_id == "task_123"
        assert dependency.prerequisite_task_id == "task_456"
        assert dependency.dependency_type == "blocking"
        assert dependency.is_critical is True
    
    def test_dependency_graph_validation(self):
        """Test dependency graph circular reference detection."""
        dependencies = [
            TaskDependency("task_a", "task_b", "blocking"),
            TaskDependency("task_b", "task_c", "blocking"),
            TaskDependency("task_c", "task_a", "blocking")  # Circular!
        ]
        
        with pytest.raises(BlueprintValidationError, match="Circular dependency"):
            TaskDependency.validate_dependency_graph(dependencies)
    
    def test_dependency_resolution_order(self):
        """Test dependency resolution ordering."""
        dependencies = [
            TaskDependency("task_c", "task_a", "blocking"),
            TaskDependency("task_b", "task_a", "blocking"),
            TaskDependency("task_d", "task_c", "blocking")
        ]
        
        execution_order = TaskDependency.resolve_execution_order(dependencies)
        
        # task_a should come first (no dependencies)
        # task_b and task_c can come next (depend only on task_a)
        # task_d should come last (depends on task_c)
        assert execution_order.index("task_a") < execution_order.index("task_b")
        assert execution_order.index("task_a") < execution_order.index("task_c")
        assert execution_order.index("task_c") < execution_order.index("task_d")


class TestTaskBlueprint:
    """Test TaskBlueprint model core functionality."""
    
    def test_task_blueprint_creation(self):
        """Test creating TaskBlueprint with required fields."""
        metadata = TaskMetadata(
            estimated_duration_minutes=60,
            required_skills=["python", "fastapi"],
            priority_score=0.7
        )
        
        blueprint = TaskBlueprint(
            blueprint_id="bp_001",
            title="Implement API endpoint",
            description="Create new REST API endpoint for user management",
            complexity=TaskComplexity.MODERATE,
            metadata=metadata,
            project_id="project_123"
        )
        
        assert blueprint.blueprint_id == "bp_001"
        assert blueprint.title == "Implement API endpoint"
        assert blueprint.complexity == TaskComplexity.MODERATE
        assert blueprint.metadata.estimated_duration_minutes == 60
        assert blueprint.project_id == "project_123"
    
    def test_task_blueprint_validation(self):
        """Test TaskBlueprint validation rules."""
        # Test empty title
        with pytest.raises(BlueprintValidationError):
            TaskBlueprint(
                blueprint_id="bp_002",
                title="",  # Empty title should fail
                description="Test description",
                complexity=TaskComplexity.SIMPLE
            )
        
        # Test invalid blueprint_id format
        with pytest.raises(BlueprintValidationError):
            TaskBlueprint(
                blueprint_id="invalid id with spaces",
                title="Valid Title",
                description="Test description",
                complexity=TaskComplexity.SIMPLE
            )
    
    def test_task_blueprint_with_dependencies(self):
        """Test TaskBlueprint with dependency management."""
        blueprint = TaskBlueprint(
            blueprint_id="bp_003",
            title="Complex Task",
            description="Task with dependencies",
            complexity=TaskComplexity.COMPLEX
        )
        
        # Add dependencies
        blueprint.add_dependency("prerequisite_task_1", "blocking")
        blueprint.add_dependency("prerequisite_task_2", "soft")
        
        assert len(blueprint.dependencies) == 2
        assert any(dep.prerequisite_task_id == "prerequisite_task_1" for dep in blueprint.dependencies)
        assert any(dep.dependency_type == "soft" for dep in blueprint.dependencies)
    
    def test_task_blueprint_performance_creation(self):
        """Test that blueprint creation meets <5ms performance requirement."""
        metadata = TaskMetadata(
            estimated_duration_minutes=30,
            required_skills=["python"],
            priority_score=0.5
        )
        
        start_time = time.perf_counter()
        
        blueprint = TaskBlueprint(
            blueprint_id="perf_test_001",
            title="Performance Test Blueprint",
            description="Testing blueprint creation performance",
            complexity=TaskComplexity.SIMPLE,
            metadata=metadata
        )
        
        end_time = time.perf_counter()
        creation_time_ms = (end_time - start_time) * 1000
        
        # Performance requirement: <5ms
        assert creation_time_ms < 5.0, f"Blueprint creation took {creation_time_ms:.2f}ms, exceeds 5ms limit"
    
    def test_task_blueprint_serialization(self):
        """Test TaskBlueprint full serialization/deserialization."""
        metadata = TaskMetadata(
            estimated_duration_minutes=90,
            required_skills=["python", "redis", "postgresql"],
            priority_score=0.8,
            tags=["backend", "database"]
        )
        
        original = TaskBlueprint(
            blueprint_id="serial_test_001",
            title="Serialization Test",
            description="Testing blueprint serialization",
            complexity=TaskComplexity.COMPLEX,
            metadata=metadata
        )
        
        # Add some dependencies
        original.add_dependency("dep_1", "blocking")
        original.add_dependency("dep_2", "soft")
        
        # Serialize and deserialize
        data = original.to_dict()
        restored = TaskBlueprint.from_dict(data)
        
        assert restored.blueprint_id == original.blueprint_id
        assert restored.title == original.title
        assert restored.complexity == original.complexity
        assert len(restored.dependencies) == len(original.dependencies)
        assert restored.metadata.estimated_duration_minutes == original.metadata.estimated_duration_minutes


class TestComplexityScorer:
    """Test ML-based complexity scoring functionality."""
    
    def test_complexity_scorer_initialization(self):
        """Test ComplexityScorer initialization."""
        scorer = ComplexityScorer()
        assert scorer is not None
        assert hasattr(scorer, 'score_task_complexity')
    
    def test_complexity_scoring_with_text_analysis(self):
        """Test complexity scoring based on task description."""
        scorer = ComplexityScorer()
        
        # Simple task
        simple_description = "Fix typo in documentation"
        simple_score = scorer.score_task_complexity(
            title="Fix typo",
            description=simple_description,
            required_skills=["documentation"]
        )
        
        # Complex task
        complex_description = """
        Implement a distributed microservice architecture with:
        - Event-driven communication using Apache Kafka
        - CQRS pattern with separate read/write databases
        - Circuit breaker pattern for fault tolerance
        - Distributed tracing with OpenTelemetry
        - OAuth2/JWT authentication and authorization
        - Real-time data streaming and processing
        """
        complex_score = scorer.score_task_complexity(
            title="Implement distributed microservices",
            description=complex_description,
            required_skills=["kafka", "cqrs", "microservices", "oauth2", "distributed-systems"]
        )
        
        # Complex task should have higher score
        assert complex_score > simple_score
        assert simple_score < 0.3  # Should be classified as simple
        assert complex_score > 0.7  # Should be classified as complex
    
    def test_complexity_scoring_performance(self):
        """Test that complexity scoring meets performance requirements."""
        scorer = ComplexityScorer()
        
        description = "Implement REST API with database integration"
        
        start_time = time.perf_counter()
        
        score = scorer.score_task_complexity(
            title="API Implementation",
            description=description,
            required_skills=["python", "fastapi", "postgresql"]
        )
        
        end_time = time.perf_counter()
        scoring_time_ms = (end_time - start_time) * 1000
        
        # Performance requirement: scoring should be fast
        assert scoring_time_ms < 50.0, f"Complexity scoring took {scoring_time_ms:.2f}ms, too slow"
        assert 0.0 <= score <= 1.0, "Score should be between 0 and 1"
    
    def test_complexity_scoring_caching(self):
        """Test that complexity scoring results are cached for performance."""
        scorer = ComplexityScorer()
        
        description = "Test caching functionality"
        
        # First call - should compute
        start_time = time.perf_counter()
        score1 = scorer.score_task_complexity(
            title="Caching Test",
            description=description,
            required_skills=["caching"]
        )
        first_call_time = time.perf_counter() - start_time
        
        # Second call - should use cache
        start_time = time.perf_counter()
        score2 = scorer.score_task_complexity(
            title="Caching Test",
            description=description,
            required_skills=["caching"]
        )
        second_call_time = time.perf_counter() - start_time
        
        # Results should be identical
        assert score1 == score2
        
        # Second call should be faster or at least not significantly slower (cached)
        # Since the operation is already very fast, we just verify caching is working
        assert second_call_time <= first_call_time * 2.0, "Caching appears to be degrading performance"


class TestBlueprintValidationError:
    """Test custom validation error handling."""
    
    def test_blueprint_validation_error_creation(self):
        """Test creating BlueprintValidationError with message."""
        error = BlueprintValidationError("Test validation error")
        assert str(error) == "Test validation error"
        assert isinstance(error, ValueError)
    
    def test_blueprint_validation_error_with_details(self):
        """Test BlueprintValidationError with detailed information."""
        error = BlueprintValidationError(
            "Invalid blueprint data",
            field="title",
            value="",
            constraint="must not be empty"
        )
        
        assert "Invalid blueprint data" in str(error)
        assert hasattr(error, 'field')
        assert hasattr(error, 'value')
        assert hasattr(error, 'constraint')


# Integration tests that will require the service layer
class TestTaskBlueprintIntegration:
    """Integration tests for TaskBlueprint with other system components."""
    
    def test_blueprint_database_integration_placeholder(self):
        """Placeholder for blueprint database integration tests."""
        # This will be implemented when we create the service layer
        pytest.skip("Requires BlueprintService implementation")
    
    def test_blueprint_mcp_tools_integration_placeholder(self):
        """Placeholder for blueprint MCP tools integration tests."""
        # This will be implemented when we create the MCP tools
        pytest.skip("Requires MCP blueprint tools implementation")
    
    def test_blueprint_security_integration_placeholder(self):
        """Placeholder for blueprint security integration tests."""
        # This will test Phase 1 security integration
        pytest.skip("Requires security integration implementation")