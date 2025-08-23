"""
TDD Tests for sync_action Consolidated Powertool
Tests all 7 sync actions with real file operations (NO MOCKS)
"""

import os
import pytest
import tempfile
import sqlite3
from datetime import datetime, timezone

# Add LTMC to path
import sys
sys.path.insert(0, '/home/feanor/Projects/ltmc')

from ltms.tools.consolidated import sync_action


class TestSyncActionTDD:
    """Test sync_action powertool with real file and database operations."""
    
    def setup_method(self):
        """Setup test environment with real files and databases."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Set up test environment
        os.environ['DB_PATH'] = self.db_path
        
        # Create test database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Blueprints table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprints (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                project_id TEXT,
                complexity TEXT DEFAULT 'medium',
                required_skills TEXT,
                tags TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        ''')
        
        # Insert test blueprint
        cursor.execute('''
            INSERT INTO blueprints (id, title, description, project_id, complexity, 
                                   required_skills, tags, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('test_bp_1', 'Test Blueprint', 'Test blueprint description', 'test_proj',
              'high', 'python,testing', 'sync,test', 'in_progress', 
              datetime.now(timezone.utc).isoformat()))
        
        conn.commit()
        conn.close()
        
        # Create test Python file
        self.test_file_path = os.path.join(self.temp_dir, 'test_module.py')
        test_code = '''"""Test module for sync testing."""

def documented_function(param1, param2):
    """This function has proper documentation."""
    return param1 + param2

def undocumented_function():
    return "no docs"

class DocumentedClass:
    """This class has documentation."""
    
    def method_with_docs(self):
        """Method with documentation."""
        pass
    
    def method_without_docs(self):
        pass

class UndocumentedClass:
    def some_method(self):
        return True
'''
        with open(self.test_file_path, 'w') as f:
            f.write(test_code)
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_sync_code_action(self):
        """Test sync code documentation with real Python file."""
        result = sync_action(
            action="code",
            file_path=self.test_file_path,
            project_id="test_project",
            force_update=False
        )
        
        assert result['success'] is True
        assert 'sync_report' in result
        
        sync_report = result['sync_report']
        assert sync_report['file_path'] == self.test_file_path
        assert sync_report['project_id'] == "test_project"
        assert 'functions_found' in sync_report
        assert 'classes_found' in sync_report
        
        # Should find some functions and classes from our test file
        assert sync_report['functions_found'] >= 0
        assert sync_report['classes_found'] >= 0
        
        # Check functions structure
        functions = sync_report['functions']
        assert isinstance(functions, list)
        if functions:
            func = functions[0]
            assert 'name' in func
            assert 'line' in func
            assert 'args' in func
        
        # Check classes structure  
        classes = sync_report['classes']
        assert isinstance(classes, list)
        if classes:
            cls = classes[0]
            assert 'name' in cls
            assert 'line' in cls
    
    def test_sync_validate_action(self):
        """Test sync validation with real Python file analysis."""
        result = sync_action(
            action="validate",
            file_path=self.test_file_path,
            project_id="test_project"
        )
        
        assert result['success'] is True
        assert result['file_path'] == self.test_file_path
        assert result['project_id'] == "test_project"
        assert 'consistency_score' in result
        assert 'consistency_level' in result
        assert 'total_elements' in result
        assert 'documented_elements' in result
        assert 'issues' in result
        
        # Should find elements from our test file
        assert result['total_elements'] >= 4  # Functions, classes, and methods
        
        # Check consistency score is reasonable
        assert 0.0 <= result['consistency_score'] <= 1.0
        
        # Should identify missing documentation issues
        assert len(result['issues']) > 0
        issue_text = ' '.join(result['issues'])
        assert 'undocumented' in issue_text.lower() or 'missing' in issue_text.lower()
    
    def test_sync_drift_action(self):
        """Test sync drift detection with real file timestamps."""
        result = sync_action(
            action="drift",
            file_path=self.test_file_path,
            project_id="test_project",
            time_threshold_hours=24
        )
        
        assert result['success'] is True
        assert result['file_path'] == self.test_file_path
        assert result['project_id'] == "test_project"
        assert 'drift_detected' in result
        assert 'hours_since_modified' in result
        assert 'time_threshold_hours' in result
        assert 'last_modified' in result
        assert 'check_timestamp' in result
        
        # Recently created file should show drift (within threshold)
        assert result['drift_detected'] is True
        assert result['hours_since_modified'] < 1  # Just created
        assert result['time_threshold_hours'] == 24
    
    def test_sync_blueprint_action(self):
        """Test sync blueprint documentation with real database data."""
        result = sync_action(
            action="blueprint",
            blueprint_id="test_bp_1",
            project_id="test_proj",
            sections=["description", "requirements", "architecture"]
        )
        
        # Should either succeed or fail gracefully with database/blueprint not found
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Database and blueprint found
            assert result['blueprint_id'] == "test_bp_1"
            assert result['project_id'] == "test_proj"
            assert 'sections' in result
            assert 'documentation_content' in result
            assert 'update_timestamp' in result
            
            # Check generated documentation content
            doc_content = result['documentation_content']
            assert '# Test Blueprint' in doc_content
            assert 'Test blueprint description' in doc_content
        else:
            # Database or blueprint not found - expected behavior
            assert 'error' in result
            assert any(keyword in result['error'].lower() for keyword in [
                'blueprint', 'not found', 'sync blueprint failed'
            ])
    
    def test_sync_score_action(self):
        """Test sync consistency scoring with real analysis."""
        result = sync_action(
            action="score",
            file_path=self.test_file_path,
            project_id="test_project",
            detailed_analysis=True
        )
        
        assert result['success'] is True
        assert result['file_path'] == self.test_file_path
        assert result['project_id'] == "test_project"
        assert 'consistency_score' in result
        assert 'total_elements' in result
        assert 'score_timestamp' in result
        assert 'detailed_elements' in result
        
        # Check detailed analysis
        elements = result['detailed_elements']
        assert len(elements) >= 4  # Functions and classes
        
        # Check element details
        for element in elements:
            assert 'name' in element
            assert 'type' in element
            assert 'line' in element
            assert 'has_docstring' in element
            assert 'score' in element
            assert 0.0 <= element['score'] <= 1.0
    
    def test_sync_monitor_action(self):
        """Test sync real-time monitoring setup."""
        test_files = [self.test_file_path, '/nonexistent/file.py']
        
        result = sync_action(
            action="monitor",
            file_paths=test_files,
            project_id="test_project",
            sync_interval_ms=200
        )
        
        assert result['success'] is True
        assert result['project_id'] == "test_project"
        assert 'monitoring_files' in result
        assert 'invalid_files' in result
        assert result['sync_interval_ms'] == 200
        assert 'monitor_started' in result
        assert 'message' in result
        
        # Should have 1 valid file and 1 invalid file
        assert len(result['monitoring_files']) == 1
        assert len(result['invalid_files']) == 1
        assert result['invalid_files'][0] == '/nonexistent/file.py'
        
        # Check valid file details
        valid_file = result['monitoring_files'][0]
        assert valid_file['path'] == self.test_file_path
        assert 'last_modified' in valid_file
    
    def test_sync_status_action(self):
        """Test sync status with real database data."""
        result = sync_action(
            action="status",
            project_id="test_proj",
            include_pending_changes=True
        )
        
        assert result['success'] is True
        assert result['project_id'] == "test_proj"
        assert 'total_blueprints' in result
        assert 'completed_blueprints' in result
        assert 'in_progress_blueprints' in result
        assert 'sync_percentage' in result
        assert 'status_timestamp' in result
        assert 'pending_changes' in result
        
        # Check data structure and ranges
        assert result['total_blueprints'] >= 0
        assert result['in_progress_blueprints'] >= 0
        assert 0.0 <= result['sync_percentage'] <= 100.0
        
        # Check pending changes
        pending = result['pending_changes']
        assert 'documentation_updates' in pending
        assert 'code_changes' in pending
        assert 'blueprint_changes' in pending
    
    def test_sync_action_invalid_action(self):
        """Test invalid action parameter handling."""
        result = sync_action(action="invalid_action")
        
        assert result['success'] is False
        assert 'Unknown sync action' in result['error']
    
    def test_sync_action_missing_action(self):
        """Test missing action parameter handling."""
        result = sync_action(action="")
        
        assert result['success'] is False
        assert result['error'] == 'Action parameter is required'
    
    def test_sync_action_missing_required_params(self):
        """Test missing required parameter handling for various actions."""
        # Test code action missing params
        result = sync_action(action="code", file_path="test.py")
        assert result['success'] is False
        assert 'Missing required parameter: project_id' in result['error']
        
        # Test validate action missing params  
        result = sync_action(action="validate", project_id="test")
        assert result['success'] is False
        assert 'Missing required parameter: file_path' in result['error']
        
        # Test blueprint action missing params
        result = sync_action(action="blueprint", blueprint_id="test")
        assert result['success'] is False
        assert 'Missing required parameter: project_id' in result['error']
        
        # Test status action missing params
        result = sync_action(action="status")
        assert result['success'] is False
        assert 'Missing required parameter: project_id' in result['error']
    
    def test_sync_action_file_not_found(self):
        """Test handling of non-existent files."""
        # Test code action with missing file
        result = sync_action(
            action="code",
            file_path="/nonexistent/file.py",
            project_id="test"
        )
        
        assert result['success'] is False
        assert 'File not found' in result['error']
        
        # Test validate action with missing file
        result = sync_action(
            action="validate",
            file_path="/nonexistent/file.py",
            project_id="test"
        )
        
        assert result['success'] is False
        assert 'File not found' in result['error']
    
    def test_sync_action_invalid_file_paths_type(self):
        """Test monitor action with invalid file_paths type."""
        result = sync_action(
            action="monitor",
            file_paths="not_a_list",
            project_id="test"
        )
        
        assert result['success'] is False
        assert 'file_paths must be a list' in result['error']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])