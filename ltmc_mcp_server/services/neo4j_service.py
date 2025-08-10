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