"""
Comprehensive failing test that exposes property synchronization bugs between SQLite and Neo4j backends in LTMC.

This test validates that all relationship properties are synchronized correctly between
SQLite and Neo4j backends, focusing on the reported issues where Neo4j relationships 
sometimes have NULL resource_id properties while SQLite contains complete data.

**EXPECTED FAILURES**:
1. Neo4j relationships with NULL resource_id properties when SQLite has valid IDs
2. Metadata not properly synchronized between backends  
3. Weight values lost or incorrectly stored in Neo4j
4. Timestamp inconsistencies between backends
5. Property completeness issues (missing properties in Neo4j)

**TEST STATUS**: This test SHOULD FAIL until property synchronization bugs are fixed.
"""

import pytest
import sqlite3
import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

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


class TestPropertySynchronizationBug:
    """
    Test that exposes property synchronization bugs between SQLite and Neo4j backends.
    
    This test validates that all relationship properties (resource_id, weight, metadata, 
    timestamps) are preserved identically across both backends, and demonstrates 
    current bugs where properties are missing or inconsistent in Neo4j.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment with clean state."""
        print("\n=== PROPERTY SYNCHRONIZATION BUG TEST SETUP ===")
        
        # Initialize backends
        self.neo4j_available = initialize_neo4j_store()
        self.neo4j_store = get_neo4j_store()
        
        # Generate unique test IDs to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")[-10:]
        self.test_source_id = f"8001{timestamp}"
        self.test_target_id = f"8002{timestamp}"
        self.test_relation = f"property_sync_test_{timestamp}"
        
        # Comprehensive test properties that should be synchronized
        self.test_weight = 0.85
        self.test_metadata = json.dumps({
            "similarity_score": 0.92,
            "algorithm": "cosine",
            "custom_field": "property_sync_test_2025",
            "nested_data": {
                "confidence": 0.88,
                "source": "automated_test"
            }
        })
        
        print(f"✓ Test IDs: {self.test_source_id} -> {self.test_target_id}")
        print(f"✓ Relation: {self.test_relation}")
        print(f"✓ Weight: {self.test_weight}")
        print(f"✓ Metadata: {self.test_metadata}")
        
        # Verify Neo4j availability
        if self.neo4j_available and self.neo4j_store:
            print("✓ Neo4j backend available - property synchronization test can proceed")
        else:
            pytest.skip("Neo4j backend unavailable - cannot test property synchronization")
        
        # Setup test resources
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
        
        # Create test resources with rich metadata
        cursor = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        # Create source resource
        cursor.execute(
            "INSERT OR REPLACE INTO resources (id, file_name, type, created_at) VALUES (?, ?, ?, ?)",
            (int(self.test_source_id), f"property_test_source_{self.test_source_id}.md", "document", current_time)
        )
        
        # Create target resource
        cursor.execute(
            "INSERT OR REPLACE INTO resources (id, file_name, type, created_at) VALUES (?, ?, ?, ?)",
            (int(self.test_target_id), f"property_test_target_{self.test_target_id}.md", "document", current_time)
        )
        
        # Create resource chunks (required for some operations)
        cursor.execute(
            "INSERT OR REPLACE INTO resource_chunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
            (int(self.test_source_id), f"Property sync test content for source {self.test_source_id}", int(self.test_source_id))
        )
        
        cursor.execute(
            "INSERT OR REPLACE INTO resource_chunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
            (int(self.test_target_id), f"Property sync test content for target {self.test_target_id}", int(self.test_target_id))
        )
        
        conn.commit()
        conn.close()
        print(f"✓ Created test resources with comprehensive metadata")

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

    def test_comprehensive_property_synchronization_across_backends(self):
        """
        **MAIN PROPERTY SYNCHRONIZATION BUG TEST**: 
        Test that all properties are synchronized identically between SQLite and Neo4j.
        
        This test SHOULD FAIL if property synchronization is incomplete.
        
        Expected Properties to be Synchronized:
        1. resource_id values on Neo4j nodes (not NULL)
        2. weight values identical in both backends
        3. metadata JSON preserved identically
        4. created_at timestamps consistent (within reasonable tolerance)
        5. All relationship properties complete and non-NULL
        """
        print(f"\n=== TESTING COMPREHENSIVE PROPERTY SYNCHRONIZATION ===")
        print(f"Creating relationship with comprehensive properties:")
        print(f"  {self.test_source_id} --[{self.test_relation}]--> {self.test_target_id}")
        print(f"  Weight: {self.test_weight}")
        print(f"  Metadata: {self.test_metadata}")
        
        # Record creation time for timestamp validation
        creation_time_start = datetime.now()
        
        # Step 1: Create relationship using real LTMC function
        print("\n1. Creating relationship using LTMC...")
        result = link_resources_handler(
            source_id=self.test_source_id,
            target_id=self.test_target_id,
            relation=self.test_relation,
            weight=self.test_weight,
            metadata=self.test_metadata
        )
        
        creation_time_end = datetime.now()
        
        # Verify creation succeeded
        assert result.get('success') is True, f"Failed to create relationship: {result}"
        print(f"✓ Relationship created successfully: {result.get('message', 'No message')}")
        
        # Step 2: Validate SQLite backend properties
        print("\n2. Validating SQLite backend properties...")
        sqlite_properties = self._query_sqlite_properties()
        print("SQLite Properties:")
        for key, value in sqlite_properties.items():
            print(f"  {key}: {value}")
        
        # Validate SQLite has all expected properties
        assert sqlite_properties['source_resource_id'] == int(self.test_source_id), "SQLite missing source_resource_id"
        assert sqlite_properties['target_resource_id'] == int(self.test_target_id), "SQLite missing target_resource_id"
        assert sqlite_properties['link_type'] == self.test_relation, "SQLite incorrect link_type"
        assert sqlite_properties['weight'] == self.test_weight, "SQLite incorrect weight"
        assert sqlite_properties['metadata'] == self.test_metadata, "SQLite incorrect metadata"
        assert sqlite_properties['created_at'] is not None, "SQLite missing created_at"
        
        print("✓ SQLite contains all expected properties correctly")
        
        # Step 3: Validate Neo4j backend properties - THIS IS WHERE BUGS MANIFEST
        print("\n3. Validating Neo4j backend properties...")
        neo4j_node_properties, neo4j_rel_properties = self._query_neo4j_properties()
        
        print("Neo4j Node Properties:")
        for node_type, props in neo4j_node_properties.items():
            print(f"  {node_type}: {props}")
        
        print("Neo4j Relationship Properties:")
        for key, value in neo4j_rel_properties.items():
            print(f"  {key}: {value}")
        
        # Step 4: Validate Neo4j Node Resource ID Properties - CRITICAL BUG CHECK
        print("\n4. Checking Neo4j node resource_id properties...")
        
        source_node_props = neo4j_node_properties.get('source', {})
        target_node_props = neo4j_node_properties.get('target', {})
        
        source_resource_id = source_node_props.get('resource_id')
        target_resource_id = target_node_props.get('resource_id')
        
        print(f"Source Node resource_id: {source_resource_id}")
        print(f"Target Node resource_id: {target_resource_id}")
        
        # THIS IS THE CRITICAL BUG: Neo4j nodes should have resource_id properties
        if source_resource_id is None:
            print("🐛 BUG DETECTED: Source node has NULL resource_id in Neo4j")
            pytest.fail(
                f"NEO4J NODE RESOURCE_ID BUG DETECTED!\n"
                f"Source node resource_id: {source_resource_id} (should be {self.test_source_id})\n"
                f"Target node resource_id: {target_resource_id} (should be {self.test_target_id})\n"
                f"SQLite has complete resource IDs but Neo4j nodes have NULL resource_id properties"
            )
        
        if target_resource_id is None:
            print("🐛 BUG DETECTED: Target node has NULL resource_id in Neo4j")
            pytest.fail(
                f"NEO4J NODE RESOURCE_ID BUG DETECTED!\n"
                f"Source node resource_id: {source_resource_id} (should be {self.test_source_id})\n"
                f"Target node resource_id: {target_resource_id} (should be {self.test_target_id})\n"
                f"SQLite has complete resource IDs but Neo4j nodes have NULL resource_id properties"
            )
        
        # Verify resource_id consistency
        assert int(source_resource_id) == int(self.test_source_id), f"Neo4j source resource_id mismatch: {source_resource_id} != {self.test_source_id}"
        assert int(target_resource_id) == int(self.test_target_id), f"Neo4j target resource_id mismatch: {target_resource_id} != {self.test_target_id}"
        
        print("✓ Neo4j nodes have correct resource_id properties")
        
        # Step 5: Validate Neo4j Relationship Properties
        print("\n5. Checking Neo4j relationship properties...")
        
        neo4j_weight = neo4j_rel_properties.get('weight')
        neo4j_metadata = neo4j_rel_properties.get('metadata')
        neo4j_created_at = neo4j_rel_properties.get('created_at')
        
        # Weight synchronization check
        if neo4j_weight != self.test_weight:
            print(f"🐛 BUG DETECTED: Weight mismatch between backends")
            pytest.fail(
                f"WEIGHT SYNCHRONIZATION BUG DETECTED!\n"
                f"SQLite weight: {sqlite_properties['weight']}\n"
                f"Neo4j weight: {neo4j_weight}\n"
                f"Expected: {self.test_weight}\n"
                f"Weight values must be identical between backends"
            )
        
        # Metadata synchronization check
        if neo4j_metadata != self.test_metadata:
            print(f"🐛 BUG DETECTED: Metadata mismatch between backends")
            pytest.fail(
                f"METADATA SYNCHRONIZATION BUG DETECTED!\n"
                f"SQLite metadata: {sqlite_properties['metadata']}\n"
                f"Neo4j metadata: {neo4j_metadata}\n"
                f"Expected: {self.test_metadata}\n"
                f"Metadata must be identical between backends"
            )
        
        # Timestamp synchronization check (allow reasonable tolerance)
        if neo4j_created_at is None:
            print(f"🐛 BUG DETECTED: Missing created_at timestamp in Neo4j")
            pytest.fail(
                f"TIMESTAMP SYNCHRONIZATION BUG DETECTED!\n"
                f"SQLite created_at: {sqlite_properties['created_at']}\n"
                f"Neo4j created_at: {neo4j_created_at}\n"
                f"Neo4j relationship missing created_at timestamp"
            )
        
        # Parse timestamps for comparison
        try:
            sqlite_time = datetime.fromisoformat(sqlite_properties['created_at'].replace('Z', '+00:00'))
            neo4j_time = datetime.fromisoformat(neo4j_created_at.replace('Z', '+00:00'))
            time_diff = abs((sqlite_time - neo4j_time).total_seconds())
            
            # Allow 10 second tolerance for timestamp differences
            if time_diff > 10:
                print(f"🐛 BUG DETECTED: Timestamp difference too large between backends")
                pytest.fail(
                    f"TIMESTAMP SYNCHRONIZATION BUG DETECTED!\n"
                    f"SQLite created_at: {sqlite_properties['created_at']}\n"
                    f"Neo4j created_at: {neo4j_created_at}\n"
                    f"Time difference: {time_diff} seconds (max allowed: 10)\n"
                    f"Timestamps should be nearly identical between backends"
                )
        except Exception as e:
            pytest.fail(f"Failed to parse timestamps for comparison: {e}")
        
        print("✓ Neo4j relationship properties are correctly synchronized")
        
        # Step 6: Comprehensive Backend Consistency Validation
        print("\n6. Verifying comprehensive backend consistency...")
        
        # All properties must be identical between backends
        consistency_errors = []
        
        if int(source_resource_id) != sqlite_properties['source_resource_id']:
            consistency_errors.append(f"Source resource_id: Neo4j={source_resource_id}, SQLite={sqlite_properties['source_resource_id']}")
        
        if int(target_resource_id) != sqlite_properties['target_resource_id']:
            consistency_errors.append(f"Target resource_id: Neo4j={target_resource_id}, SQLite={sqlite_properties['target_resource_id']}")
        
        if neo4j_weight != sqlite_properties['weight']:
            consistency_errors.append(f"Weight: Neo4j={neo4j_weight}, SQLite={sqlite_properties['weight']}")
        
        if neo4j_metadata != sqlite_properties['metadata']:
            consistency_errors.append(f"Metadata: Neo4j={neo4j_metadata[:100]}..., SQLite={sqlite_properties['metadata'][:100]}...")
        
        if consistency_errors:
            pytest.fail(
                f"BACKEND CONSISTENCY BUGS DETECTED!\n"
                f"Property mismatches between SQLite and Neo4j:\n" +
                "\n".join(f"  - {error}" for error in consistency_errors) +
                f"\n\nBoth backends must store identical property values."
            )
        
        print("✓ All properties are consistent between SQLite and Neo4j backends")

    def test_multiple_relationships_property_synchronization(self):
        """
        Test property synchronization across multiple relationships with different property sets.
        
        This test creates several relationships with varying properties to ensure
        the property synchronization bugs affect all relationships consistently.
        """
        print("\n=== TESTING MULTIPLE RELATIONSHIPS PROPERTY SYNCHRONIZATION ===")
        
        test_cases = [
            {
                "relation": "semantic_similarity",
                "weight": 0.95,
                "metadata": json.dumps({"algorithm": "bert", "score": 0.95})
            },
            {
                "relation": "builds_upon",
                "weight": 0.75,
                "metadata": json.dumps({"dependency_type": "implementation", "confidence": 0.8})
            },
            {
                "relation": "contradicts",
                "weight": 0.60,
                "metadata": json.dumps({"conflict_level": "high", "resolution": "manual_review"})
            }
        ]
        
        sync_failures = []
        
        # Create additional test resources for multiple relationships
        conn = get_db_connection(Config.DB_PATH)
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        
        for i, test_case in enumerate(test_cases):
            # Generate unique integer IDs for each test relationship
            source_id = int(f"{self.test_source_id}{i}")
            target_id = int(f"{self.test_target_id}{i}")
            
            # Create resources for this test case
            cursor.execute(
                "INSERT OR REPLACE INTO resources (id, file_name, type, created_at) VALUES (?, ?, ?, ?)",
                (source_id, f"multi_test_source_{source_id}.md", "document", current_time)
            )
            cursor.execute(
                "INSERT OR REPLACE INTO resources (id, file_name, type, created_at) VALUES (?, ?, ?, ?)",
                (target_id, f"multi_test_target_{target_id}.md", "document", current_time)
            )
            cursor.execute(
                "INSERT OR REPLACE INTO resource_chunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
                (source_id, f"Multi test content for source {source_id}", source_id)
            )
            cursor.execute(
                "INSERT OR REPLACE INTO resource_chunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
                (target_id, f"Multi test content for target {target_id}", target_id)
            )
            
            print(f"\nTesting relationship {i+1}: {test_case['relation']}")
            print(f"  IDs: {source_id} -> {target_id}")
            
            # Create relationship
            result = link_resources_handler(
                source_id=str(source_id),
                target_id=str(target_id),
                relation=test_case['relation'],
                weight=test_case['weight'],
                metadata=test_case['metadata']
            )
            
            assert result.get('success') is True, f"Failed to create relationship {i+1}: {result}"
            
            # Check property synchronization for this relationship
            sqlite_props = self._query_sqlite_properties_for_nodes(source_id, target_id)
            neo4j_node_props, neo4j_rel_props = self._query_neo4j_properties_for_nodes(str(source_id), str(target_id))
            
            # Check for synchronization issues
            issues = []
            
            if neo4j_node_props['source'].get('resource_id') is None:
                issues.append("Source node missing resource_id")
            
            if neo4j_node_props['target'].get('resource_id') is None:
                issues.append("Target node missing resource_id")
            
            if neo4j_rel_props.get('weight') != test_case['weight']:
                issues.append(f"Weight mismatch: Neo4j={neo4j_rel_props.get('weight')}, Expected={test_case['weight']}")
            
            if neo4j_rel_props.get('metadata') != test_case['metadata']:
                issues.append(f"Metadata mismatch")
            
            if issues:
                sync_failures.append({
                    'relationship': test_case['relation'],
                    'issues': issues
                })
        
        # Close database connection
        conn.commit()
        conn.close()
        
        # Report all synchronization failures
        if sync_failures:
            failure_report = "\n".join([
                f"  {failure['relationship']}: {', '.join(failure['issues'])}"
                for failure in sync_failures
            ])
            
            pytest.fail(
                f"MULTIPLE RELATIONSHIP PROPERTY SYNCHRONIZATION BUGS DETECTED!\n"
                f"Out of {len(test_cases)} relationships, {len(sync_failures)} had property sync issues:\n"
                f"{failure_report}\n"
                f"\nThis indicates systematic property synchronization problems between backends."
            )

    def _query_sqlite_properties(self) -> Dict[str, Any]:
        """Query SQLite database directly to get all stored relationship properties."""
        return self._query_sqlite_properties_for_nodes(int(self.test_source_id), int(self.test_target_id))

    def _query_sqlite_properties_for_nodes(self, source_id: int, target_id: int) -> Dict[str, Any]:
        """Query SQLite for relationship properties between specific nodes."""
        conn = get_db_connection(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT source_resource_id, target_resource_id, link_type, weight, metadata, created_at
            FROM resource_links 
            WHERE source_resource_id = ? AND target_resource_id = ?
        """, (source_id, target_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'source_resource_id': result[0],
                'target_resource_id': result[1],
                'link_type': result[2],
                'weight': result[3],
                'metadata': result[4],
                'created_at': result[5]
            }
        else:
            raise AssertionError(f"No relationship found in SQLite for {source_id} -> {target_id}")

    def _query_neo4j_properties(self) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """
        Query Neo4j database directly to get both node and relationship properties.
        
        Returns:
            Tuple of (node_properties, relationship_properties)
        """
        return self._query_neo4j_properties_for_nodes(self.test_source_id, self.test_target_id)

    def _query_neo4j_properties_for_nodes(self, source_id: str, target_id: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """
        Query Neo4j for both node and relationship properties between specific nodes.
        
        Returns:
            Tuple of (node_properties, relationship_properties)
        """
        node_query = """
        MATCH (source:Document {id: $source_id})-[r]->(target:Document {id: $target_id})
        RETURN source, target, r
        """
        
        try:
            with self.neo4j_store.driver.session() as session:
                result = session.run(node_query, {"source_id": source_id, "target_id": target_id})
                record = result.single()
                
                if record:
                    source_node = record['source']
                    target_node = record['target']
                    relationship = record['r']
                    
                    node_properties = {
                        'source': dict(source_node),
                        'target': dict(target_node)
                    }
                    
                    relationship_properties = dict(relationship)
                    
                    return node_properties, relationship_properties
                else:
                    raise AssertionError(f"No relationship found in Neo4j for {source_id} -> {target_id}")
                
        except Exception as e:
            raise AssertionError(f"Failed to query Neo4j properties: {e}")

    def test_property_completeness_validation(self):
        """
        Test that validates all expected properties exist and are non-NULL in both backends.
        
        This test documents the complete property set that should be synchronized
        and can detect missing or NULL properties.
        """
        print("\n=== PROPERTY COMPLETENESS VALIDATION ===")
        
        # Create relationship with all possible properties
        result = link_resources_handler(
            source_id=self.test_source_id,
            target_id=self.test_target_id,
            relation=self.test_relation,
            weight=self.test_weight,
            metadata=self.test_metadata
        )
        
        assert result.get('success') is True
        
        # Define expected properties for each backend
        expected_sqlite_properties = {
            'source_resource_id': int,
            'target_resource_id': int,
            'link_type': str,
            'weight': float,
            'metadata': str,
            'created_at': str
        }
        
        expected_neo4j_node_properties = {
            'id': str,
            'file_name': str,
            'resource_type': str,
            'resource_id': int  # Critical property that's often NULL
        }
        
        expected_neo4j_rel_properties = {
            'weight': float,
            'metadata': str,
            'created_at': str,
            'type': str,
            'original_type': str
        }
        
        # Validate SQLite property completeness
        sqlite_props = self._query_sqlite_properties()
        sqlite_missing = []
        
        for prop_name, prop_type in expected_sqlite_properties.items():
            if prop_name not in sqlite_props:
                sqlite_missing.append(f"{prop_name} (missing)")
            elif sqlite_props[prop_name] is None:
                sqlite_missing.append(f"{prop_name} (NULL)")
            elif not isinstance(sqlite_props[prop_name], prop_type):
                sqlite_missing.append(f"{prop_name} (wrong type: {type(sqlite_props[prop_name]).__name__})")
        
        # Validate Neo4j property completeness
        neo4j_nodes, neo4j_rel = self._query_neo4j_properties()
        neo4j_missing = []
        
        # Check source node properties
        for prop_name, prop_type in expected_neo4j_node_properties.items():
            source_value = neo4j_nodes['source'].get(prop_name)
            if source_value is None:
                neo4j_missing.append(f"source.{prop_name} (NULL)")
            elif not isinstance(source_value, prop_type):
                neo4j_missing.append(f"source.{prop_name} (wrong type)")
        
        # Check target node properties
        for prop_name, prop_type in expected_neo4j_node_properties.items():
            target_value = neo4j_nodes['target'].get(prop_name)
            if target_value is None:
                neo4j_missing.append(f"target.{prop_name} (NULL)")
            elif not isinstance(target_value, prop_type):
                neo4j_missing.append(f"target.{prop_name} (wrong type)")
        
        # Check relationship properties
        for prop_name, prop_type in expected_neo4j_rel_properties.items():
            rel_value = neo4j_rel.get(prop_name)
            if rel_value is None:
                neo4j_missing.append(f"relationship.{prop_name} (NULL)")
            elif not isinstance(rel_value, prop_type):
                neo4j_missing.append(f"relationship.{prop_name} (wrong type)")
        
        # Report property completeness issues
        completeness_issues = []
        
        if sqlite_missing:
            completeness_issues.extend([f"SQLite: {issue}" for issue in sqlite_missing])
        
        if neo4j_missing:
            completeness_issues.extend([f"Neo4j: {issue}" for issue in neo4j_missing])
        
        if completeness_issues:
            pytest.fail(
                f"PROPERTY COMPLETENESS BUGS DETECTED!\n"
                f"Missing or invalid properties found:\n" +
                "\n".join(f"  - {issue}" for issue in completeness_issues) +
                f"\n\nAll expected properties must be present and non-NULL in both backends."
            )
        
        print("✓ All expected properties are complete and correctly typed in both backends")


if __name__ == "__main__":
    """
    Run this test directly to expose property synchronization bugs.
    
    Usage:
        python tests/integration/test_property_synchronization_bug.py
        
    Or with pytest:
        pytest tests/integration/test_property_synchronization_bug.py -v -s
    """
    import json
    pytest.main([__file__, "-v", "-s"])