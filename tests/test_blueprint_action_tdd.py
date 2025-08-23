"""
TDD Tests for blueprint_action Consolidated Powertool
Tests all 8 blueprint actions with real database operations (NO MOCKS)
"""

import os
import pytest
import tempfile
import sqlite3
from datetime import datetime, timezone

# Add LTMC to path
import sys
sys.path.insert(0, '/home/feanor/Projects/ltmc')

from ltms.tools.consolidated import blueprint_action


class TestBlueprintActionTDD:
    """Test blueprint_action powertool with real database operations."""
    
    def setup_method(self):
        """Setup test environment with real databases."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Set up test environment
        os.environ['DB_PATH'] = self.db_path
        
        # Create test database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Blueprint table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprints (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                project_id TEXT,
                complexity TEXT DEFAULT 'medium',
                complexity_score REAL DEFAULT 0.5,
                priority_score REAL DEFAULT 0.5,
                estimated_duration_minutes INTEGER DEFAULT 60,
                required_skills TEXT,
                tags TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        ''')
        
        # Blueprint dependencies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprint_dependencies (
                id INTEGER PRIMARY KEY,
                dependent_blueprint_id TEXT NOT NULL,
                prerequisite_blueprint_id TEXT NOT NULL,
                dependency_type TEXT DEFAULT 'blocking',
                is_critical INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(dependent_blueprint_id, prerequisite_blueprint_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_blueprint_create_action(self):
        """Test blueprint creation with real database operations."""
        result = blueprint_action(
            action="create",
            title="Test Authentication System",
            description="Implement OAuth2 with JWT tokens and role-based access control",
            project_id="test_project",
            complexity="high",
            estimated_duration_minutes=480,
            required_skills=["python", "security", "oauth2", "jwt"],
            priority_score=0.9,
            tags=["security", "authentication", "critical"]
        )
        
        assert result['success'] is True
        assert 'blueprint_id' in result
        assert result['title'] == "Test Authentication System"
        assert result['complexity'] == "high"
        assert result['project_id'] == "test_project"
        
        # Verify database storage
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM blueprints WHERE id = ?', (result['blueprint_id'],))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[1] == "Test Authentication System"  # title
        assert row[2].startswith("Implement OAuth2")  # description
        assert row[3] == "test_project"  # project_id
    
    def test_blueprint_analyze_complexity_action(self):
        """Test ML-based complexity analysis with real scoring."""
        result = blueprint_action(
            action="analyze_complexity",
            title="Advanced Database Migration System",
            description="Implement zero-downtime database migrations with rollback capabilities, schema versioning, and multi-database support across PostgreSQL, MySQL, and SQLite",
            required_skills=["database", "migrations", "sql", "devops", "python"]
        )
        
        assert result['success'] is True
        assert 'complexity_score' in result
        assert 'complexity_level' in result
        assert 'estimated_duration_minutes' in result
        assert result['complexity_score'] > 0.0
        assert result['complexity_score'] <= 1.0
        
        # Complex task should have high complexity score
        assert result['complexity_score'] >= 0.7  # Due to multi-system complexity
        assert result['complexity_level'] in ['medium', 'high', 'complex']
        assert result['estimated_duration_minutes'] >= 300  # Complex tasks take time
    
    def test_blueprint_list_project_action(self):
        """Test project blueprint listing with filtering."""
        # Create test blueprints
        bp1 = blueprint_action(
            action="create",
            title="User Management System",
            description="Basic user CRUD operations",
            project_id="web_app_project",
            complexity="medium",
            priority_score=0.7
        )
        
        bp2 = blueprint_action(
            action="create", 
            title="Payment Integration",
            description="Stripe payment processing",
            project_id="web_app_project",
            complexity="high",
            priority_score=0.9
        )
        
        bp3 = blueprint_action(
            action="create",
            title="Analytics Dashboard", 
            description="User analytics and reporting",
            project_id="different_project",
            complexity="medium",
            priority_score=0.6
        )
        
        # Test project filtering
        result = blueprint_action(
            action="list_project",
            project_id="web_app_project",
            limit=10
        )
        
        assert result['success'] is True
        assert len(result['blueprints']) == 2
        assert result['project_id'] == "web_app_project"
        
        # Verify priority ordering (higher priority first)
        blueprints = result['blueprints']
        assert blueprints[0]['title'] == "Payment Integration"  # priority 0.9
        assert blueprints[1]['title'] == "User Management System"  # priority 0.7
        
        # Test complexity filtering
        result = blueprint_action(
            action="list_project",
            project_id="web_app_project", 
            min_complexity="high"
        )
        
        assert result['success'] is True
        assert len(result['blueprints']) == 1
        assert result['blueprints'][0]['title'] == "Payment Integration"
    
    def test_blueprint_add_dependency_action(self):
        """Test blueprint dependency management with real relationships."""
        # Create prerequisite and dependent blueprints
        auth_bp = blueprint_action(
            action="create",
            title="Authentication System",
            description="OAuth2 authentication",
            project_id="test_project"
        )
        
        user_bp = blueprint_action(
            action="create",
            title="User Management",
            description="User CRUD operations", 
            project_id="test_project"
        )
        
        api_bp = blueprint_action(
            action="create",
            title="REST API",
            description="API endpoints",
            project_id="test_project"
        )
        
        # Add dependencies: API depends on User, User depends on Auth
        dep1_result = blueprint_action(
            action="add_dependency",
            dependent_blueprint_id=user_bp['blueprint_id'],
            prerequisite_blueprint_id=auth_bp['blueprint_id'],
            dependency_type="blocking",
            is_critical=True
        )
        
        dep2_result = blueprint_action(
            action="add_dependency",
            dependent_blueprint_id=api_bp['blueprint_id'],
            prerequisite_blueprint_id=user_bp['blueprint_id'],
            dependency_type="blocking",
            is_critical=True
        )
        
        assert dep1_result['success'] is True
        assert dep2_result['success'] is True
        
        # Verify database storage
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM blueprint_dependencies')
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 2
    
    def test_blueprint_resolve_order_action(self):
        """Test dependency-based execution order resolution."""
        # Create blueprints with complex dependency chain
        auth_bp = blueprint_action(action="create", title="Auth", description="Auth system", project_id="test")
        db_bp = blueprint_action(action="create", title="Database", description="DB setup", project_id="test")  
        user_bp = blueprint_action(action="create", title="User", description="User mgmt", project_id="test")
        api_bp = blueprint_action(action="create", title="API", description="REST API", project_id="test")
        
        # Dependencies: API -> User -> Auth, API -> Database
        blueprint_action(
            action="add_dependency",
            dependent_blueprint_id=user_bp['blueprint_id'],
            prerequisite_blueprint_id=auth_bp['blueprint_id']
        )
        blueprint_action(
            action="add_dependency", 
            dependent_blueprint_id=api_bp['blueprint_id'],
            prerequisite_blueprint_id=user_bp['blueprint_id']
        )
        blueprint_action(
            action="add_dependency",
            dependent_blueprint_id=api_bp['blueprint_id'], 
            prerequisite_blueprint_id=db_bp['blueprint_id']
        )
        
        # Resolve execution order
        result = blueprint_action(
            action="resolve_order",
            blueprint_ids=[
                api_bp['blueprint_id'],
                user_bp['blueprint_id'], 
                auth_bp['blueprint_id'],
                db_bp['blueprint_id']
            ]
        )
        
        assert result['success'] is True
        assert 'execution_order' in result
        
        order = result['execution_order']
        auth_pos = next(i for i, bp in enumerate(order) if bp['blueprint_id'] == auth_bp['blueprint_id'])
        user_pos = next(i for i, bp in enumerate(order) if bp['blueprint_id'] == user_bp['blueprint_id'])
        api_pos = next(i for i, bp in enumerate(order) if bp['blueprint_id'] == api_bp['blueprint_id'])
        
        # Verify topological ordering
        assert auth_pos < user_pos  # Auth before User
        assert user_pos < api_pos   # User before API
    
    def test_blueprint_update_metadata_action(self):
        """Test blueprint metadata updates."""
        # Create blueprint
        bp = blueprint_action(
            action="create",
            title="Initial System",
            description="Basic implementation",
            project_id="test",
            complexity="medium",
            estimated_duration_minutes=240
        )
        
        # Update metadata
        result = blueprint_action(
            action="update_metadata",
            blueprint_id=bp['blueprint_id'],
            estimated_duration_minutes=360,
            priority_score=0.95,
            required_skills=["python", "fastapi", "postgresql"],
            tags=["api", "database", "critical"]
        )
        
        assert result['success'] is True
        assert result['estimated_duration_minutes'] == 360
        assert result['priority_score'] == 0.95
        
        # Verify database update
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT estimated_duration_minutes, priority_score FROM blueprints WHERE id = ?', 
                      (bp['blueprint_id'],))
        row = cursor.fetchone()
        conn.close()
        
        assert row[0] == 360  # duration updated
        assert abs(row[1] - 0.95) < 0.01  # priority updated
    
    def test_blueprint_get_dependencies_action(self):
        """Test blueprint dependency retrieval."""
        # Create blueprints with dependencies
        auth_bp = blueprint_action(action="create", title="Auth", description="Auth", project_id="test")
        user_bp = blueprint_action(action="create", title="User", description="User", project_id="test")
        
        blueprint_action(
            action="add_dependency",
            dependent_blueprint_id=user_bp['blueprint_id'],
            prerequisite_blueprint_id=auth_bp['blueprint_id'],
            dependency_type="blocking"
        )
        
        # Get dependencies
        result = blueprint_action(
            action="get_dependencies",
            blueprint_id=user_bp['blueprint_id']
        )
        
        assert result['success'] is True
        assert len(result['dependencies']) == 1
        assert result['dependencies'][0]['prerequisite_blueprint_id'] == auth_bp['blueprint_id']
        assert result['dependencies'][0]['dependency_type'] == "blocking"
    
    def test_blueprint_delete_action(self):
        """Test blueprint deletion with dependency cleanup."""
        # Create blueprint
        bp = blueprint_action(
            action="create",
            title="Test Blueprint",
            description="To be deleted",
            project_id="test"
        )
        
        blueprint_id = bp['blueprint_id']
        
        # Verify creation
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM blueprints WHERE id = ?', (blueprint_id,))
        assert cursor.fetchone()[0] == 1
        conn.close()
        
        # Delete blueprint
        result = blueprint_action(
            action="delete",
            blueprint_id=blueprint_id
        )
        
        assert result['success'] is True
        assert result['blueprint_id'] == blueprint_id
        
        # Verify deletion
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM blueprints WHERE id = ?', (blueprint_id,))
        assert cursor.fetchone()[0] == 0
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])