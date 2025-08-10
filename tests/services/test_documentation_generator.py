"""Tests for Documentation Generator - Component 4 (Blueprint Generation) - Phase 2."""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from ltms.services.documentation_generator import (
    DocumentationGenerator,
    DocumentType,
    DocumentationMetadata,
    APIDocumentationResult,
    ArchitectureDiagramResult,
    ProgressReportResult
)
from ltms.models.task_blueprint import TaskBlueprint, TaskDependency, TaskPriority


class TestDocumentationGenerator:
    """Test suite for DocumentationGenerator."""
    
    @pytest.fixture
    async def doc_generator(self, redis_manager, neo4j_store):
        """Create DocumentationGenerator instance for testing."""
        generator = DocumentationGenerator(
            redis_manager=redis_manager,
            neo4j_store=neo4j_store
        )
        await generator.initialize()
        yield generator
        await generator.cleanup()
    
    @pytest.fixture
    def sample_task_blueprint(self):
        """Sample TaskBlueprint for testing."""
        return TaskBlueprint(
            blueprint_id="test_blueprint_001",
            name="Test API Implementation",
            description="Implement REST API for user management",
            required_skills=["python", "fastapi", "database"],
            estimated_hours=8.0,
            priority=TaskPriority.HIGH,
            dependencies=[
                TaskDependency(
                    blueprint_id="test_blueprint_000",
                    dependency_type="blocks"
                )
            ],
            complexity_score=0.7,
            project_id="test_project",
            metadata={"api_version": "v1", "endpoints": 5}
        )
    
    @pytest.fixture
    def sample_code_files(self):
        """Sample code files for documentation generation."""
        return {
            "api/endpoints.py": '''
"""User management API endpoints."""

from fastapi import APIRouter, Depends
from typing import List
from .models import User, UserCreate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[User])
async def get_users():
    """Get all users."""
    pass

@router.post("/", response_model=User)
async def create_user(user: UserCreate):
    """Create a new user."""
    pass
            ''',
            "models/user.py": '''
"""User data models."""

from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    """Base user model."""
    username: str
    email: str

class UserCreate(UserBase):
    """User creation model."""
    password: str

class User(UserBase):
    """User model with ID."""
    id: int
    is_active: bool = True
            '''
        }
    
    # Core Functionality Tests
    
    async def test_initialization(self, doc_generator):
        """Test DocumentationGenerator initialization."""
        assert doc_generator.initialized
        assert doc_generator.redis_manager is not None
        assert doc_generator.neo4j_store is not None
        assert doc_generator._performance_metrics is not None
    
    async def test_generate_api_documentation(self, doc_generator, sample_code_files):
        """Test API documentation generation."""
        start_time = asyncio.get_event_loop().time()
        
        # Test API documentation generation
        result = await doc_generator.generate_api_documentation(
            project_id="test_project",
            source_files=sample_code_files,
            output_format="markdown"
        )
        
        end_time = asyncio.get_event_loop().time()
        generation_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Validate result
        assert isinstance(result, APIDocumentationResult)
        assert result.success
        assert result.documentation_content
        assert result.metadata.total_endpoints > 0
        assert result.metadata.total_models > 0
        
        # Performance requirement: <10ms
        assert generation_time < 10, f"API doc generation took {generation_time:.2f}ms, expected <10ms"
        
        # Check content structure
        doc_content = result.documentation_content
        assert "# API Documentation" in doc_content
        assert "## Endpoints" in doc_content
        assert "## Models" in doc_content
        assert "/users/" in doc_content
        assert "UserCreate" in doc_content
    
    async def test_create_architecture_diagram(self, doc_generator, sample_task_blueprint):
        """Test architecture diagram creation."""
        start_time = asyncio.get_event_loop().time()
        
        # Create architecture diagram
        result = await doc_generator.create_architecture_diagram(
            project_id="test_project",
            blueprint_id=sample_task_blueprint.blueprint_id,
            diagram_type="component_diagram"
        )
        
        end_time = asyncio.get_event_loop().time()
        generation_time = (end_time - start_time) * 1000
        
        # Validate result
        assert isinstance(result, ArchitectureDiagramResult)
        assert result.success
        assert result.diagram_content
        assert result.metadata.diagram_type == "component_diagram"
        assert result.metadata.component_count > 0
        
        # Performance requirement: <10ms
        assert generation_time < 10, f"Architecture diagram took {generation_time:.2f}ms, expected <10ms"
        
        # Check diagram content
        assert "graph" in result.diagram_content.lower()
        assert sample_task_blueprint.name in result.diagram_content
    
    async def test_generate_progress_report(self, doc_generator, sample_task_blueprint):
        """Test progress report generation."""
        start_time = asyncio.get_event_loop().time()
        
        # Generate progress report
        result = await doc_generator.generate_progress_report(
            project_id="test_project",
            report_type="weekly",
            include_blueprints=[sample_task_blueprint.blueprint_id]
        )
        
        end_time = asyncio.get_event_loop().time()
        generation_time = (end_time - start_time) * 1000
        
        # Validate result
        assert isinstance(result, ProgressReportResult)
        assert result.success
        assert result.report_content
        assert result.metadata.total_tasks > 0
        assert result.metadata.completion_percentage >= 0
        
        # Performance requirement: <10ms
        assert generation_time < 10, f"Progress report took {generation_time:.2f}ms, expected <10ms"
        
        # Check report content
        report_content = result.report_content
        assert "Progress Report" in report_content
        assert sample_task_blueprint.name in report_content
        assert "completion" in report_content.lower()
    
    # Neo4j Integration Tests
    
    async def test_blueprint_system_integration(self, doc_generator, sample_task_blueprint):
        """Test integration with Neo4j blueprint system."""
        # This should query the Neo4j graph for blueprint relationships
        result = await doc_generator.create_architecture_diagram(
            project_id="test_project",
            blueprint_id=sample_task_blueprint.blueprint_id,
            diagram_type="dependency_graph"
        )
        
        assert result.success
        assert result.metadata.dependency_count >= 0
        # Should include blueprint relationships from Neo4j
        assert "dependency" in result.diagram_content.lower() or result.metadata.dependency_count == 0
    
    # Template System Tests
    
    async def test_documentation_with_templates(self, doc_generator, sample_code_files):
        """Test documentation generation with templates."""
        # Test with custom template
        result = await doc_generator.generate_api_documentation(
            project_id="test_project",
            source_files=sample_code_files,
            output_format="markdown",
            template_name="api_template"
        )
        
        assert result.success
        assert result.documentation_content
        # Should follow template structure
        assert "# API Documentation" in result.documentation_content
    
    # Error Handling Tests
    
    async def test_invalid_source_files(self, doc_generator):
        """Test handling of invalid source files."""
        invalid_files = {
            "invalid.py": "This is not valid Python code $$$ @@@"
        }
        
        result = await doc_generator.generate_api_documentation(
            project_id="test_project",
            source_files=invalid_files,
            output_format="markdown"
        )
        
        # Should handle gracefully
        assert not result.success
        assert result.error_message
        assert "parsing" in result.error_message.lower()
    
    async def test_missing_blueprint(self, doc_generator):
        """Test handling of missing blueprint."""
        result = await doc_generator.create_architecture_diagram(
            project_id="test_project",
            blueprint_id="nonexistent_blueprint",
            diagram_type="component_diagram"
        )
        
        # Should handle gracefully
        assert not result.success
        assert result.error_message
        assert "not found" in result.error_message.lower()
    
    # Performance Tests
    
    async def test_concurrent_generation(self, doc_generator, sample_code_files, sample_task_blueprint):
        """Test concurrent document generation."""
        start_time = asyncio.get_event_loop().time()
        
        # Run multiple generations concurrently
        tasks = [
            doc_generator.generate_api_documentation(
                project_id="test_project",
                source_files=sample_code_files,
                output_format="markdown"
            ),
            doc_generator.create_architecture_diagram(
                project_id="test_project",
                blueprint_id=sample_task_blueprint.blueprint_id,
                diagram_type="component_diagram"
            ),
            doc_generator.generate_progress_report(
                project_id="test_project",
                report_type="daily",
                include_blueprints=[sample_task_blueprint.blueprint_id]
            )
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        total_time = (end_time - start_time) * 1000
        
        # All should succeed
        for result in results:
            assert result.success
        
        # Performance: concurrent should be faster than sequential
        # Total time should be less than 3x individual time
        assert total_time < 30, f"Concurrent generation took {total_time:.2f}ms, expected <30ms"
    
    async def test_caching_performance(self, doc_generator, sample_code_files):
        """Test caching improves performance."""
        # First generation (uncached)
        start_time = asyncio.get_event_loop().time()
        result1 = await doc_generator.generate_api_documentation(
            project_id="test_project",
            source_files=sample_code_files,
            output_format="markdown"
        )
        first_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Second generation (should be cached)
        start_time = asyncio.get_event_loop().time()
        result2 = await doc_generator.generate_api_documentation(
            project_id="test_project",
            source_files=sample_code_files,
            output_format="markdown"
        )
        second_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Both should succeed
        assert result1.success and result2.success
        assert result1.documentation_content == result2.documentation_content
        
        # Second should be faster (cached)
        assert second_time < first_time, f"Cache didn't improve performance: {second_time:.2f}ms vs {first_time:.2f}ms"
    
    # Security Integration Tests
    
    async def test_project_isolation(self, doc_generator, sample_code_files):
        """Test project isolation in documentation generation."""
        # Generate docs for two different projects
        result1 = await doc_generator.generate_api_documentation(
            project_id="project_1",
            source_files=sample_code_files,
            output_format="markdown"
        )
        
        result2 = await doc_generator.generate_api_documentation(
            project_id="project_2",
            source_files=sample_code_files,
            output_format="markdown"
        )
        
        assert result1.success and result2.success
        # Should be isolated (different cache keys, etc.)
        assert result1.metadata.project_id != result2.metadata.project_id
    
    # Memory Management Tests
    
    async def test_memory_usage_cleanup(self, doc_generator, sample_code_files):
        """Test memory cleanup after generation."""
        # Generate multiple large documents
        large_files = {f"file_{i}.py": sample_code_files["api/endpoints.py"] * 10 for i in range(10)}
        
        results = []
        for i in range(5):
            result = await doc_generator.generate_api_documentation(
                project_id=f"project_{i}",
                source_files=large_files,
                output_format="markdown"
            )
            results.append(result)
        
        # All should succeed
        for result in results:
            assert result.success
        
        # Memory should be managed properly (no explicit test, but shouldn't crash)
        assert len(results) == 5
    
    # Metadata and Analytics Tests
    
    async def test_generation_metadata(self, doc_generator, sample_code_files, sample_task_blueprint):
        """Test metadata collection during generation."""
        result = await doc_generator.generate_api_documentation(
            project_id="test_project",
            source_files=sample_code_files,
            output_format="markdown"
        )
        
        assert result.success
        metadata = result.metadata
        
        # Check metadata completeness
        assert metadata.generation_time_ms > 0
        assert metadata.total_endpoints == 2  # get_users, create_user
        assert metadata.total_models == 3     # UserBase, UserCreate, User
        assert metadata.template_used
        assert metadata.project_id == "test_project"
        assert metadata.generated_at
    
    async def test_performance_metrics_collection(self, doc_generator, sample_code_files):
        """Test performance metrics are collected."""
        # Generate documentation to collect metrics
        await doc_generator.generate_api_documentation(
            project_id="test_project",
            source_files=sample_code_files,
            output_format="markdown"
        )
        
        # Get metrics
        metrics = await doc_generator.get_performance_metrics()
        
        assert metrics
        assert "api_documentation" in metrics
        assert metrics["api_documentation"]["total_generations"] > 0
        assert metrics["api_documentation"]["avg_generation_time_ms"] > 0
        assert metrics["api_documentation"]["avg_generation_time_ms"] < 10  # Performance target


# Integration test marker
pytestmark = pytest.mark.asyncio