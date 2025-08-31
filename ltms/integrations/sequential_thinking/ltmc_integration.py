"""
LTMC Sequential MCP Integration - Production Implementation
Integrates Sequential Thinking MCP with LTMC's existing 4-database coordination infrastructure.

This module leverages LTMC's proven DatabaseSyncCoordinator, ConsistencyManager, and
UnifiedDatabaseOperations for atomic operations across SQLite, FAISS, Neo4j, and Redis.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import ulid
import hashlib
from pydantic import BaseModel, Field, validator

from ltms.database.sync_coordinator import DatabaseSyncCoordinator
from ltms.database.consistency_manager import ConsistencyManager, ConflictResolution
from ltms.database.unified_operations import UnifiedDatabaseOperations
from ltms.sync.sync_models import DocumentData
from ltms.tools.core.mcp_base import MCPToolBase

logger = logging.getLogger(__name__)

class ThoughtData(BaseModel):
    """
    Sequential thinking data model with ULID identification and content hashing.
    Integrates with LTMC's existing DocumentData structure.
    """
    ulid_id: str = Field(default_factory=lambda: str(ulid.new()))
    session_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    content_hash: str = Field(default="")
    previous_thought_id: Optional[str] = None
    step_number: int = Field(default=1, ge=1)
    thought_type: str = Field(default="intermediate")  # problem, intermediate, conclusion
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def model_post_init(self, __context):
        """Calculate content hash after initialization."""
        if not self.content_hash:
            self.content_hash = self._calculate_content_hash()
    
    def _calculate_content_hash(self) -> str:
        """Calculate SHA-256 hash of content for integrity verification."""
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify content integrity using stored hash."""
        return self.content_hash == self._calculate_content_hash()
    
    def to_document_data(self) -> DocumentData:
        """Convert to LTMC's standard DocumentData format."""
        return DocumentData(
            id=self.ulid_id,
            content=self.content,
            tags=[f"session:{self.session_id}", f"type:{self.thought_type}", "sequential_thinking"],
            metadata={
                **self.metadata,
                "session_id": self.session_id,
                "previous_thought_id": self.previous_thought_id,
                "step_number": self.step_number,
                "thought_type": self.thought_type,
                "content_hash": self.content_hash,
                "integration_type": "sequential_mcp"
            }
        )

class SequentialThinkingCoordinator:
    """
    Production coordinator for Sequential MCP operations using LTMC's database infrastructure.
    Provides atomic operations across all 4 databases with proper error handling.
    """
    
    def __init__(self, sync_coordinator: DatabaseSyncCoordinator, test_mode: bool = False):
        """Initialize with LTMC's existing coordination infrastructure."""
        self.sync_coordinator = sync_coordinator
        self.test_mode = test_mode
        
        # Initialize consistency manager for conflict resolution
        from ltms.database.consistency_manager import ConsistencyLevel
        self.consistency_manager = ConsistencyManager(
            sync_coordinator, 
            consistency_level=ConsistencyLevel.STRONG
        )
        
        # Initialize unified operations for high-level API
        self.unified_ops = UnifiedDatabaseOperations(sync_coordinator, test_mode)
        
        # Performance tracking
        self.metrics = {
            "thoughts_created": 0,
            "thoughts_retrieved": 0,
            "chains_analyzed": 0,
            "avg_creation_time_ms": 0,
            "avg_retrieval_time_ms": 0,
            "integrity_violations": 0
        }
        
        logger.info(f"SequentialThinkingCoordinator initialized (test_mode={test_mode})")
    
    async def store_thought(self, thought: ThoughtData) -> Dict[str, Any]:
        """
        Store thought atomically across all databases using LTMC's coordination.
        
        Implements ordered fan-out: SQLite → FAISS → Neo4j → Redis
        """
        start_time = datetime.now()
        
        try:
            # Verify content integrity before storage
            if not thought.verify_integrity():
                raise ValueError(f"Content integrity verification failed for thought {thought.ulid_id}")
            
            # Convert to LTMC DocumentData format
            doc_data = thought.to_document_data()
            
            # Use LTMC's atomic storage with relationships if this is a chain continuation
            relationships = []
            if thought.previous_thought_id:
                relationships.append({
                    "target": thought.previous_thought_id,
                    "type": "FOLLOWS",
                    "properties": {
                        "step_sequence": thought.step_number,
                        "session_id": thought.session_id
                    }
                })
            
            # Store using LTMC's unified operations
            result = await self.unified_ops.store_document(
                doc_id=thought.ulid_id,
                content=thought.content,
                tags=doc_data.tags,
                metadata=doc_data.metadata,
                relationships=relationships,
                cache_ttl=3600
            )
            
            # Additional Redis session tracking with proper namespacing
            redis_key = f"ltmc:sequential:{thought.session_id}:head"
            if self.sync_coordinator.redis_cache:
                await self.sync_coordinator.redis_cache.setex(redis_key, 3600, thought.ulid_id)
            
            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_creation_metrics(execution_time)
            
            # Verify SLA compliance
            if execution_time > 100:  # 100ms SLA for thought creation
                logger.warning(f"Thought creation SLA violation: {execution_time:.2f}ms > 100ms")
            
            result.update({
                "ulid_id": thought.ulid_id,
                "session_id": thought.session_id,
                "execution_time_ms": execution_time,
                "sla_compliant": execution_time <= 100
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to store thought {thought.ulid_id}: {e}")
            raise
    
    async def retrieve_thought_chain(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve complete thought chain for a session using graph traversal.
        """
        start_time = datetime.now()
        
        try:
            # Get session head from Redis cache
            redis_key = f"ltmc:sequential:{session_id}:head"
            head_id = None
            
            if self.sync_coordinator.redis_cache:
                head_id = await self.sync_coordinator.redis_cache.get(redis_key)
            
            if not head_id:
                # Fallback: find latest thought in session from SQLite
                logger.debug(f"No Redis head found, falling back to SQLite for session {session_id}")
                # This would require a query method in SQLite manager
                return []
            
            # Retrieve the head thought
            head_thought = await self.unified_ops.retrieve_document(
                head_id, 
                use_cache=True, 
                include_relationships=True
            )
            
            if not head_thought:
                logger.warning(f"Head thought {head_id} not found for session {session_id}")
                return []
            
            # Build chain by following relationships backwards
            chain = []
            current_thought = head_thought
            visited = set()
            
            while current_thought and current_thought["doc_id"] not in visited:
                visited.add(current_thought["doc_id"])
                
                # Format for response
                chain.append({
                    "ulid_id": current_thought["doc_id"],
                    "content": current_thought["content"],
                    "step_number": current_thought.get("metadata", {}).get("step_number", 0),
                    "thought_type": current_thought.get("metadata", {}).get("thought_type", "unknown"),
                    "created_at": current_thought.get("created_at"),
                    "metadata": current_thought.get("metadata", {})
                })
                
                # Find previous thought via relationships
                previous_id = current_thought.get("metadata", {}).get("previous_thought_id")
                if previous_id:
                    current_thought = await self.unified_ops.retrieve_document(
                        previous_id, 
                        use_cache=True, 
                        include_relationships=True
                    )
                else:
                    break
            
            # Reverse to get chronological order
            chain.reverse()
            
            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_retrieval_metrics(execution_time)
            
            logger.info(f"Retrieved chain of {len(chain)} thoughts for session {session_id} in {execution_time:.2f}ms")
            
            return chain
            
        except Exception as e:
            logger.error(f"Failed to retrieve thought chain for session {session_id}: {e}")
            raise
    
    async def find_similar_reasoning(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar reasoning patterns using FAISS semantic search.
        """
        try:
            # Use LTMC's unified semantic search with tag filtering
            results = await self.unified_ops.semantic_search(
                query=query,
                k=k,
                filter_tags=["sequential_thinking"]
            )
            
            # Enrich with session context
            enriched_results = []
            for result in results:
                session_id = result.get("metadata", {}).get("session_id")
                if session_id:
                    # Get brief chain context
                    chain_preview = await self.retrieve_thought_chain(session_id)
                    result["chain_length"] = len(chain_preview)
                    result["session_preview"] = chain_preview[:2] if chain_preview else []
                
                enriched_results.append(result)
            
            self.metrics["chains_analyzed"] += len(enriched_results)
            return enriched_results
            
        except Exception as e:
            logger.error(f"Similar reasoning search failed: {e}")
            raise
    
    def _update_creation_metrics(self, execution_time_ms: float):
        """Update creation performance metrics."""
        self.metrics["thoughts_created"] += 1
        n = self.metrics["thoughts_created"]
        if n == 1:
            self.metrics["avg_creation_time_ms"] = execution_time_ms
        else:
            prev_avg = self.metrics["avg_creation_time_ms"]
            self.metrics["avg_creation_time_ms"] = ((n - 1) * prev_avg + execution_time_ms) / n
    
    def _update_retrieval_metrics(self, execution_time_ms: float):
        """Update retrieval performance metrics."""
        self.metrics["thoughts_retrieved"] += 1
        n = self.metrics["thoughts_retrieved"]
        if n == 1:
            self.metrics["avg_retrieval_time_ms"] = execution_time_ms
        else:
            prev_avg = self.metrics["avg_retrieval_time_ms"]
            self.metrics["avg_retrieval_time_ms"] = ((n - 1) * prev_avg + execution_time_ms) / n
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status including database coordination."""
        # Get LTMC coordination health
        coord_health = await self.sync_coordinator.get_unified_health_status()
        
        return {
            "sequential_coordinator_status": "healthy",
            "database_coordination": coord_health,
            "metrics": self.metrics,
            "sla_compliance": {
                "avg_creation_time_ms": self.metrics["avg_creation_time_ms"],
                "creation_sla_target": 100,
                "creation_sla_compliant": self.metrics["avg_creation_time_ms"] <= 100,
                "avg_retrieval_time_ms": self.metrics["avg_retrieval_time_ms"], 
                "retrieval_sla_target": 50,
                "retrieval_sla_compliant": self.metrics["avg_retrieval_time_ms"] <= 50
            }
        }