"""
Backend Success Reporting Accuracy Tests for LTMC Phase 4.

This test suite exposes backend success reporting accuracy bugs where functions
claim complete success when only partial backends succeed.

CURRENT BUG: link_resources reports 'backends_used': ['neo4j', 'sqlite'] and 
'success': True even when Neo4j fails and only SQLite actually works.

These tests SHOULD FAIL until accurate backend reporting is implemented.
"""

import pytest
import time
import logging
import os
import sqlite3
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Real LTMC MCP imports
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.config import Config
from ltms.services.context_service import (
    get_neo4j_store,
    initialize_neo4j_store,
    check_neo4j_health,
    link_resources as direct_link_resources
)

# Configure logging to capture warnings
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TestBackendSuccessReportingAccuracy:
    """Tests for accurate backend success reporting in LTMC operations."""

    @pytest.fixture(autouse=True)
    def setup_test_resources(self):
        """Set up test resources in SQLite for testing."""
        # Create test resources in SQLite
        db_path = Config.get_db_path()
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Clean up any existing test data - delete links first due to foreign key constraints
        cursor.execute("DELETE FROM resource_links WHERE metadata LIKE '%backend_accuracy_test%'")
        cursor.execute("DELETE FROM resources WHERE file_name LIKE 'test_backend_accuracy_%'")
        conn.commit()
        
        # Create test resources
        test_resources = [
            (1001, 'test_backend_accuracy_doc1.md', 'document'),
            (1002, 'test_backend_accuracy_doc2.md', 'document'),
            (1003, 'test_backend_accuracy_doc3.md', 'document'),
        ]
        
        for resource_id, file_name, resource_type in test_resources:
            cursor.execute("""
                INSERT OR REPLACE INTO resources (id, file_name, type, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (resource_id, file_name, resource_type))
        
        conn.commit()
        close_db_connection(conn)
        
        yield
        
        # Cleanup - delete links first due to foreign key constraints
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resource_links WHERE metadata LIKE '%backend_accuracy_test%'")
        cursor.execute("DELETE FROM resources WHERE file_name LIKE 'test_backend_accuracy_%'")
        conn.commit()
        close_db_connection(conn)

    def test_neo4j_connection_failure_accurate_reporting_validation(self):
        """
        Test that validates ACCURATE backend success reporting when Neo4j connection fails.
        
        This test validates that the current implementation correctly reports:
        - 'success': True (because SQLite succeeded)
        - 'backends_used': ['sqlite'] (only SQLite, not Neo4j)
        - 'neo4j_fallback_reason': explanation of why Neo4j failed
        
        This test should PASS if reporting is accurate, FAIL if misleading.
        """
        # Force Neo4j connection to fail by mocking it as unavailable
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            # Call the real link_resources function
            result = direct_link_resources(
                source_resource_id=1001,
                target_resource_id=1002,
                link_type="accurate_reporting_test",
                weight=0.95,
                metadata='{"test_type": "backend_accuracy_test", "scenario": "neo4j_connection_failure"}'
            )
            
            print(f"DEBUG: link_resources result: {result}")
            
            # Validate accurate success reporting
            assert result.get('success') is True, "Should succeed because SQLite worked"
            
            backends_used = result.get('backends_used', [])
            print(f"DEBUG: backends_used: {backends_used}")
            
            # CRITICAL: Neo4j should NOT be in backends_used when it failed
            assert 'neo4j' not in backends_used, (
                f"INACCURATE REPORTING: backends_used includes 'neo4j' ({backends_used}) "
                f"but Neo4j was not available. Should only include backends that actually worked."
            )
            
            # Should only report SQLite since that's what actually worked
            assert 'sqlite' in backends_used, (
                f"Missing SQLite in backends_used ({backends_used}) but SQLite should have worked"
            )
            
            # Should provide fallback explanation when Neo4j fails
            assert 'neo4j_fallback_reason' in result or 'fallback' in result.get('message', '').lower(), (
                f"Missing Neo4j fallback explanation. Result: {result}"
            )
            
            # Message should reflect actual backends used
            message = result.get('message', '')
            assert 'sqlite' in message.lower(), f"Message should mention SQLite: {message}"
            assert 'neo4j' not in message.lower() or 'fallback' in message.lower(), (
                f"Message shouldn't claim Neo4j success without fallback indication: {message}"
            )
            
            # Verify SQLite actually worked (this should pass)
            self._verify_sqlite_link_exists(1001, 1002, "accurate_reporting_test")

    def test_neo4j_authentication_failure_still_claims_neo4j_backend(self):
        """
        Test that exposes misleading reporting when Neo4j auth fails but code 
        still claims to have tried Neo4j in the backends_used list.
        
        This test SHOULD FAIL if the code claims Neo4j was used when it 
        actually failed due to authentication or other runtime errors.
        """
        # Mock Neo4j store that appears available but fails on operations
        mock_store = MagicMock()
        mock_store.is_available.return_value = True  # Appears available
        mock_store.create_document_node.side_effect = Exception("Authentication failed: Invalid credentials")
        
        with patch('ltms.services.context_service.get_neo4j_store', return_value=mock_store):
            result = direct_link_resources(
                source_resource_id=1001,
                target_resource_id=1003,
                link_type="auth_failure_test",
                weight=0.8,
                metadata='{"test_type": "backend_accuracy_test", "scenario": "neo4j_auth_failure"}'
            )
            
            print(f"DEBUG: Auth failure result: {result}")
            backends_used = result.get('backends_used', [])
            print(f"DEBUG: Auth failure backends_used: {backends_used}")
            
            # Current behavior reports success even when Neo4j fails
            assert result.get('success') is True
            
            # THE BUG: If Neo4j operation failed, it shouldn't be listed as successfully used
            if 'neo4j' in backends_used:
                # Check if the mock was actually called and failed
                assert mock_store.create_document_node.called, "Mock should have been called"
                
                # If neo4j is in backends_used, the operations should have succeeded
                # But we know they threw exceptions, so this is misleading
                neo4j_error_occurred = any(call.args for call in mock_store.create_document_node.call_args_list 
                                         if hasattr(call, 'side_effect'))
                
                if hasattr(mock_store.create_document_node, 'side_effect'):
                    assert False, (
                        f"MISLEADING BACKEND REPORTING: backends_used includes 'neo4j' ({backends_used}) "
                        f"but Neo4j operations failed with authentication error. The function should not "
                        f"claim neo4j success when it threw an exception."
                    )
            
            # Verify SQLite worked (this should pass)
            self._verify_sqlite_link_exists(1001, 1003, "auth_failure_test")

    def test_neo4j_relationship_creation_failure_but_claims_success(self):
        """
        Test that exposes potential bug when Neo4j node creation succeeds but 
        relationship creation fails, yet code might still claim Neo4j success.
        
        This test SHOULD FAIL if the code reports Neo4j in backends_used when
        the relationship creation step failed.
        """
        # Mock Neo4j store where node creation works but relationship creation fails
        mock_store = MagicMock()
        mock_store.is_available.return_value = True
        
        # Node creation succeeds
        mock_store.create_document_node.return_value = {'success': True}
        
        # But relationship creation fails
        mock_store.create_relationship.return_value = {
            'success': False, 
            'error': 'Constraint violation: Relationship already exists with different properties'
        }
        
        with patch('ltms.services.context_service.get_neo4j_store', return_value=mock_store):
            result = direct_link_resources(
                source_resource_id=1002,
                target_resource_id=1003,
                link_type="relationship_failure_test",
                weight=0.75,
                metadata='{"test_type": "backend_accuracy_test", "scenario": "neo4j_relationship_failure"}'
            )
            
            print(f"DEBUG: Relationship failure result: {result}")
            backends_used = result.get('backends_used', [])
            print(f"DEBUG: Relationship failure backends_used: {backends_used}")
            
            # The operation should still succeed because SQLite worked
            assert result.get('success') is True
            
            # CRITICAL TEST: Neo4j should NOT be in backends_used when relationship creation failed
            if 'neo4j' in backends_used:
                # Verify that relationship creation was actually attempted and failed
                assert mock_store.create_relationship.called, "Relationship creation should have been attempted"
                
                # Check the return value from create_relationship
                rel_call_result = mock_store.create_relationship.return_value
                rel_success = rel_call_result.get('success', False)
                
                assert rel_success is True, (
                    f"MISLEADING BACKEND REPORTING: backends_used includes 'neo4j' ({backends_used}) "
                    f"but Neo4j relationship creation failed (success={rel_success}). "
                    f"If the full Neo4j operation didn't succeed, it shouldn't be listed in backends_used."
                )
            
            # Verify SQLite worked
            self._verify_sqlite_link_exists(1002, 1003, "relationship_failure_test")

    def test_both_backends_fail_should_report_failure(self):
        """
        Test that when both Neo4j AND SQLite fail, the operation should report failure.
        
        This test SHOULD FAIL if the code reports success when both backends fail.
        """
        # Mock Neo4j to fail
        mock_store = MagicMock()
        mock_store.is_available.return_value = True
        mock_store.create_document_node.side_effect = Exception("Neo4j connection lost")
        
        # Mock SQLite to fail as well
        with patch('ltms.services.context_service.get_neo4j_store', return_value=mock_store):
            with patch('ltms.database.connection.get_db_connection') as mock_get_conn:
                mock_conn = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.execute.side_effect = Exception("SQLite database locked")
                mock_conn.cursor.return_value = mock_cursor
                mock_get_conn.return_value = mock_conn
                
                result = direct_link_resources(
                    source_resource_id=1001,
                    target_resource_id=1002,
                    link_type="both_backends_fail_test",
                    weight=0.5
                )
                
                print(f"DEBUG: Both backends fail result: {result}")
                
                # When both backends fail, the operation should report failure
                assert result.get('success') is False, (
                    f"INACCURATE SUCCESS REPORTING: Operation reports success when both "
                    f"Neo4j and SQLite failed. Result: {result}"
                )
                
                # Should not claim any backends were used successfully
                backends_used = result.get('backends_used', [])
                assert len(backends_used) == 0, (
                    f"INACCURATE BACKEND REPORTING: Claims backends were used ({backends_used}) "
                    f"when both Neo4j and SQLite failed"
                )

    def test_accurate_vs_inaccurate_backend_reporting_comparison(self):
        """
        Test misleading success reporting when Neo4j authentication fails.
        
        This test SHOULD FAIL because link_resources reports Neo4j success
        even when authentication fails and only SQLite works.
        """
        # Mock Neo4j store with authentication failure
        mock_store = MagicMock()
        mock_store.is_available.return_value = False  # Simulate auth failure
        mock_store.create_document_node.side_effect = Exception("Authentication failed")
        
        with patch('ltms.services.context_service.get_neo4j_store', return_value=mock_store):
            result = direct_link_resources(
                source_resource_id=1001,
                target_resource_id=1003,
                link_type="auth_failure_test",
                weight=0.8,
                metadata='{"test_type": "backend_accuracy_test", "scenario": "neo4j_auth_failure"}'
            )
            
            # Current behavior reports success even when Neo4j fails
            assert result.get('success') is True
            backends_used = result.get('backends_used', [])
            
            # THE BUG: Reports neo4j success when authentication failed
            if 'neo4j' in backends_used:
                # Verify Neo4j is actually available (should fail with auth issues)
                assert mock_store.is_available(), (
                    f"MISLEADING SUCCESS REPORTING: backends_used includes 'neo4j' ({backends_used}) "
                    f"but Neo4j store is_available() returned False due to authentication failure. "
                    f"Partial failure should not be reported as complete success."
                )
            
            # Verify SQLite worked
            self._verify_sqlite_link_exists(1001, 1003, "auth_failure_test")

    def test_neo4j_partial_failure_vs_complete_success_distinction(self):
        """
        Test that partial success (SQLite only) is clearly distinguished from 
        complete success (Neo4j + SQLite).
        
        This test SHOULD FAIL because there's no clear distinction between
        partial and complete success in current reporting.
        """
        # Test with working Neo4j (if available)
        working_neo4j_result = direct_link_resources(
            source_resource_id=1001,
            target_resource_id=1002,
            link_type="complete_success_test",
            weight=0.9
        )
        
        # Test with failed Neo4j
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            partial_success_result = direct_link_resources(
                source_resource_id=1002,
                target_resource_id=1003,
                link_type="partial_success_test", 
                weight=0.9
            )
        
        # Both should report success=True (current behavior)
        assert working_neo4j_result.get('success') is True
        assert partial_success_result.get('success') is True
        
        # THE BUG: No clear distinction between partial and complete success
        working_backends = set(working_neo4j_result.get('backends_used', []))
        partial_backends = set(partial_success_result.get('backends_used', []))
        
        # This should fail to expose the lack of distinction
        assert working_backends != partial_backends, (
            f"MISLEADING SUCCESS REPORTING: No distinction between complete success "
            f"(working Neo4j: {working_backends}) and partial success "
            f"(failed Neo4j: {partial_backends}). Both report the same backends_used, "
            f"making it impossible for users to know if Neo4j actually worked."
        )

    def test_backends_used_accuracy_vs_actual_storage(self):
        """
        Test that backends_used accurately reflects where data was actually stored.
        
        This test SHOULD FAIL because backends_used includes Neo4j even when
        data was only stored in SQLite.
        """
        # Force Neo4j to fail
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            result = direct_link_resources(
                source_resource_id=1001,
                target_resource_id=1002,
                link_type="storage_accuracy_test",
                weight=0.85,
                metadata='{"test_type": "backend_accuracy_test", "scenario": "storage_verification"}'
            )
            
            backends_used = result.get('backends_used', [])
            
            # Check actual storage in each backend
            sqlite_exists = self._check_sqlite_link_exists(1001, 1002, "storage_accuracy_test")
            neo4j_exists = self._check_neo4j_link_exists(1001, 1002, "storage_accuracy_test")
            
            # Verify backends_used accuracy
            if 'sqlite' in backends_used:
                assert sqlite_exists, (
                    f"INACCURATE REPORTING: backends_used includes 'sqlite' ({backends_used}) "
                    f"but no link found in SQLite database."
                )
            
            if 'neo4j' in backends_used:
                assert neo4j_exists, (
                    f"MISLEADING SUCCESS REPORTING: backends_used includes 'neo4j' ({backends_used}) "
                    f"but no link found in Neo4j database. This indicates the function "
                    f"is claiming Neo4j success when data was only stored in SQLite."
                )

    def test_error_transparency_vs_hidden_failures(self):
        """
        Test that Neo4j failures are clearly reported, not hidden in warnings.
        
        This test SHOULD FAIL because Neo4j failures are currently logged as
        warnings but not reflected in the success response.
        """
        # Capture log warnings
        import logging
        from io import StringIO
        import sys
        
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger('ltms.services.context_service')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        
        try:
            # Force Neo4j to fail with specific error
            mock_store = MagicMock()
            mock_store.is_available.return_value = True
            mock_store.create_document_node.side_effect = Exception("Connection timeout")
            mock_store.create_relationship.side_effect = Exception("Connection timeout")
            
            with patch('ltms.services.context_service.get_neo4j_store', return_value=mock_store):
                result = direct_link_resources(
                    source_resource_id=1002,
                    target_resource_id=1003,
                    link_type="error_transparency_test",
                    weight=0.7
                )
                
                # Check if Neo4j error was logged
                log_output = log_capture.getvalue()
                neo4j_error_logged = "Neo4j" in log_output and "failed" in log_output
                
                backends_used = result.get('backends_used', [])
                
                # THE BUG: Neo4j failures are hidden from user
                if neo4j_error_logged and 'neo4j' in backends_used:
                    assert 'error' in result or 'neo4j_error' in result or 'failed_backends' in result, (
                        f"HIDDEN FAILURE: Neo4j error was logged ({log_output.strip()}) "
                        f"but not reported in result. backends_used: {backends_used}. "
                        f"Result: {result}. Users cannot distinguish between complete "
                        f"success and partial failure with hidden errors."
                    )
        
        finally:
            logger.removeHandler(handler)

    def test_user_experience_misleading_messages(self):
        """
        Test that success messages accurately reflect what actually happened.
        
        This test SHOULD FAIL because success messages claim dual-backend
        success even when only SQLite worked.
        """
        # Force Neo4j to fail
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            result = direct_link_resources(
                source_resource_id=1001,
                target_resource_id=1003,
                link_type="user_experience_test",
                weight=0.75
            )
            
            message = result.get('message', '')
            backends_used = result.get('backends_used', [])
            
            # Check actual backend usage
            neo4j_actually_used = self._check_neo4j_link_exists(1001, 1003, "user_experience_test")
            
            # THE BUG: Message claims neo4j success when it wasn't used
            if 'neo4j' in message.lower() and not neo4j_actually_used:
                assert False, (
                    f"MISLEADING USER MESSAGE: Success message mentions Neo4j ('{message}') "
                    f"and backends_used includes neo4j ({backends_used}) but Neo4j was not "
                    f"actually used. This misleads users about the actual operation result."
                )

    def _verify_sqlite_link_exists(self, source_id: int, target_id: int, link_type: str):
        """Verify that a link exists in SQLite database."""
        assert self._check_sqlite_link_exists(source_id, target_id, link_type), (
            f"Link {source_id}->{target_id} ({link_type}) not found in SQLite database"
        )

    def _check_sqlite_link_exists(self, source_id: int, target_id: int, link_type: str) -> bool:
        """Check if a link exists in SQLite database."""
        try:
            db_path = Config.get_db_path()
            conn = get_db_connection(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM resource_links 
                WHERE source_resource_id = ? AND target_resource_id = ? AND link_type = ?
            """, (source_id, target_id, link_type))
            
            count = cursor.fetchone()[0]
            close_db_connection(conn)
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking SQLite link: {e}")
            return False

    def _check_neo4j_link_exists(self, source_id: int, target_id: int, link_type: str) -> bool:
        """Check if a link exists in Neo4j database."""
        try:
            neo4j_store = get_neo4j_store()
            if not neo4j_store:
                return False
                
            # Query Neo4j for the relationship
            result = neo4j_store.query_relationships(str(source_id), link_type, "outgoing")
            if not result.get('success'):
                return False
                
            relationships = result.get('relationships', [])
            for rel in relationships:
                if rel.get('target') == str(target_id) and rel.get('type') == link_type:
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking Neo4j link: {e}")
            return False


class TestBackendSuccessReportingWithMCPTools:
    """Test backend success reporting through actual MCP tool interface."""
    
    @pytest.fixture(autouse=True) 
    def setup_mcp_test_resources(self):
        """Set up resources for MCP tool testing."""
        # Create test resources
        db_path = Config.get_db_path()
        conn = get_db_connection(db_path) 
        cursor = conn.cursor()
        
        # Clean up any existing test data - delete links first due to foreign key constraints
        cursor.execute("DELETE FROM resource_links WHERE metadata LIKE '%mcp_backend_test%'")
        cursor.execute("DELETE FROM resources WHERE file_name LIKE 'test_mcp_backend_%'")
        conn.commit()
        
        # Create test resources
        test_resources = [
            (2001, 'test_mcp_backend_doc1.md', 'document'),
            (2002, 'test_mcp_backend_doc2.md', 'document'),
        ]
        
        for resource_id, file_name, resource_type in test_resources:
            cursor.execute("""
                INSERT OR REPLACE INTO resources (id, file_name, type, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (resource_id, file_name, resource_type))
        
        conn.commit()
        close_db_connection(conn)
        
        yield
        
        # Cleanup - delete links first due to foreign key constraints
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resource_links WHERE metadata LIKE '%mcp_backend_test%'")
        cursor.execute("DELETE FROM resources WHERE file_name LIKE 'test_mcp_backend_%'")
        conn.commit()
        close_db_connection(conn)

    def test_mcp_link_resources_misleading_success_real_call(self):
        """
        Test misleading success reporting through actual MCP tool call.
        
        This test SHOULD FAIL because the MCP tool returns misleading success
        when Neo4j fails but SQLite succeeds.
        """
        # Import the actual MCP tool handler
        from ltms.tools.context_tools import link_resources_handler
        
        # Force Neo4j to fail
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            # Call through actual MCP tool interface
            result = link_resources_handler(
                source_id="2001",
                target_id="2002", 
                relation="mcp_misleading_test",
                weight=0.9,
                metadata='{"test_type": "mcp_backend_test", "scenario": "mcp_interface"}'
            )
            
            # Verify MCP tool reports success
            assert result.get('success') is True
            backends_used = result.get('backends_used', [])
            
            # THE BUG: MCP tool claims neo4j success when it failed
            if 'neo4j' in backends_used:
                # Verify Neo4j actually worked
                neo4j_available = get_neo4j_store() is not None
                assert neo4j_available, (
                    f"MCP TOOL MISLEADING REPORTING: link_resources_handler returned "
                    f"backends_used={backends_used} including 'neo4j' but Neo4j store "
                    f"is not available. This misleads MCP clients about actual operation results."
                )

    def test_mcp_tool_partial_vs_complete_success_user_impact(self):
        """
        Test user impact of partial vs complete success reporting through MCP.
        
        This test SHOULD FAIL because MCP users cannot distinguish between
        partial success (SQLite only) and complete success (Neo4j + SQLite).
        """
        from ltms.tools.context_tools import link_resources_handler
        
        # Test complete success scenario (Neo4j working)
        complete_result = link_resources_handler(
            source_id="2001",
            target_id="2002",
            relation="complete_mcp_test", 
            weight=0.85
        )
        
        # Test partial success scenario (Neo4j failing)
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            partial_result = link_resources_handler(
                source_id="2002", 
                target_id="2001",
                relation="partial_mcp_test",
                weight=0.85
            )
        
        # Both report success (current behavior)
        assert complete_result.get('success') is True
        assert partial_result.get('success') is True
        
        complete_backends = set(complete_result.get('backends_used', []))
        partial_backends = set(partial_result.get('backends_used', []))
        complete_message = complete_result.get('message', '')
        partial_message = partial_result.get('message', '')
        
        # THE BUG: No clear user distinction between partial and complete success
        user_can_distinguish = (
            complete_backends != partial_backends or
            'partial' in partial_message.lower() or
            'fallback' in partial_message.lower() or
            'some backends failed' in partial_message.lower()
        )
        
        assert user_can_distinguish, (
            f"MCP USER EXPERIENCE BUG: Users cannot distinguish between complete success "
            f"(backends: {complete_backends}, message: '{complete_message}') and "
            f"partial success (backends: {partial_backends}, message: '{partial_message}'). "
            f"Both look identical to MCP clients, hiding critical backend status information."
        )


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=long",
        "-x",  # Stop on first failure to see the exact issue
        "--capture=no"  # Show print statements and logs
    ])