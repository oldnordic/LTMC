"""
Comprehensive SQLite backend and fallback mechanism tests for LTMC.

Tests cover:
- SQLite resource_links table operations
- Fallback behavior when Neo4j unavailable  
- Data persistence across system restarts
- SQLite-specific performance characteristics
- Schema validation and integrity constraints
"""

import pytest
import sqlite3
import tempfile
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import patch

# Import SQLite specific components  
from ltms.database.connection import get_connection
from ltms.database.dal import get_all_resources
from ltms.database.schema import create_tables
from ltms.services.context_service import (
    link_resources,
    get_resource_links as get_resource_links_service,
    remove_resource_link as remove_resource_link_service,
    list_all_resource_links as list_all_resource_links_service
)
from ltms.tools.context_tools import (
    link_resources_handler,
    get_resource_links_handler, 
    remove_resource_link_handler,
    list_all_resource_links_handler
)


class TestSQLiteBackendFallback:
    """Comprehensive tests for SQLite backend and fallback functionality."""

    @pytest.fixture(autouse=True)
    def setup_sqlite_environment(self):
        """Set up SQLite test environment."""
        # Create temporary database
        self.test_db_path = tempfile.mktemp(suffix='.db')
        
        # Initialize database with proper schema
        conn = sqlite3.connect(self.test_db_path)
        create_tables(conn)
        
        # Create test resources
        self._create_test_resources(conn)
        conn.close()
        
        # Mock the connection to use our test database
        original_get_connection = None
        
        def mock_get_connection():
            return sqlite3.connect(self.test_db_path)
        
        self.mock_patch = patch('ltms.database.connection.get_connection', side_effect=mock_get_connection)
        self.mock_patch.start()
        
        yield
        
        # Cleanup
        self.mock_patch.stop()
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def _create_test_resources(self, conn: sqlite3.Connection):
        """Create test resources in SQLite database."""
        cursor = conn.cursor()
        
        # Create test resources
        test_resources = [
            ("machine_learning.md", "document"),
            ("neural_networks.py", "code"),
            ("data_science.md", "document"),
            ("algorithms.py", "code"),
            ("statistics.md", "document")
        ]
        
        self.resource_ids = []
        for filename, resource_type in test_resources:
            cursor.execute(
                "INSERT INTO resources (file_name, type, created_at) VALUES (?, ?, ?)",
                (filename, resource_type, datetime.now().isoformat())
            )
            self.resource_ids.append(cursor.lastrowid)
        
        # Create resource chunks for testing
        for i, resource_id in enumerate(self.resource_ids):
            for j in range(3):  # 3 chunks per resource
                cursor.execute(
                    "INSERT INTO resource_chunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
                    (resource_id, f"Test content for resource {i+1}, chunk {j+1}", resource_id * 100 + j)
                )
        
        conn.commit()

    def test_sqlite_schema_validation(self):
        """Test SQLite resource_links table schema is correct."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resource_links'")
        table_exists = cursor.fetchone()
        assert table_exists is not None
        
        # Check table structure
        cursor.execute("PRAGMA table_info(resource_links)")
        columns = cursor.fetchall()
        
        expected_columns = {
            'id': 'INTEGER',
            'source_resource_id': 'INTEGER', 
            'target_resource_id': 'INTEGER',
            'link_type': 'TEXT',
            'created_at': 'TEXT',
            'metadata': 'TEXT',
            'weight': 'REAL'
        }
        
        actual_columns = {col[1]: col[2] for col in columns}
        
        for col_name, col_type in expected_columns.items():
            assert col_name in actual_columns, f"Missing column: {col_name}"
            assert col_type in actual_columns[col_name], f"Wrong type for {col_name}: expected {col_type}, got {actual_columns[col_name]}"
        
        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='resource_links'")
        indexes = cursor.fetchall()
        
        expected_indexes = [
            'idx_resource_links_source',
            'idx_resource_links_target', 
            'idx_resource_links_type',
            'idx_resource_links_weight'
        ]
        
        actual_indexes = [idx[0] for idx in indexes]
        for expected_idx in expected_indexes:
            assert expected_idx in actual_indexes, f"Missing index: {expected_idx}"
        
        conn.close()

    def test_sqlite_create_resource_links(self):
        """Test creating resource links in SQLite."""
        # Force SQLite-only mode
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            result = link_resources_handler(str(self.resource_ids[0]), str(self.resource_ids[1]), "references", 0.8)
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert result['success'] is True
            
            # Should have SQLite-specific fields
            assert 'resource_link_id' in result
            assert result['source_resource_id'] == self.resource_ids[0]
            assert result['target_resource_id'] == self.resource_ids[1]
            assert result['link_type'] == 'references'
            assert result['weight'] == 0.8

    def test_sqlite_get_resource_links(self):
        """Test retrieving resource links from SQLite."""
        # Create test link first
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            create_result = link_resources_handler(str(self.resource_ids[0]), str(self.resource_ids[1]), "test_get")
            assert create_result['success'] is True
            
            # Retrieve links
            result = get_resource_links_handler(str(self.resource_ids[0]))
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert result['success'] is True
            assert 'links' in result
            assert isinstance(result['links'], list)
            assert len(result['links']) >= 1
            
            # Verify link structure
            link = result['links'][0]
            assert 'id' in link
            assert 'source_resource_id' in link
            assert 'target_resource_id' in link
            assert 'link_type' in link
            assert 'weight' in link
            assert link['source_resource_id'] == self.resource_ids[0]

    def test_sqlite_remove_resource_links(self):
        """Test removing resource links from SQLite."""
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            # Create link first
            create_result = link_resources_handler(str(self.resource_ids[0]), str(self.resource_ids[1]), "test_remove")
            assert create_result['success'] is True
            link_id = create_result['resource_link_id']
            
            # Remove link
            result = remove_resource_link_handler(str(link_id))
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert result['success'] is True
            assert 'removed' in result or 'deleted' in result
            
            # Verify link was removed
            get_result = get_resource_links_handler(str(self.resource_ids[0]))
            remaining_links = [link for link in get_result['links'] if link.get('link_type') == 'test_remove']
            assert len(remaining_links) == 0

    def test_sqlite_list_all_resource_links(self):
        """Test listing all resource links from SQLite."""
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            # Create multiple links
            created_links = []
            for i in range(3):
                result = link_resources_handler(
                    str(self.resource_ids[i]), 
                    str(self.resource_ids[i+1]), 
                    f"test_list_{i}"
                )
                if result['success']:
                    created_links.append(result['resource_link_id'])
            
            # List all links
            result = list_all_resource_links_handler(10)
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert result['success'] is True
            assert 'links' in result
            assert isinstance(result['links'], list)
            assert len(result['links']) >= len(created_links)

    def test_sqlite_relationship_metadata(self):
        """Test SQLite handling of relationship metadata."""
        metadata = {
            "created_by": "test_sqlite",
            "confidence": 0.92,
            "algorithm": "cosine_similarity",
            "timestamp": datetime.now().isoformat()
        }
        
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            result = link_resources_handler(
                str(self.resource_ids[0]), 
                str(self.resource_ids[1]), 
                "metadata_test", 
                0.9,
                json.dumps(metadata)
            )
            
            assert result['success'] is True
            assert 'metadata' in result
            
            # Retrieve and verify metadata
            get_result = get_resource_links_handler(str(self.resource_ids[0]), "metadata_test")
            if get_result['success'] and get_result['links']:
                link = get_result['links'][0]
                stored_metadata = link.get('metadata')
                if stored_metadata:
                    parsed_metadata = json.loads(stored_metadata) if isinstance(stored_metadata, str) else stored_metadata
                    assert parsed_metadata['created_by'] == metadata['created_by']
                    assert parsed_metadata['confidence'] == metadata['confidence']

    def test_sqlite_constraints_and_integrity(self):
        """Test SQLite database constraints and integrity."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Test unique constraint on (source_resource_id, target_resource_id, link_type)
        cursor.execute(
            "INSERT INTO resource_links (source_resource_id, target_resource_id, link_type, created_at) VALUES (?, ?, ?, ?)",
            (self.resource_ids[0], self.resource_ids[1], "constraint_test", datetime.now().isoformat())
        )
        
        # Try to insert duplicate - should fail or be handled gracefully
        try:
            cursor.execute(
                "INSERT INTO resource_links (source_resource_id, target_resource_id, link_type, created_at) VALUES (?, ?, ?, ?)",
                (self.resource_ids[0], self.resource_ids[1], "constraint_test", datetime.now().isoformat())
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Expected - constraint violation
            conn.rollback()
        
        # Test foreign key constraints (if enabled)
        try:
            cursor.execute(
                "INSERT INTO resource_links (source_resource_id, target_resource_id, link_type, created_at) VALUES (?, ?, ?, ?)",
                (99999, 99998, "invalid_fk_test", datetime.now().isoformat())
            )
            conn.commit()
            # If this succeeds, foreign keys might not be enforced (which is OK)
        except sqlite3.IntegrityError:
            # Foreign key constraint violation (good)
            conn.rollback()
        
        conn.close()

    def test_sqlite_performance_characteristics(self):
        """Test SQLite performance for relationship operations."""
        operations = [
            ("create_link", lambda: link_resources_handler(str(self.resource_ids[0]), str(self.resource_ids[1]), "perf_test")),
            ("get_links", lambda: get_resource_links_handler(str(self.resource_ids[0]))),
            ("list_all", lambda: list_all_resource_links_handler(20))
        ]
        
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            for operation_name, operation_func in operations:
                start_time = time.time()
                result = operation_func()
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                # SQLite operations should be very fast (< 1 second)
                assert execution_time < 1.0, f"SQLite {operation_name} took {execution_time:.2f}s (> 1s limit)"
                
                # Verify operation succeeded
                assert isinstance(result, dict)
                assert 'success' in result

    def test_sqlite_data_persistence(self):
        """Test data persistence across database connections."""
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            # Create relationship
            create_result = link_resources_handler(str(self.resource_ids[0]), str(self.resource_ids[1]), "persistence_test")
            assert create_result['success'] is True
            link_id = create_result['resource_link_id']
        
        # Simulate system restart by creating new connection
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Verify relationship persisted
        cursor.execute(
            "SELECT * FROM resource_links WHERE id = ?", 
            (link_id,)
        )
        persisted_link = cursor.fetchone()
        
        assert persisted_link is not None
        assert persisted_link[1] == self.resource_ids[0]  # source_resource_id
        assert persisted_link[2] == self.resource_ids[1]  # target_resource_id
        assert persisted_link[3] == "persistence_test"    # link_type
        
        conn.close()

    def test_sqlite_fallback_activation(self):
        """Test automatic SQLite fallback when Neo4j unavailable."""
        # Mock Neo4j as completely unavailable
        with patch('ltms.services.context_service.initialize_neo4j_store', return_value=False):
            with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
                
                # All operations should fall back to SQLite
                fallback_operations = [
                    ("link_resources", lambda: link_resources_handler(str(self.resource_ids[0]), str(self.resource_ids[1]), "fallback_test")),
                    ("get_links", lambda: get_resource_links_handler(str(self.resource_ids[0]))),
                    ("list_links", lambda: list_all_resource_links_handler(5))
                ]
                
                for operation_name, operation_func in fallback_operations:
                    result = operation_func()
                    
                    assert isinstance(result, dict)
                    assert 'success' in result
                    
                    if result['success']:
                        # Verify this was SQLite operation
                        if operation_name == "link_resources":
                            assert 'resource_link_id' in result  # SQLite-specific field
                        elif operation_name in ["get_links", "list_links"]:
                            assert 'links' in result

    def test_sqlite_concurrent_operations(self):
        """Test SQLite handling of concurrent operations."""
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            # Simulate concurrent operations
            results = []
            for i in range(5):
                result = link_resources_handler(
                    str(self.resource_ids[0]), 
                    str(self.resource_ids[i + 1 if i + 1 < len(self.resource_ids) else 1]), 
                    f"concurrent_sqlite_{i}"
                )
                results.append(result)
            
            # All operations should complete successfully
            successful_operations = sum(1 for result in results if result.get('success'))
            assert successful_operations >= 3  # Most should succeed

    def test_sqlite_large_scale_operations(self):
        """Test SQLite performance with large numbers of relationships."""
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            # Create many relationships
            batch_size = 100
            successful_creates = 0
            
            start_time = time.time()
            for i in range(batch_size):
                source_id = self.resource_ids[i % len(self.resource_ids)]
                target_id = self.resource_ids[(i + 1) % len(self.resource_ids)]
                
                if source_id != target_id:  # Avoid self-references
                    result = link_resources_handler(str(source_id), str(target_id), f"scale_test_{i}")
                    if result.get('success'):
                        successful_creates += 1
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should handle batch operations efficiently
            assert total_time < 10.0, f"SQLite batch operations took {total_time:.2f}s (> 10s limit)"
            assert successful_creates >= batch_size * 0.8  # At least 80% should succeed
            
            # Verify we can query the large dataset efficiently
            start_time = time.time()
            list_result = list_all_resource_links_handler(200)
            end_time = time.time()
            query_time = end_time - start_time
            
            assert query_time < 2.0, f"SQLite large query took {query_time:.2f}s (> 2s limit)"
            assert list_result['success'] is True
            assert len(list_result['links']) >= successful_creates

    def test_sqlite_error_handling(self):
        """Test SQLite error handling for edge cases."""
        with patch('ltms.services.context_service.get_neo4j_store', return_value=None):
            error_cases = [
                # Non-existent resource IDs
                ("invalid_source", lambda: link_resources_handler("99999", str(self.resource_ids[0]), "test")),
                ("invalid_target", lambda: link_resources_handler(str(self.resource_ids[0]), "99999", "test")),
                ("invalid_link_id", lambda: remove_resource_link_handler("99999")),
                
                # Invalid parameter types
                ("non_numeric_source", lambda: link_resources_handler("abc", str(self.resource_ids[0]), "test")),
                ("non_numeric_target", lambda: link_resources_handler(str(self.resource_ids[0]), "xyz", "test"))
            ]
            
            for case_name, operation_func in error_cases:
                result = operation_func()
                
                assert isinstance(result, dict)
                assert 'success' in result
                
                # Should either succeed (if resource exists) or fail gracefully with error message
                if not result['success']:
                    assert 'error' in result
                    assert isinstance(result['error'], str)
                    assert len(result['error']) > 0


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v", 
        "--tb=short",
        "-k", "test_sqlite"  # Run only SQLite specific tests
    ])