"""
Simple integration test for TaskBlueprint attribute access fix without heavy dependencies.

This test focuses specifically on the attribute access patterns without importing
services that have heavy dependencies (like numpy).

NO MOCKS, NO STUBS, NO PLACEHOLDERS - 100% REAL INTEGRATION TEST
"""

import pytest
import tempfile
import os
from datetime import datetime

from ltms.models.task_blueprint import TaskBlueprint, TaskComplexity, TaskMetadata
from ltms.services.blueprint_service import BlueprintManager
from ltms.database.connection import get_db_connection


class TestBlueprintAttributeFixSimpleIntegration:
    """Simple integration test for TaskBlueprint attribute access fix."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    def test_real_world_blueprint_attribute_access(self, temp_db_path):
        """Test real-world blueprint creation and attribute access patterns."""
        # Create a real blueprint in database
        conn = get_db_connection(temp_db_path)
        manager = BlueprintManager(conn)
        
        # Create comprehensive metadata (real data)
        metadata = TaskMetadata(
            estimated_duration_minutes=180,
            required_skills=["python", "databases", "api-design", "testing", "documentation"],
            priority_score=0.85,
            resource_requirements={
                "development_environment": "python-3.11+",
                "database": "sqlite-with-wal",
                "testing_framework": "pytest",
                "documentation_tools": "markdown-sphinx"
            },
            tags=["backend", "database", "api", "high-priority", "well-tested"]
        )
        
        # Create blueprint with complex description (real scenario)
        blueprint = manager.create_blueprint(
            title="Advanced Task Management API with Blueprint Integration",
            description="""
            Implement a comprehensive task management API that integrates with the blueprint system.
            
            Requirements:
            1. RESTful API endpoints for CRUD operations on tasks and blueprints
            2. Advanced filtering and search capabilities
            3. Real-time task status updates
            4. Integration with existing blueprint complexity scoring
            5. Comprehensive input validation and error handling
            6. Database optimization for high-performance queries
            7. Complete test suite with >95% coverage
            8. API documentation with OpenAPI/Swagger
            9. Authentication and authorization
            10. Rate limiting and request throttling
            
            This API will be the foundation for task orchestration across the entire system.
            """,
            metadata=metadata,
            project_id="TASK_MANAGEMENT_INTEGRATION"
        )
        
        conn.close()
        
        # Test retrieval and attribute access (the real scenario)
        conn = get_db_connection(temp_db_path)
        manager = BlueprintManager(conn)
        retrieved_blueprint = manager.get_blueprint(blueprint.blueprint_id)
        
        assert retrieved_blueprint is not None
        
        # Test the EXACT attribute access pattern from documentation_sync_service.py
        # This is what was failing before our fix
        tb_node_data = {
            'blueprint_id': retrieved_blueprint.blueprint_id,
            'title': retrieved_blueprint.title,
            'description': retrieved_blueprint.description,
            'complexity': retrieved_blueprint.complexity,
            'complexity_score': retrieved_blueprint.complexity.score,  # CORRECTED ACCESS
            'estimated_duration_minutes': retrieved_blueprint.metadata.estimated_duration_minutes,  # CORRECTED ACCESS
            'required_skills': retrieved_blueprint.metadata.required_skills,  # CORRECTED ACCESS  
            'priority_score': retrieved_blueprint.metadata.priority_score,  # CORRECTED ACCESS
            'tags': retrieved_blueprint.metadata.tags,  # CORRECTED ACCESS
            'resource_requirements': retrieved_blueprint.metadata.resource_requirements,  # CORRECTED ACCESS
            'created_at': str(retrieved_blueprint.created_at),
            'project_id': retrieved_blueprint.project_id
        }
        
        # Comprehensive validation of all attributes
        assert tb_node_data['blueprint_id'] == blueprint.blueprint_id
        assert "Advanced Task Management API" in tb_node_data['title']
        assert isinstance(tb_node_data['complexity'], TaskComplexity)
        assert isinstance(tb_node_data['complexity_score'], float)
        assert 0.0 <= tb_node_data['complexity_score'] <= 1.0
        assert tb_node_data['estimated_duration_minutes'] == 180
        assert tb_node_data['required_skills'] == ["python", "databases", "api-design", "testing", "documentation"]
        assert tb_node_data['priority_score'] == 0.85
        assert tb_node_data['tags'] == ["backend", "database", "api", "high-priority", "well-tested"]
        assert "development_environment" in tb_node_data['resource_requirements']
        assert tb_node_data['project_id'] == "TASK_MANAGEMENT_INTEGRATION"
        
        conn.close()
        
        # Test documentation-style string generation (simulates real usage)
        complexity_name = tb_node_data['complexity'].name
        doc_content = f"""
# Blueprint Documentation: {tb_node_data['title']}

**Project**: {tb_node_data['project_id']}
**Blueprint ID**: {tb_node_data['blueprint_id']}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Complexity Analysis
- **Level**: {complexity_name}
- **Score**: {tb_node_data['complexity_score']:.3f}/1.0
- **Estimated Duration**: {tb_node_data['estimated_duration_minutes']} minutes

## Requirements
- **Priority**: {tb_node_data['priority_score']}/1.0
- **Required Skills**: {', '.join(tb_node_data['required_skills'])}
- **Tags**: {', '.join(tb_node_data['tags'])}

## Resource Requirements
""" + "\\n".join([f"- **{k}**: {v}" for k, v in tb_node_data['resource_requirements'].items()]) + f"""

## Description
{tb_node_data['description'].strip()}

---
*This documentation was generated from TaskBlueprint data with corrected attribute access patterns.*
"""
        
        # Verify documentation generation succeeded
        assert "Advanced Task Management API" in doc_content
        assert "TASK_MANAGEMENT_INTEGRATION" in doc_content
        assert blueprint.blueprint_id in doc_content
        assert "python" in doc_content
        assert "0.85" in doc_content
        assert "backend" in doc_content
        assert "180 minutes" in doc_content
        
        print("✅ SUCCESS: TaskBlueprint attribute access fix verified in real integration scenario")
        print(f"✅ SUCCESS: All attributes accessible: complexity_score={tb_node_data['complexity_score']:.3f}")
        print(f"✅ SUCCESS: Documentation generated successfully ({len(doc_content)} characters)")
        
        return tb_node_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])