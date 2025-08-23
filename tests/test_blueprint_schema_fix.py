"""
Test file for blueprint schema fix.
Tests the current broken state and validates the fix.
"""

import sqlite3
import tempfile
import os
import sys
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ltms.database.schema import create_tables
from ltms.services.blueprint_service import BlueprintManager


class TestBlueprintSchemaFix:
    """Test class for blueprint schema fix validation."""
    
    def setup_method(self):
        """Set up test database for each test."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create connection and tables
        self.conn = sqlite3.connect(self.db_path)
        create_tables(self.conn)
    
    def teardown_method(self):
        """Clean up test database."""
        self.conn.close()
        os.unlink(self.db_path)
    
    def test_current_broken_state(self):
        """Test that blueprint creation currently fails due to missing metadata_json column."""
        # This test should fail - confirming the current broken state
        with pytest.raises(Exception) as exc_info:
            blueprint_manager = BlueprintManager(self.conn)
            # Try to create a blueprint - this should fail
            blueprint_manager.create_blueprint(
                title="Test Blueprint",
                description="Test description",
                project_id="test_project"
            )
        
        # Verify the error is about missing metadata_json column
        error_msg = str(exc_info.value)
        assert ("metadata_json" in error_msg or 
                "no column named" in error_msg)
    
    def test_schema_mismatch(self):
        """Test that there's a mismatch between main schema and blueprint service schema."""
        cursor = self.conn.cursor()
        
        # Check what columns exist in TaskBlueprints table
        cursor.execute("PRAGMA table_info(TaskBlueprints)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Main schema should NOT have metadata_json
        assert "metadata_json" not in column_names
        
        # But blueprint service expects it
        # This confirms the schema mismatch
    
    def test_blueprint_service_table_creation(self):
        """Test that blueprint service can create its own tables."""
        # This should work - blueprint service creates its own table structure
        blueprint_manager = BlueprintManager(self.conn)
        
        # Verify the table was created with metadata_json column
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(TaskBlueprints)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Now it should have metadata_json
        assert "metadata_json" in column_names
    
    def test_blueprint_creation_after_fix(self):
        """Test that blueprint creation works after the fix."""
        # Create blueprint manager (this will fix the schema)
        blueprint_manager = BlueprintManager(self.conn)
        
        # Now try to create a blueprint - this should work
        blueprint = blueprint_manager.create_blueprint(
            title="Test Blueprint",
            description="Test description",
            project_id="test_project"
        )
        
        # Verify the blueprint was created
        assert blueprint is not None
        assert blueprint.title == "Test Blueprint"
        assert blueprint.description == "Test description"
        assert blueprint.project_id == "test_project"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
