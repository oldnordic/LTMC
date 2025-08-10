"""
Neo4j Service - Graph Operations
===============================

Neo4j graph database operations.
Existing Neo4j config: port 7687, password 'kwe_password'
"""

import neo4j
import logging
from typing import List, Dict, Any, Optional

from config.settings import LTMCSettings
from utils.performance_utils import measure_performance


class Neo4jService:
    """
    Neo4j service for graph database operations.
    
    Uses existing Neo4j instance on port 7687 with password.
    """
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.driver: Optional[neo4j.AsyncDriver] = None
        
    async def initialize(self) -> bool:
        """Initialize Neo4j driver."""
        if not self.settings.neo4j_enabled:
            self.logger.info("Neo4j disabled in settings")
            return False
            
        try:
            self.driver = neo4j.AsyncGraphDatabase.driver(
                self.settings.get_neo4j_uri(),
                auth=(self.settings.neo4j_user, self.settings.neo4j_password)
            )
            
            # Test connection
            await self.driver.verify_connectivity()
            self.logger.info("✅ Neo4j connection initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Neo4j initialization failed: {e}")
            return False
    
    @measure_performance
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform Neo4j graph database health check.
        
        Returns:
            Dict with health status, connection info, and database metrics
        """
        import time
        
        try:
            if not self.driver:
                return {
                    "status": "error",
                    "connected": False,
                    "service": "Neo4j",
                    "latency_ms": None,
                    "metrics": {"error_details": "Driver not initialized"},
                    "error": "Neo4j driver not initialized"
                }
            
            # Test database connectivity and basic operations
            start_time = time.time()
            
            async with self.driver.session() as session:
                # Test basic connectivity with simple query
                result = await session.run("RETURN 1 as test")
                test_record = await result.single()
                
                # Test database info query
                result = await session.run("CALL db.info() YIELD name, value RETURN name, value")
                db_info = await result.data()
                
                # Test node count (lightweight query)
                result = await session.run("MATCH (n) RETURN count(n) as node_count LIMIT 1")
                count_record = await result.single()
                node_count = count_record["node_count"] if count_record else 0
                
                # Test relationship count 
                result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count LIMIT 1")
                rel_record = await result.single()
                relationship_count = rel_record["rel_count"] if rel_record else 0
                
                # Test write capability with transaction rollback
                tx = await session.begin_transaction()
                try:
                    await tx.run("CREATE (:HealthCheck {timestamp: timestamp()})")
                    await tx.rollback()  # Don't actually create the node
                    write_capable = True
                except Exception:
                    write_capable = False
                    await tx.rollback()
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract relevant database info
            db_metrics = {}
            for info in db_info:
                if info.get("name") in ["neo4jVersion", "databaseName", "storeSizeBytes"]:
                    db_metrics[info["name"]] = info.get("value")
            
            return {
                "status": "healthy",
                "connected": True,
                "service": "Neo4j",
                "latency_ms": round(latency_ms, 2),
                "metrics": {
                    "node_count": node_count,
                    "relationship_count": relationship_count,
                    "write_capable": write_capable,
                    "database_info": db_metrics
                },
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Neo4j health check failed: {e}")
            return {
                "status": "error",
                "connected": False,
                "service": "Neo4j",
                "latency_ms": None,
                "metrics": {
                    "error_details": str(e),
                    "driver_initialized": self.driver is not None
                },
                "error": str(e)
            }

    @measure_performance
    async def create_node(self, label: str, properties: Dict[str, Any]) -> Optional[int]:
        """Create node in Neo4j."""
        if not self.driver:
            return None
            
        async with self.driver.session() as session:
            try:
                result = await session.run(
                    f"CREATE (n:{label} $props) RETURN id(n) as node_id",
                    props=properties
                )
                record = await result.single()
                return record["node_id"] if record else None
            except Exception as e:
                self.logger.error(f"Neo4j create node error: {e}")
                return None
    
    async def close(self) -> None:
        """Close Neo4j driver."""
        if self.driver:
            await self.driver.close()