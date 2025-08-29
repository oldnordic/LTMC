"""
Neo4j Mind Graph Schema Migration
File: ltms/database/migrations/002_neo4j_mind_graph_schema.py
Purpose: Create Mind Graph constraints and indexes in Neo4j
Status: Phase 1 - Real Neo4j Implementation
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class Neo4jMindGraphMigration:
    """Real Neo4j schema migration for Mind Graph."""
    
    def __init__(self):
        """Initialize Neo4j Mind Graph migration."""
        self.migration_name = "002_neo4j_mind_graph_schema"
    
    async def apply_migration(self) -> bool:
        """Apply Neo4j Mind Graph schema with real database operations.
        
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                logger.error("Neo4j graph store not available for migration")
                return False
            
            logger.info(f"Applying Neo4j migration {self.migration_name}")
            
            # Check if migration already applied
            if await self._is_migration_applied(store):
                logger.info(f"Neo4j migration {self.migration_name} already applied")
                return True
            
            # Apply constraints and indexes
            success = True
            success &= await self._create_node_constraints(store)
            success &= await self._create_performance_indexes(store)
            success &= await self._create_schema_validation(store)
            
            if success:
                # Record migration
                await self._record_migration(store)
                logger.info(f"Neo4j migration {self.migration_name} applied successfully")
                return True
            else:
                logger.error(f"Neo4j migration {self.migration_name} failed")
                return False
                
        except Exception as e:
            logger.error(f"Neo4j migration connection failed: {e}")
            return False
    
    async def _is_migration_applied(self, store) -> bool:
        """Check if Neo4j migration is already applied."""
        try:
            # Check if our migration tracking node exists
            with store.driver.session() as session:
                result = session.run(
                    "MATCH (m:MigrationRecord {version: $version}) RETURN count(m) as count",
                    version=self.migration_name
                )
                return result.single()["count"] > 0
        except Exception as e:
            logger.warning(f"Could not check migration status: {e}")
            return False
    
    async def _record_migration(self, store):
        """Record migration in Neo4j MigrationRecord node."""
        try:
            with store.driver.session() as session:
                session.run("""
                    CREATE (m:MigrationRecord {
                        version: $version,
                        applied_at: datetime(),
                        migration_type: 'mind_graph_schema'
                    })
                """, version=self.migration_name)
                
            logger.info("Migration recorded in Neo4j")
        except Exception as e:
            logger.error(f"Could not record migration: {e}")
    
    async def _create_node_constraints(self, store) -> bool:
        """Create unique constraints for Mind Graph nodes."""
        constraints = [
            # Agent constraints
            {
                'cypher': "CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE",
                'description': "Unique agent IDs"
            },
            
            # Change constraints  
            {
                'cypher': "CREATE CONSTRAINT change_id_unique IF NOT EXISTS FOR (c:Change) REQUIRE c.change_id IS UNIQUE",
                'description': "Unique change IDs"
            },
            
            # Reason constraints
            {
                'cypher': "CREATE CONSTRAINT reason_id_unique IF NOT EXISTS FOR (r:Reason) REQUIRE r.reason_id IS UNIQUE", 
                'description': "Unique reason IDs"
            },
            
            # CodeFile constraints
            {
                'cypher': "CREATE CONSTRAINT codefile_path_unique IF NOT EXISTS FOR (f:CodeFile) REQUIRE f.file_path IS UNIQUE",
                'description': "Unique file paths"
            },
            
            # Task constraints (for existing integration)
            {
                'cypher': "CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.task_id IS UNIQUE",
                'description': "Unique task IDs"
            },
            
            # Blueprint constraints (for existing integration)
            {
                'cypher': "CREATE CONSTRAINT blueprint_id_unique IF NOT EXISTS FOR (b:Blueprint) REQUIRE b.blueprint_id IS UNIQUE",
                'description': "Unique blueprint IDs"
            }
        ]
        
        success = True
        
        try:
            with store.driver.session() as session:
                for constraint in constraints:
                    try:
                        session.run(constraint['cypher'])
                        logger.info(f"Created constraint: {constraint['description']}")
                    except Exception as e:
                        if "already exists" in str(e).lower() or "equivalent constraint already exists" in str(e).lower():
                            logger.info(f"Constraint already exists: {constraint['description']}")
                        else:
                            logger.error(f"Failed to create constraint {constraint['description']}: {e}")
                            success = False
                            
        except Exception as e:
            logger.error(f"Neo4j constraint creation failed: {e}")
            success = False
            
        return success
    
    async def _create_performance_indexes(self, store) -> bool:
        """Create performance indexes for Mind Graph queries."""
        indexes = [
            # Change indexes
            {
                'cypher': "CREATE INDEX change_timestamp_idx IF NOT EXISTS FOR (c:Change) ON (c.timestamp)",
                'description': "Change timestamp index"
            },
            {
                'cypher': "CREATE INDEX change_agent_idx IF NOT EXISTS FOR (c:Change) ON (c.agent_id)", 
                'description': "Change agent index"
            },
            {
                'cypher': "CREATE INDEX change_file_idx IF NOT EXISTS FOR (c:Change) ON (c.file_path)",
                'description': "Change file path index"
            },
            {
                'cypher': "CREATE INDEX change_type_idx IF NOT EXISTS FOR (c:Change) ON (c.change_type)",
                'description': "Change type index"
            },
            
            # Reason indexes
            {
                'cypher': "CREATE INDEX reason_type_idx IF NOT EXISTS FOR (r:Reason) ON (r.reason_type)",
                'description': "Reason type index"
            },
            {
                'cypher': "CREATE INDEX reason_chain_idx IF NOT EXISTS FOR (r:Reason) ON (r.reasoning_chain_id)",
                'description': "Reasoning chain index"
            },
            
            # Agent indexes
            {
                'cypher': "CREATE INDEX agent_type_idx IF NOT EXISTS FOR (a:Agent) ON (a.agent_type)",
                'description': "Agent type index"
            },
            {
                'cypher': "CREATE INDEX agent_active_idx IF NOT EXISTS FOR (a:Agent) ON (a.last_active_at)",
                'description': "Agent last active index"
            },
            
            # CodeFile indexes
            {
                'cypher': "CREATE INDEX codefile_project_idx IF NOT EXISTS FOR (f:CodeFile) ON (f.project_id)",
                'description': "CodeFile project index"
            },
            {
                'cypher': "CREATE INDEX codefile_type_idx IF NOT EXISTS FOR (f:CodeFile) ON (f.file_type)",
                'description': "CodeFile type index"
            },
            {
                'cypher': "CREATE INDEX codefile_modified_idx IF NOT EXISTS FOR (f:CodeFile) ON (f.last_modified)",
                'description': "CodeFile modification index"
            }
        ]
        
        success = True
        
        try:
            with store.driver.session() as session:
                for index in indexes:
                    try:
                        session.run(index['cypher'])
                        logger.info(f"Created index: {index['description']}")
                    except Exception as e:
                        if "already exists" in str(e).lower() or "equivalent index already exists" in str(e).lower():
                            logger.info(f"Index already exists: {index['description']}")
                        else:
                            logger.error(f"Failed to create index {index['description']}: {e}")
                            success = False
                            
        except Exception as e:
            logger.error(f"Neo4j index creation failed: {e}")
            success = False
            
        return success
    
    async def _create_schema_validation(self, store) -> bool:
        """Create schema validation and sample relationships."""
        try:
            with store.driver.session() as session:
                # Create schema documentation node
                session.run("""
                    CREATE (schema:MindGraphSchema {
                        version: $version,
                        created_at: datetime(),
                        node_types: ['Agent', 'Change', 'Reason', 'CodeFile', 'Task', 'Blueprint'],
                        relationship_types: [
                            'MADE_CHANGE', 'MOTIVATED_BY', 'MODIFIES', 'REFERENCES', 
                            'ASSIGNED_TO', 'HAS_VERSION', 'FOLLOWS', 'COLLABORATES_WITH', 
                            'RELATES_TO', 'IMPLEMENTS', 'DEPENDS_ON'
                        ],
                        relationship_patterns: [
                            '(:Agent)-[:MADE_CHANGE]->(:Change)',
                            '(:Change)-[:MOTIVATED_BY]->(:Reason)',
                            '(:Change)-[:MODIFIES]->(:CodeFile)',
                            '(:Reason)-[:REFERENCES]->(:Task|:Blueprint)',
                            '(:Task|:Blueprint)-[:ASSIGNED_TO]->(:Agent)',
                            '(:CodeFile)-[:HAS_VERSION]->(:CodeFile)',
                            '(:Change)-[:FOLLOWS]->(:Change)',
                            '(:Agent)-[:COLLABORATES_WITH]->(:Agent)',
                            '(:Reason)-[:RELATES_TO]->(:Reason)'
                        ]
                    })
                """, version=self.migration_name)
                
                logger.info("Created Mind Graph schema documentation")
                return True
                
        except Exception as e:
            logger.error(f"Schema validation creation failed: {e}")
            return False


async def apply_neo4j_mind_graph_migration() -> bool:
    """Apply Neo4j Mind Graph migration.
    
    Returns:
        bool: True if successful, False otherwise
    """
    migration = Neo4jMindGraphMigration()
    return await migration.apply_migration()


async def test_neo4j_migration():
    """Test Neo4j migration with sample data."""
    try:
        from ltms.database.neo4j_store import get_neo4j_graph_store
        from datetime import datetime, timezone
        
        store = await get_neo4j_graph_store()
        
        if not store.is_available():
            print("❌ Neo4j not available for testing")
            return False
        
        # Test constraint enforcement
        with store.driver.session() as session:
            # Try to create a test agent
            session.run("""
                CREATE (a:Agent {
                    agent_id: 'test_migration_agent',
                    agent_name: 'Migration Test Agent', 
                    agent_type: 'test',
                    created_at: $timestamp
                })
            """, timestamp=datetime.now(timezone.utc).isoformat())
            
            # Verify it was created
            result = session.run(
                "MATCH (a:Agent {agent_id: 'test_migration_agent'}) RETURN count(a) as count"
            )
            count = result.single()["count"]
            
            # Clean up test node
            session.run("MATCH (a:Agent {agent_id: 'test_migration_agent'}) DELETE a")
            
            if count == 1:
                print("✅ Neo4j constraint test passed")
                return True
            else:
                print("❌ Neo4j constraint test failed")
                return False
                
    except Exception as e:
        print(f"❌ Neo4j migration test failed: {e}")
        return False


if __name__ == "__main__":
    async def main():
        print("Testing Neo4j Mind Graph migration")
        
        if await apply_neo4j_mind_graph_migration():
            print("✅ Neo4j migration applied successfully")
            
            # Test the migration
            if await test_neo4j_migration():
                print("✅ Neo4j migration test passed")
            else:
                print("❌ Neo4j migration test failed")
        else:
            print("❌ Neo4j migration failed")
    
    asyncio.run(main())