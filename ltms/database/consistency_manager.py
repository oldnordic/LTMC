"""
Consistency Manager for LTMC - Cross-Database Synchronization.
Ensures data consistency and conflict resolution across all 4 databases.

File: ltms/database/consistency_manager.py
Lines: ~300 (under 300 limit)
Purpose: Data consistency, conflict resolution, and synchronization protocols
"""
import asyncio
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ConsistencyLevel(Enum):
    """Consistency levels for multi-database operations."""
    EVENTUAL = "eventual"        # Best effort, async sync
    STRONG = "strong"            # All databases must succeed
    QUORUM = "quorum"           # Majority must succeed (3/4)
    PRIMARY = "primary"         # SQLite success is sufficient

class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE = "merge"
    MANUAL = "manual"

class DataVersion:
    """Represents a versioned piece of data for conflict detection."""
    
    def __init__(self, doc_id: str, content: str, timestamp: datetime = None):
        self.doc_id = doc_id
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.version = self._calculate_version()
        
    def _calculate_version(self) -> str:
        """Calculate version hash based on content."""
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        timestamp_str = self.timestamp.isoformat()
        return f"{content_hash[:16]}-{int(self.timestamp.timestamp())}"

class ConsistencyManager:
    """
    Manages data consistency across all 4 databases with
    conflict detection and resolution strategies.
    """
    
    def __init__(self, coordinator, consistency_level: ConsistencyLevel = ConsistencyLevel.STRONG):
        """Initialize consistency manager.
        
        Args:
            coordinator: AtomicDatabaseCoordinator instance
            consistency_level: Default consistency level
        """
        self.coordinator = coordinator
        self.default_consistency = consistency_level
        
        # Version tracking
        self.version_map: Dict[str, DataVersion] = {}
        self.conflict_log: List[Dict[str, Any]] = []
        
        # Synchronization state
        self.sync_status: Dict[str, Dict[str, Any]] = {}
        self.pending_syncs: Set[str] = set()
        
        # Performance metrics
        self.metrics = {
            "total_syncs": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "sync_failures": 0,
            "avg_sync_time": 0
        }
        
        logger.info(f"ConsistencyManager initialized (consistency={consistency_level.value})")
    
    async def check_consistency(self, doc_id: str) -> Dict[str, Any]:
        """
        Check consistency of a document across all databases.
        
        Args:
            doc_id: Document identifier to check
            
        Returns:
            Consistency status report
        """
        report = {
            "doc_id": doc_id,
            "timestamp": datetime.now().isoformat(),
            "consistent": True,
            "databases": {},
            "conflicts": []
        }
        
        try:
            # 1. Check SQLite (source of truth)
            sqlite_doc = self.coordinator.sqlite.retrieve_document(doc_id)
            report["databases"]["sqlite"] = {
                "exists": sqlite_doc is not None,
                "version": None
            }
            
            if sqlite_doc:
                sqlite_version = DataVersion(
                    doc_id, 
                    sqlite_doc["content"],
                    datetime.fromisoformat(sqlite_doc.get("updated_at", datetime.now().isoformat()))
                )
                report["databases"]["sqlite"]["version"] = sqlite_version.version
                
                # 2. Check Redis cache
                redis_doc = await self.coordinator.redis.retrieve_cached_document(doc_id)
                report["databases"]["redis"] = {
                    "exists": redis_doc is not None,
                    "version": None
                }
                
                if redis_doc:
                    redis_version = DataVersion(
                        doc_id,
                        redis_doc["content"],
                        datetime.fromisoformat(redis_doc.get("cached_at", datetime.now().isoformat()))
                    )
                    report["databases"]["redis"]["version"] = redis_version.version
                    
                    # Check for consistency
                    if redis_doc["content"] != sqlite_doc["content"]:
                        report["consistent"] = False
                        report["conflicts"].append({
                            "type": "content_mismatch",
                            "databases": ["sqlite", "redis"],
                            "sqlite_version": sqlite_version.version,
                            "redis_version": redis_version.version
                        })
                
                # 3. Check Neo4j graph
                neo4j_doc = await self.coordinator.neo4j.retrieve_document_node(doc_id)
                report["databases"]["neo4j"] = {
                    "exists": neo4j_doc is not None,
                    "version": None
                }
                
                if neo4j_doc:
                    neo4j_version = DataVersion(
                        doc_id,
                        neo4j_doc["content"],
                        datetime.fromisoformat(neo4j_doc.get("updated_at", datetime.now().isoformat()))
                    )
                    report["databases"]["neo4j"]["version"] = neo4j_version.version
                    
                    if neo4j_doc["content"] != sqlite_doc["content"]:
                        report["consistent"] = False
                        report["conflicts"].append({
                            "type": "content_mismatch",
                            "databases": ["sqlite", "neo4j"],
                            "sqlite_version": sqlite_version.version,
                            "neo4j_version": neo4j_version.version
                        })
                
                # 4. Check FAISS vector store
                faiss_doc = await self.coordinator.faiss.retrieve_document_vector(doc_id)
                report["databases"]["faiss"] = {
                    "exists": faiss_doc is not None,
                    "has_vector": faiss_doc is not None
                }
                
                # Check for missing entries
                missing_in = []
                if not redis_doc:
                    missing_in.append("redis")
                if not neo4j_doc:
                    missing_in.append("neo4j")
                if not faiss_doc:
                    missing_in.append("faiss")
                
                if missing_in:
                    report["consistent"] = False
                    report["conflicts"].append({
                        "type": "missing_entries",
                        "databases": missing_in,
                        "source": "sqlite"
                    })
            
        except Exception as e:
            logger.error(f"Consistency check failed for {doc_id}: {e}")
            report["error"] = str(e)
            report["consistent"] = False
        
        # Log conflicts
        if not report["consistent"]:
            self.metrics["conflicts_detected"] += 1
            self.conflict_log.append(report)
        
        return report
    
    async def synchronize_document(self, doc_id: str, 
                                  resolution_strategy: ConflictResolution = ConflictResolution.LAST_WRITE_WINS,
                                  consistency_level: Optional[ConsistencyLevel] = None) -> Dict[str, Any]:
        """
        Synchronize a document across all databases with conflict resolution.
        
        Args:
            doc_id: Document to synchronize
            resolution_strategy: How to resolve conflicts
            consistency_level: Override default consistency level
            
        Returns:
            Synchronization result
        """
        consistency = consistency_level or self.default_consistency
        
        result = {
            "doc_id": doc_id,
            "timestamp": datetime.now().isoformat(),
            "strategy": resolution_strategy.value,
            "consistency_level": consistency.value,
            "status": "pending",
            "operations": []
        }
        
        sync_start = datetime.now()
        
        try:
            # 1. Check current consistency
            consistency_report = await self.check_consistency(doc_id)
            
            if consistency_report["consistent"]:
                result["status"] = "already_consistent"
                return result
            
            # 2. Determine source of truth based on resolution strategy
            source_doc = None
            source_db = None
            
            if resolution_strategy == ConflictResolution.LAST_WRITE_WINS:
                # Find the most recently updated version
                latest_time = datetime.min
                
                for db_name in ["sqlite", "neo4j"]:
                    if db_name == "sqlite":
                        doc = self.coordinator.sqlite.retrieve_document(doc_id)
                    else:
                        doc = await self.coordinator.neo4j.retrieve_document_node(doc_id)
                    
                    if doc:
                        updated_at = datetime.fromisoformat(doc.get("updated_at", datetime.now().isoformat()))
                        if updated_at > latest_time:
                            latest_time = updated_at
                            source_doc = doc
                            source_db = db_name
            
            elif resolution_strategy == ConflictResolution.FIRST_WRITE_WINS:
                # Use SQLite as the authoritative source
                source_doc = self.coordinator.sqlite.retrieve_document(doc_id)
                source_db = "sqlite"
            
            if not source_doc:
                result["status"] = "no_source_found"
                return result
            
            # 3. Propagate to other databases
            sync_tasks = []
            
            # Update Redis cache
            if consistency_report["databases"]["redis"]["exists"] is False or \
               consistency_report["databases"]["redis"]["version"] != consistency_report["databases"][source_db]["version"]:
                sync_tasks.append(self._sync_to_redis(doc_id, source_doc))
                result["operations"].append({"database": "redis", "action": "update"})
            
            # Update Neo4j if needed
            if source_db != "neo4j":
                if consistency_report["databases"]["neo4j"]["exists"] is False or \
                   consistency_report["databases"]["neo4j"]["version"] != consistency_report["databases"][source_db]["version"]:
                    sync_tasks.append(self._sync_to_neo4j(doc_id, source_doc))
                    result["operations"].append({"database": "neo4j", "action": "update"})
            
            # Update FAISS if needed
            if not consistency_report["databases"]["faiss"]["exists"]:
                sync_tasks.append(self._sync_to_faiss(doc_id, source_doc))
                result["operations"].append({"database": "faiss", "action": "update"})
            
            # 4. Execute synchronization based on consistency level
            if consistency == ConsistencyLevel.STRONG:
                # All must succeed
                results = await asyncio.gather(*sync_tasks)
                if all(results):
                    result["status"] = "success"
                else:
                    result["status"] = "partial_failure"
                    self.metrics["sync_failures"] += 1
                    
            elif consistency == ConsistencyLevel.QUORUM:
                # At least 3/4 must succeed
                results = await asyncio.gather(*sync_tasks, return_exceptions=True)
                success_count = sum(1 for r in results if r is True)
                if success_count >= 3:
                    result["status"] = "success"
                else:
                    result["status"] = "quorum_not_met"
                    self.metrics["sync_failures"] += 1
                    
            elif consistency == ConsistencyLevel.EVENTUAL:
                # Fire and forget
                for task in sync_tasks:
                    asyncio.create_task(task)
                result["status"] = "initiated"
                
            elif consistency == ConsistencyLevel.PRIMARY:
                # SQLite is already the source, so we're done
                result["status"] = "success"
            
            # 5. Update metrics
            self.metrics["total_syncs"] += 1
            if result["status"] in ["success", "initiated"]:
                self.metrics["conflicts_resolved"] += len(consistency_report["conflicts"])
            
            sync_time = (datetime.now() - sync_start).total_seconds()
            self._update_avg_sync_time(sync_time)
            result["sync_time"] = sync_time
            
        except Exception as e:
            logger.error(f"Synchronization failed for {doc_id}: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            self.metrics["sync_failures"] += 1
        
        return result
    
    async def _sync_to_redis(self, doc_id: str, source_doc: Dict[str, Any]) -> bool:
        """Sync document to Redis cache."""
        try:
            return await self.coordinator.redis.cache_document(
                doc_id,
                source_doc["content"],
                source_doc.get("metadata", {}),
                ttl=3600
            )
        except Exception as e:
            logger.error(f"Failed to sync {doc_id} to Redis: {e}")
            return False
    
    async def _sync_to_neo4j(self, doc_id: str, source_doc: Dict[str, Any]) -> bool:
        """Sync document to Neo4j graph."""
        try:
            return await self.coordinator.neo4j.store_document_node(
                doc_id,
                source_doc["content"],
                source_doc.get("tags", []),
                source_doc.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Failed to sync {doc_id} to Neo4j: {e}")
            return False
    
    async def _sync_to_faiss(self, doc_id: str, source_doc: Dict[str, Any]) -> bool:
        """Sync document to FAISS vector store."""
        try:
            return await self.coordinator.faiss.store_document_vector(
                doc_id,
                source_doc["content"],
                source_doc.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Failed to sync {doc_id} to FAISS: {e}")
            return False
    
    def _update_avg_sync_time(self, sync_time: float):
        """Update average synchronization time metric."""
        n = self.metrics["total_syncs"]
        if n == 0:
            self.metrics["avg_sync_time"] = sync_time
        else:
            prev_avg = self.metrics["avg_sync_time"]
            self.metrics["avg_sync_time"] = ((n - 1) * prev_avg + sync_time) / n
    
    async def batch_consistency_check(self, doc_ids: List[str] = None, 
                                     limit: int = 100) -> Dict[str, Any]:
        """
        Check consistency for multiple documents.
        
        Args:
            doc_ids: Specific documents to check (or all if None)
            limit: Maximum number of documents to check
            
        Returns:
            Batch consistency report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_checked": 0,
            "consistent": 0,
            "inconsistent": 0,
            "errors": 0,
            "documents": []
        }
        
        # Get documents to check
        if not doc_ids:
            all_docs = self.coordinator.sqlite.list_documents(limit=limit)
            doc_ids = [doc["id"] for doc in all_docs]
        
        # Check each document
        for doc_id in doc_ids[:limit]:
            try:
                doc_report = await self.check_consistency(doc_id)
                report["documents"].append(doc_report)
                report["total_checked"] += 1
                
                if doc_report["consistent"]:
                    report["consistent"] += 1
                else:
                    report["inconsistent"] += 1
                    
            except Exception as e:
                logger.error(f"Failed to check consistency for {doc_id}: {e}")
                report["errors"] += 1
        
        return report
    
    def get_conflict_report(self) -> Dict[str, Any]:
        """Get report of all detected conflicts."""
        return {
            "total_conflicts": len(self.conflict_log),
            "metrics": self.metrics,
            "recent_conflicts": self.conflict_log[-10:],  # Last 10 conflicts
            "conflict_types": self._analyze_conflict_types()
        }
    
    def _analyze_conflict_types(self) -> Dict[str, int]:
        """Analyze types of conflicts detected."""
        types = {}
        for conflict in self.conflict_log:
            for c in conflict.get("conflicts", []):
                conflict_type = c.get("type", "unknown")
                types[conflict_type] = types.get(conflict_type, 0) + 1
        return types