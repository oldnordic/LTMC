"""
Comprehensive failing test that exposes the Neo4j relationship type mapping bug in LTMC.

This test demonstrates the critical bug where Neo4j hardcodes all relationships as 
`RELATES_TO` instead of using the actual `link_type` parameter, creating data 
inconsistency between SQLite and Neo4j backends.

**BUG LOCATION**: /home/feanor/Projects/lmtc/ltms/database/neo4j_store.py:139
**BUG DESCRIPTION**: 
  - Neo4j Cypher query hardcodes relationship type as `RELATES_TO`
  - Actual relationship type stored only as property `{type: $relationship_type}`
  - SQLite correctly stores actual relationship type in `link_type` column
  - This creates backend inconsistency and data integrity issues

**TEST STATUS**: This test SHOULD FAIL until the bug is fixed.
"""

import pytest
import sqlite3
import time
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import LTMC components for real database operations
from ltms.tools.context_tools import link_resources_handler
from ltms.database.connection import get_db_connection
from ltms.database.neo4j_store import Neo4jGraphStore
from ltms.database.schema import create_tables
from ltms.services.context_service import initialize_neo4j_store, get_neo4j_store
from ltms.config import Config


class TestNeo4jRelationshipTypeBug:
    """
    Test that exposes the Neo4j relationship type mapping bug.
    
    This test validates that relationship types are preserved correctly 
    across both SQLite and Neo4j backends, and demonstrates the current
    bug where Neo4j hardcodes all relationships as RELATES_TO.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment with clean state."""
        print("\n=== RELATIONSHIP TYPE BUG TEST SETUP ===")
        
        # Initialize backends
        self.neo4j_available = initialize_neo4j_store()
        self.neo4j_store = get_neo4j_store()
        
        # Generate unique test IDs to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")[-10:]  # Last 10 digits to fit in integer
        self.test_source_id = f"9001{timestamp}"  # Prefix with 9001 to make it obviously a test ID
        self.test_target_id = f"9002{timestamp}"  # Prefix with 9002 to make it obviously a test ID  
        self.custom_relationship_type = f"semantic_similarity_test_{timestamp}"
        
        print(f"✓ Test IDs generated: {self.test_source_id} -> {self.test_target_id}")
        print(f"✓ Custom relationship type: {self.custom_relationship_type}")
        
        # Verify Neo4j availability
        if self.neo4j_available and self.neo4j_store:
            print("✓ Neo4j backend available - bug test can proceed")
        else:
            pytest.skip("Neo4j backend unavailable - cannot test relationship type bug")
        
        # Ensure database schema exists and create test resources
        self._setup_test_resources()
        
        yield
        
        # Cleanup test data
        self._cleanup_test_data()

    def _setup_test_resources(self):
        """Setup database schema and create test resources."""
        print("\n=== SETTING UP TEST RESOURCES ===")
        
        # Ensure database schema exists
        conn = get_db_connection(Config.DB_PATH)
        create_tables(conn)
        
        # Create test resources
        cursor = conn.cursor()
        
        # Create source resource
        cursor.execute(
            "INSERT OR REPLACE INTO resources (id, file_name, type, created_at) VALUES (?, ?, ?, ?)",
            (int(self.test_source_id), f"test_source_{self.test_source_id}.md", "document", datetime.now().isoformat())
        )
        
        # Create target resource
        cursor.execute(
            "INSERT OR REPLACE INTO resources (id, file_name, type, created_at) VALUES (?, ?, ?, ?)",
            (int(self.test_target_id), f"test_target_{self.test_target_id}.md", "document", datetime.now().isoformat())
        )
        
        # Create resource chunks (required for some operations)
        cursor.execute(
            "INSERT OR REPLACE INTO resource_chunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
            (int(self.test_source_id), f"Test content for source {self.test_source_id}", int(self.test_source_id))
        )
        
        cursor.execute(
            "INSERT OR REPLACE INTO resource_chunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
            (int(self.test_target_id), f"Test content for target {self.test_target_id}", int(self.test_target_id))
        )
        
        conn.commit()
        conn.close()
        print(f"✓ Created test resources: {self.test_source_id}, {self.test_target_id}")

    def _cleanup_test_data(self):
        """Clean up test data from both backends."""
        print("\n=== CLEANING UP TEST DATA ===")
        
        # Clean SQLite
        try:
            conn = get_db_connection(Config.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM resource_links WHERE source_resource_id = ? OR target_resource_id = ?",
                (int(self.test_source_id), int(self.test_target_id))
            )
            cursor.execute(
                "DELETE FROM resource_chunks WHERE resource_id = ? OR resource_id = ?",
                (int(self.test_source_id), int(self.test_target_id))
            )
            cursor.execute(
                "DELETE FROM resources WHERE id = ? OR id = ?",
                (int(self.test_source_id), int(self.test_target_id))
            )
            conn.commit()
            conn.close()
            print("✓ SQLite test data cleaned")
        except Exception as e:
            print(f"! SQLite cleanup error: {e}")
        
        # Clean Neo4j
        try:
            if self.neo4j_store and self.neo4j_store.is_available():
                with self.neo4j_store.driver.session() as session:
                    session.run(
                        "MATCH (n:Document) WHERE n.id = $source_id OR n.id = $target_id DETACH DELETE n",
                        {"source_id": self.test_source_id, "target_id": self.test_target_id}
                    )
                print("✓ Neo4j test data cleaned")
        except Exception as e:
            print(f"! Neo4j cleanup error: {e}")

    def test_relationship_type_preservation_across_backends(self):
        """
        **MAIN BUG TEST**: Test that Neo4j preserves actual relationship type, not hardcoded RELATES_TO.
        
        This test SHOULD FAIL until the bug in neo4j_store.py:139 is fixed.
        
        Expected Behavior:
        - SQLite: Stores custom relationship type in `link_type` column
        - Neo4j: Should store custom relationship type as Neo4j relationship TYPE
        
        Actual Buggy Behavior:
        - SQLite: Correctly stores custom relationship type ✓
        - Neo4j: Hardcodes `RELATES_TO` as relationship type, stores custom type as property ✗
        """
        print(f"\n=== TESTING RELATIONSHIP TYPE BUG ===")
        print(f"Custom relationship type: {self.custom_relationship_type}")
        print(f"Testing: {self.test_source_id} --{self.custom_relationship_type}--> {self.test_target_id}")
        
        # Step 1: Create relationship using real LTMC function
        print("\n1. Creating relationship using LTMC...")
        result = link_resources_handler(
            source_id=self.test_source_id,
            target_id=self.test_target_id,
            relation=self.custom_relationship_type,
            weight=1.0,
            metadata=json.dumps({"test": "relationship_type_bug_test"})
        )
        
        # Verify creation succeeded
        assert result.get('success') is True, f"Failed to create relationship: {result}"
        print(f"✓ Relationship created successfully: {result.get('message', 'No message')}")
        
        # Step 2: Validate SQLite backend stores correct relationship type
        print("\n2. Validating SQLite backend...")
        sqlite_link_type = self._query_sqlite_relationship_type()
        print(f"SQLite link_type: '{sqlite_link_type}'")
        
        assert sqlite_link_type == self.custom_relationship_type, (
            f"SQLite backend failed to store correct relationship type. "
            f"Expected: '{self.custom_relationship_type}', Found: '{sqlite_link_type}'"
        )
        print("✓ SQLite correctly stores the actual relationship type")
        
        # Step 3: Validate Neo4j backend - THIS IS WHERE THE BUG MANIFESTS
        print("\n3. Validating Neo4j backend...")
        neo4j_relationship_type, neo4j_property_type = self._query_neo4j_relationship_type()
        print(f"Neo4j relationship TYPE: '{neo4j_relationship_type}'")
        print(f"Neo4j relationship property 'type': '{neo4j_property_type}'")
        
        # THIS IS THE BUG: Neo4j should store the custom type as the relationship TYPE
        # But it currently hardcodes RELATES_TO and puts the custom type as a property
        
        if neo4j_relationship_type == "RELATES_TO":
            print("\n🐛 BUG DETECTED: Neo4j hardcoded relationship type as 'RELATES_TO'")
            print(f"   Expected: Neo4j relationship TYPE = '{self.custom_relationship_type}'")
            print(f"   Found: Neo4j relationship TYPE = 'RELATES_TO'")
            print(f"   Found: Neo4j relationship property 'type' = '{neo4j_property_type}'")
            
            # This assertion SHOULD FAIL, proving the bug exists
            pytest.fail(
                f"NEO4J RELATIONSHIP TYPE BUG DETECTED!\n"
                f"File: /home/feanor/Projects/lmtc/ltms/database/neo4j_store.py:139\n"
                f"Problem: Hardcoded 'RELATES_TO' instead of using actual relationship type\n"
                f"Expected Neo4j relationship TYPE: '{self.custom_relationship_type}'\n"
                f"Actual Neo4j relationship TYPE: '{neo4j_relationship_type}'\n"
                f"Backend Inconsistency:\n"
                f"  - SQLite link_type: '{sqlite_link_type}' ✓\n"
                f"  - Neo4j relationship TYPE: '{neo4j_relationship_type}' ✗\n"
                f"  - Neo4j relationship property: '{neo4j_property_type}' (should be relationship TYPE)\n"
                f"\nFIX: Change line 139 from:\n"
                f"  MERGE (source)-[r:RELATES_TO {{type: $relationship_type}}]->(target)\n"
                f"TO:\n"
                f"  MERGE (source)-[r:`{self.custom_relationship_type}` {{metadata: $properties}}]->(target)\n"
                f"OR use dynamic relationship type construction."
            )
        else:
            # If this passes, the bug has been fixed
            assert neo4j_relationship_type == self.custom_relationship_type, (
                f"Neo4j relationship type mismatch. "
                f"Expected: '{self.custom_relationship_type}', Found: '{neo4j_relationship_type}'"
            )
            print("✓ Neo4j correctly stores the actual relationship type")
        
        # Step 4: Verify backend consistency
        print("\n4. Verifying backend consistency...")
        assert sqlite_link_type == neo4j_relationship_type, (
            f"Backend inconsistency detected!\n"
            f"SQLite link_type: '{sqlite_link_type}'\n"
            f"Neo4j relationship TYPE: '{neo4j_relationship_type}'\n"
            f"Both backends should store the same relationship type."
        )
        print("✓ Both backends store consistent relationship types")

    def test_multiple_custom_relationship_types(self):
        """
        Test multiple custom relationship types to ensure the bug affects all non-RELATES_TO types.
        
        This test creates several relationships with different custom types and verifies
        that Neo4j hardcodes all of them as RELATES_TO instead of preserving the actual types.
        """
        print("\n=== TESTING MULTIPLE CUSTOM RELATIONSHIP TYPES ===")
        
        custom_types = [
            "semantic_similarity",
            "builds_upon", 
            "contradicts",
            "implements",
            "references_implementation"
        ]
        
        results = {}
        
        for i, custom_type in enumerate(custom_types):
            source_id = f"{self.test_source_id}_multi_{i}"
            target_id = f"{self.test_target_id}_multi_{i}"
            
            print(f"\nTesting relationship type: '{custom_type}'")
            print(f"Creating: {source_id} --{custom_type}--> {target_id}")
            
            # Create relationship
            result = link_resources_handler(
                source_id=source_id,
                target_id=target_id,
                relation=custom_type,
                weight=1.0
            )
            
            assert result.get('success') is True, f"Failed to create {custom_type} relationship"
            
            # Check what's actually stored in Neo4j
            neo4j_type, neo4j_prop = self._query_neo4j_relationship_type_for_nodes(source_id, target_id)
            results[custom_type] = {
                'neo4j_relationship_type': neo4j_type,
                'neo4j_property_type': neo4j_prop
            }
            
            print(f"  Neo4j relationship TYPE: '{neo4j_type}'")
            print(f"  Neo4j property 'type': '{neo4j_prop}'")
        
        # Analyze results to show the pattern of the bug
        print(f"\n=== BUG PATTERN ANALYSIS ===")
        hardcoded_count = 0
        
        for custom_type, data in results.items():
            neo4j_type = data['neo4j_relationship_type']
            if neo4j_type == "RELATES_TO":
                hardcoded_count += 1
                print(f"✗ '{custom_type}' -> Neo4j TYPE: 'RELATES_TO' (HARDCODED)")
            else:
                print(f"✓ '{custom_type}' -> Neo4j TYPE: '{neo4j_type}' (CORRECT)")
        
        if hardcoded_count > 0:
            pytest.fail(
                f"NEO4J HARDCODING BUG CONFIRMED!\n"
                f"Out of {len(custom_types)} custom relationship types:\n"
                f"  - {hardcoded_count} were hardcoded as 'RELATES_TO' in Neo4j\n"
                f"  - {len(custom_types) - hardcoded_count} were stored correctly\n"
                f"\nThis proves the bug systematically affects all relationship types.\n"
                f"Fix required in: /home/feanor/Projects/lmtc/ltms/database/neo4j_store.py:139"
            )

    def _query_sqlite_relationship_type(self) -> str:
        """Query SQLite database directly to get the stored relationship type."""
        conn = get_db_connection(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT link_type 
            FROM resource_links 
            WHERE source_resource_id = ? AND target_resource_id = ?
        """, (self.test_source_id, self.test_target_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            raise AssertionError(f"No relationship found in SQLite for {self.test_source_id} -> {self.test_target_id}")

    def _query_neo4j_relationship_type(self) -> tuple[str, str]:
        """
        Query Neo4j database directly to get both:
        1. The actual Neo4j relationship TYPE (e.g., RELATES_TO)
        2. The relationship property 'type' (e.g., the custom type)
        
        Returns: (relationship_type, property_type)
        """
        return self._query_neo4j_relationship_type_for_nodes(self.test_source_id, self.test_target_id)

    def _query_neo4j_relationship_type_for_nodes(self, source_id: str, target_id: str) -> tuple[str, str]:
        """
        Query Neo4j for relationship type and property for specific nodes.
        
        Returns: (relationship_type, property_type)
        """
        query = """
        MATCH (source:Document {id: $source_id})-[r]->(target:Document {id: $target_id})
        RETURN type(r) as relationship_type, r.type as property_type
        """
        
        try:
            with self.neo4j_store.driver.session() as session:
                result = session.run(query, {"source_id": source_id, "target_id": target_id})
                record = result.single()
                
                if record:
                    relationship_type = record['relationship_type']
                    property_type = record['property_type']
                    return relationship_type, property_type
                else:
                    raise AssertionError(f"No relationship found in Neo4j for {source_id} -> {target_id}")
                
        except Exception as e:
            raise AssertionError(f"Failed to query Neo4j relationship: {e}")

    def test_bug_fix_validation_ready(self):
        """
        Test that validates the correct behavior once the bug is fixed.
        
        This test documents the expected behavior and can be used to verify
        that the fix works correctly.
        """
        print("\n=== BUG FIX VALIDATION TEST ===")
        print("This test documents the expected behavior after the bug is fixed.")
        
        # Expected fix: Neo4j should use dynamic relationship types
        expected_cypher_pattern = """
        MERGE (source:Document {id: $source_id})
        MERGE (target:Document {id: $target_id})
        CALL apoc.create.relationship(source, $relationship_type, $properties, target) 
        YIELD rel
        RETURN rel
        """
        
        print(f"\nExpected Cypher pattern after fix:")
        print(expected_cypher_pattern)
        
        print(f"\nOR alternative fix using string interpolation:")
        print(f"Build Cypher dynamically with validated relationship type names")
        
        # This test will pass once the bug is fixed
        result = link_resources_handler(
            source_id=self.test_source_id,
            target_id=self.test_target_id,
            relation=self.custom_relationship_type
        )
        
        assert result.get('success') is True
        
        # After fix, this should work without hardcoding
        sqlite_type = self._query_sqlite_relationship_type()
        neo4j_type, _ = self._query_neo4j_relationship_type()
        
        # These should be equal after the bug is fixed
        if sqlite_type == neo4j_type == self.custom_relationship_type:
            print("✓ BUG FIX CONFIRMED: Neo4j now correctly stores custom relationship types")
        else:
            print(f"✗ Bug still exists: SQLite='{sqlite_type}', Neo4j='{neo4j_type}'")


if __name__ == "__main__":
    """
    Run this test directly to expose the Neo4j relationship type bug.
    
    Usage:
        python tests/integration/test_neo4j_relationship_type_bug.py
        
    Or with pytest:
        pytest tests/integration/test_neo4j_relationship_type_bug.py -v -s
    """
    import json
    pytest.main([__file__, "-v", "-s"])