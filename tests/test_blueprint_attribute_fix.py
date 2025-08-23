"""
Test-Driven Development tests for TaskBlueprint attribute access fix.

This test suite ensures that TaskBlueprint objects have correct attribute access patterns
and that the documentation service can properly access all required attributes.

NO MOCKS, NO STUBS, NO PLACEHOLDERS - 100% REAL IMPLEMENTATIONS ONLY
"""

import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
import tempfile
import os

from ltms.models.task_blueprint import (
    TaskBlueprint, 
    TaskComplexity, 
    TaskMetadata,
    ComplexityScorer
)
from ltms.services.blueprint_service import BlueprintManager
from ltms.database.connection import get_db_connection
from ltms.config import Config


class TestTaskBlueprintAttributeAccess:
    """Test correct attribute access patterns for TaskBlueprint objects."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def blueprint_manager(self, temp_db_path):
        """Create BlueprintManager with temporary database."""
        conn = get_db_connection(temp_db_path)
        manager = BlueprintManager(conn)
        yield manager
        conn.close()
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample TaskMetadata with all required fields."""
        return TaskMetadata(
            estimated_duration_minutes=120,
            required_skills=["python", "database", "testing"],
            priority_score=0.8,
            resource_requirements={"cpu": "high", "memory": "medium"},
            tags=["backend", "database", "critical"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_blueprint(self, sample_metadata):
        """Create sample TaskBlueprint with all fields populated."""
        return TaskBlueprint(
            blueprint_id="test_bp_001",
            title="Test Blueprint Implementation",
            description="A comprehensive test blueprint with all metadata fields populated for validation testing",
            complexity=TaskComplexity.COMPLEX,
            metadata=sample_metadata,
            project_id="TEST_PROJECT"
        )
    
    def test_taskblueprint_complexity_access(self, sample_blueprint):
        """Test that complexity score is accessed via complexity.score, not complexity_score."""
        # Test correct access pattern
        assert hasattr(sample_blueprint.complexity, 'score')
        complexity_score = sample_blueprint.complexity.score
        assert isinstance(complexity_score, float)
        assert 0.0 <= complexity_score <= 1.0
        
        # Test that direct complexity_score access fails (as expected)
        with pytest.raises(AttributeError, match="'TaskBlueprint' object has no attribute 'complexity_score'"):
            _ = sample_blueprint.complexity_score
    
    def test_taskblueprint_metadata_access(self, sample_blueprint):
        """Test that metadata attributes are accessed via metadata field, not directly."""
        # Test correct access patterns
        assert sample_blueprint.metadata.estimated_duration_minutes == 120
        assert sample_blueprint.metadata.required_skills == ["python", "database", "testing"]
        assert sample_blueprint.metadata.priority_score == 0.8
        assert sample_blueprint.metadata.resource_requirements == {"cpu": "high", "memory": "medium"}
        assert sample_blueprint.metadata.tags == ["backend", "database", "critical"]
        
        # Test that direct access fails (as expected)
        with pytest.raises(AttributeError, match="'TaskBlueprint' object has no attribute 'estimated_duration_minutes'"):
            _ = sample_blueprint.estimated_duration_minutes
        
        with pytest.raises(AttributeError, match="'TaskBlueprint' object has no attribute 'required_skills'"):
            _ = sample_blueprint.required_skills
        
        with pytest.raises(AttributeError, match="'TaskBlueprint' object has no attribute 'priority_score'"):
            _ = sample_blueprint.priority_score
        
        with pytest.raises(AttributeError, match="'TaskBlueprint' object has no attribute 'tags'"):
            _ = sample_blueprint.tags
        
        with pytest.raises(AttributeError, match="'TaskBlueprint' object has no attribute 'resource_requirements'"):
            _ = sample_blueprint.resource_requirements
    
    def test_blueprint_manager_returns_correct_object(self, blueprint_manager, sample_metadata):
        """Test that BlueprintManager.get_blueprint returns TaskBlueprint with correct attribute access."""
        # Create blueprint via manager
        created_blueprint = blueprint_manager.create_blueprint(
            title="Database Integration Task",
            description="Implement comprehensive database integration with error handling and performance optimization",
            metadata=sample_metadata,
            project_id="INTEGRATION_TEST"
        )
        
        # Retrieve blueprint via manager
        retrieved_blueprint = blueprint_manager.get_blueprint(created_blueprint.blueprint_id)
        
        # Verify it's the correct type
        assert isinstance(retrieved_blueprint, TaskBlueprint)
        
        # Verify correct attribute access patterns work
        assert retrieved_blueprint.complexity.score >= 0.0
        assert retrieved_blueprint.metadata.estimated_duration_minutes == 120
        assert retrieved_blueprint.metadata.required_skills == ["python", "database", "testing"]
        assert retrieved_blueprint.metadata.priority_score == 0.8
        assert retrieved_blueprint.metadata.tags == ["backend", "database", "critical"]
        
        # Verify incorrect access patterns fail
        with pytest.raises(AttributeError):
            _ = retrieved_blueprint.complexity_score
        
        with pytest.raises(AttributeError):
            _ = retrieved_blueprint.estimated_duration_minutes


class TestDocumentationServiceIntegration:
    """Test that documentation service can access TaskBlueprint attributes correctly."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture  
    def test_blueprint_in_db(self, temp_db_path):
        """Create a test blueprint in database and return its ID."""
        conn = get_db_connection(temp_db_path)
        manager = BlueprintManager(conn)
        
        metadata = TaskMetadata(
            estimated_duration_minutes=180,
            required_skills=["architecture", "design", "documentation"],
            priority_score=0.9,
            resource_requirements={"expertise": "senior", "time": "extended"},
            tags=["architecture", "documentation", "high-priority"]
        )
        
        blueprint = manager.create_blueprint(
            title="System Architecture Documentation",
            description="Create comprehensive system architecture documentation with detailed component diagrams and integration patterns",
            metadata=metadata,
            project_id="DOC_INTEGRATION_TEST"
        )
        
        conn.close()
        yield blueprint.blueprint_id, temp_db_path
    
    def test_documentation_service_blueprint_access_pattern(self, test_blueprint_in_db):
        """Test that documentation service can access blueprint attributes correctly."""
        blueprint_id, db_path = test_blueprint_in_db
        
        # Simulate the exact code pattern used in documentation_sync_service.py
        conn = get_db_connection(db_path)
        manager = BlueprintManager(conn)
        blueprint_obj = manager.get_blueprint(blueprint_id)
        
        assert blueprint_obj is not None
        
        # Test the CORRECT attribute access pattern that should work
        tb_node_correct = {
            'blueprint_id': blueprint_obj.blueprint_id,
            'title': blueprint_obj.title,
            'description': blueprint_obj.description,
            'complexity': blueprint_obj.complexity,
            'complexity_score': blueprint_obj.complexity.score,  # CORRECT
            'estimated_duration_minutes': blueprint_obj.metadata.estimated_duration_minutes,  # CORRECT
            'required_skills': blueprint_obj.metadata.required_skills,  # CORRECT
            'priority_score': blueprint_obj.metadata.priority_score,  # CORRECT
            'tags': blueprint_obj.metadata.tags,  # CORRECT
            'resource_requirements': blueprint_obj.metadata.resource_requirements,  # CORRECT
            'created_at': str(blueprint_obj.created_at),
            'project_id': blueprint_obj.project_id
        }
        
        # Verify all values are accessible and correct
        assert tb_node_correct['blueprint_id'] == blueprint_id
        assert tb_node_correct['title'] == "System Architecture Documentation"
        assert isinstance(tb_node_correct['complexity_score'], float)
        assert tb_node_correct['estimated_duration_minutes'] == 180
        assert tb_node_correct['required_skills'] == ["architecture", "design", "documentation"]
        assert tb_node_correct['priority_score'] == 0.9
        assert tb_node_correct['tags'] == ["architecture", "documentation", "high-priority"]
        assert isinstance(tb_node_correct['resource_requirements'], dict)
        
        conn.close()
    
    def test_documentation_service_incorrect_access_fails(self, test_blueprint_in_db):
        """Test that the INCORRECT attribute access pattern fails (demonstrating the bug)."""
        blueprint_id, db_path = test_blueprint_in_db
        
        conn = get_db_connection(db_path)
        manager = BlueprintManager(conn)
        blueprint_obj = manager.get_blueprint(blueprint_id)
        
        # Test that the INCORRECT patterns fail (this proves the bug exists)
        with pytest.raises(AttributeError):
            _ = blueprint_obj.complexity_score  # INCORRECT - should be blueprint_obj.complexity.score
        
        with pytest.raises(AttributeError):
            _ = blueprint_obj.estimated_duration_minutes  # INCORRECT - should be blueprint_obj.metadata.estimated_duration_minutes
        
        with pytest.raises(AttributeError):
            _ = blueprint_obj.required_skills  # INCORRECT - should be blueprint_obj.metadata.required_skills
        
        with pytest.raises(AttributeError):
            _ = blueprint_obj.priority_score  # INCORRECT - should be blueprint_obj.metadata.priority_score
        
        with pytest.raises(AttributeError):
            _ = blueprint_obj.tags  # INCORRECT - should be blueprint_obj.metadata.tags
        
        with pytest.raises(AttributeError):
            _ = blueprint_obj.resource_requirements  # INCORRECT - should be blueprint_obj.metadata.resource_requirements
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])