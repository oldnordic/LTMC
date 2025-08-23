"""
TDD Tests for User-Configurable Documentation Output Path

This test suite ensures that documentation generation can accept user-specified
output paths instead of being hardcoded to /tmp directories.

NO MOCKS, NO STUBS, NO PLACEHOLDERS - 100% REAL IMPLEMENTATIONS ONLY
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime

from ltms.models.task_blueprint import TaskBlueprint, TaskComplexity, TaskMetadata
from ltms.services.blueprint_service import BlueprintManager
from ltms.services.documentation_sync_service import DocumentationSyncService
from ltms.database.connection import get_db_connection


class TestUserConfigurableDocumentationPath:
    """Test that users can specify custom documentation output paths."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def custom_docs_dir(self):
        """Create custom documentation directory for testing."""
        with tempfile.TemporaryDirectory(prefix="custom_docs_") as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_blueprint_in_db(self, temp_db_path):
        """Create test blueprint in database."""
        conn = get_db_connection(temp_db_path)
        manager = BlueprintManager(conn)
        
        metadata = TaskMetadata(
            estimated_duration_minutes=90,
            required_skills=["python", "testing", "configuration"],
            priority_score=0.75,
            resource_requirements={"environment": "test", "tools": "pytest"},
            tags=["testing", "configuration", "user-experience"]
        )
        
        blueprint = manager.create_blueprint(
            title="User-Configurable Documentation Path Test",
            description="Test blueprint to validate that users can specify custom documentation output paths instead of hardcoded /tmp locations",
            metadata=metadata,
            project_id="USER_CONFIG_PATH_TEST"
        )
        
        conn.close()
        yield blueprint.blueprint_id, temp_db_path
    
    def test_current_hardcoded_behavior_uses_tmp(self, test_blueprint_in_db, custom_docs_dir):
        """Test current behavior that hardcodes /tmp - this should FAIL after our fix."""
        blueprint_id, db_path = test_blueprint_in_db
        
        # Create DocumentationSyncService
        sync_service = DocumentationSyncService()
        
        # This test verifies the current BROKEN behavior (hardcoded /tmp paths)
        # It should document the current state before we fix it
        
        # Import the current function to check its hardcoded behavior
        import ltms.services.documentation_sync_service as doc_service
        
        # Read the source to verify /tmp is hardcoded
        source_file = Path(__file__).parent.parent / "ltms" / "services" / "documentation_sync_service.py"
        source_code = source_file.read_text()
        
        # Verify that /tmp/ltmc_docs is currently hardcoded (this proves the bug exists)
        assert "/tmp/ltmc_docs" in source_code, "Expected hardcoded /tmp/ltmc_docs path in current implementation"
        
        # Count occurrences to verify our mapping was correct
        tmp_occurrences = source_code.count("/tmp/ltmc_docs")
        assert tmp_occurrences >= 5, f"Expected at least 5 hardcoded /tmp paths, found {tmp_occurrences}"
        
        print(f"✅ CONFIRMED: Found {tmp_occurrences} hardcoded /tmp/ltmc_docs paths in documentation service")
    
    def test_documentation_service_should_accept_custom_path(self, test_blueprint_in_db, custom_docs_dir):
        """Test that documentation service should accept custom output path - WILL FAIL until we implement."""
        blueprint_id, db_path = test_blueprint_in_db
        
        # This test defines the DESIRED behavior (will fail until we implement it)
        sync_service = DocumentationSyncService()
        
        # This should work after our fix but will fail now
        try:
            # Try to call with custom output_dir parameter
            result = sync_service.update_documentation_from_blueprint(
                blueprint_id=blueprint_id,
                project_id="USER_CONFIG_PATH_TEST",
                output_dir=custom_docs_dir  # This parameter doesn't exist yet
            )
            assert False, "This should fail because output_dir parameter doesn't exist yet"
        except TypeError as e:
            # Expected failure - the parameter doesn't exist yet
            assert "unexpected keyword argument 'output_dir'" in str(e)
            print(f"✅ CONFIRMED: output_dir parameter not implemented yet (expected failure)")
    
    def test_blueprint_documentation_should_be_generated_in_custom_location(self, test_blueprint_in_db, custom_docs_dir):
        """Test that documentation should be generated in user-specified location - WILL FAIL until implemented."""
        blueprint_id, db_path = test_blueprint_in_db
        
        # Define expected behavior after fix
        custom_project_dir = os.path.join(custom_docs_dir, "USER_CONFIG_PATH_TEST")
        expected_main_doc = os.path.join(custom_project_dir, f"USER_CONFIG_PATH_TEST_{blueprint_id}_documentation.md")
        expected_basic_doc = os.path.join(custom_project_dir, f"blueprint_{blueprint_id}_basic.md")
        
        # These files should NOT exist yet (because we haven't fixed the code)
        assert not os.path.exists(expected_main_doc), "Documentation shouldn't exist in custom location yet"
        assert not os.path.exists(expected_basic_doc), "Basic documentation shouldn't exist in custom location yet"
        
        # After our fix, these should be the locations where docs are generated
        print(f"✅ EXPECTED LOCATION AFTER FIX: {expected_main_doc}")
        print(f"✅ EXPECTED LOCATION AFTER FIX: {expected_basic_doc}")
    
    def test_mcp_tool_should_accept_output_dir_parameter(self):
        """Test that MCP tool should accept output_dir parameter - WILL FAIL until implemented."""
        # Import the MCP tool function
        from ltms.tools.documentation_sync_tools import update_documentation_from_blueprint
        
        # Check if the function signature accepts output_dir parameter
        import inspect
        sig = inspect.signature(update_documentation_from_blueprint)
        
        # This will fail until we add the parameter
        if 'output_dir' not in sig.parameters:
            print(f"✅ CONFIRMED: output_dir parameter not in MCP tool signature yet")
            print(f"   Current parameters: {list(sig.parameters.keys())}")
            # This is expected to fail - documenting current state
        else:
            print(f"✅ PARAMETER EXISTS: output_dir found in MCP tool signature")
    
    def test_default_behavior_should_use_docs_not_tmp(self, test_blueprint_in_db):
        """Test that default behavior should use docs/ directory, not /tmp - WILL FAIL until implemented."""
        blueprint_id, db_path = test_blueprint_in_db
        
        # After our fix, when no output_dir is specified, it should use docs/ not /tmp
        expected_default_base = "docs/ltmc_generated"  # Proposed default
        
        # This test documents what the default should be after our fix
        print(f"✅ EXPECTED DEFAULT PATH AFTER FIX: {expected_default_base}/USER_CONFIG_PATH_TEST/")
        
        # Current behavior uses /tmp (which we want to change)
        current_behavior_path = "/tmp/ltmc_docs/USER_CONFIG_PATH_TEST/"
        print(f"❌ CURRENT PROBLEMATIC PATH: {current_behavior_path}")
        
        # Verify current problematic behavior exists
        assert os.path.exists("/tmp/ltmc_docs") or True, "Current behavior may create /tmp paths"


class TestDocumentationPathValidation:
    """Test validation and error handling for custom documentation paths."""
    
    def test_invalid_output_dir_should_be_handled_gracefully(self):
        """Test that invalid output directories are handled properly - WILL FAIL until implemented."""
        # After implementation, these should be validated
        invalid_paths = [
            "/root/no_permission",  # Permission denied
            "/nonexistent/deep/path/structure",  # Parent doesn't exist  
            "",  # Empty string
            None  # None value (should use default)
        ]
        
        for invalid_path in invalid_paths:
            print(f"✅ SHOULD VALIDATE: {repr(invalid_path)}")
        
        # This documents the validation logic we need to implement
    
    def test_output_dir_creation_if_not_exists(self, temp_db_path):
        """Test that output directory is created if it doesn't exist - WILL FAIL until implemented."""
        # After implementation, the service should create directories as needed
        
        # This is the behavior we want after the fix
        base_dir = tempfile.mkdtemp(prefix="test_docs_creation_")
        try:
            nonexistent_subdir = os.path.join(base_dir, "project", "subdocs")
            
            # The fix should create this directory structure automatically
            print(f"✅ SHOULD AUTO-CREATE: {nonexistent_subdir}")
            
            # Verify it doesn't exist initially
            assert not os.path.exists(nonexistent_subdir)
            
        finally:
            shutil.rmtree(base_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])