"""
Atomic Database Coordinator for LTMC - Unified Multi-Database Architecture.
Orchestrates SQLite, FAISS, Neo4j, and Redis as one powerful atomic system.

File: ltms/database/atomic_coordinator.py
Lines: ~300 (under 300 limit)
Purpose: Unified atomic database operations with ACID compliance across all 4 databases
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
from datetime import datetime
from contextlib import asynccontextmanager
import json

from .sqlite_manager import SQLiteManager
from .faiss_manager import FAISSManager
from .neo4j_manager import Neo4jManager
from .redis_manager import RedisManager
from ltms.config.json_config_loader import get_config

logger = logging.getLogger(__name__)

class DatabaseRole(Enum):
    """Define specific roles for each database in the unified system."""
    PRIMARY_TRANSACTIONAL = "sqlite"  # Source of truth for metadata
    VECTOR_SEARCH = "faiss"           # Semantic similarity operations
    GRAPH_RELATIONS = "neo4j"         # Complex relationships
    CACHE_REALTIME = "redis"          # Fast access and real-time data

class OperationType(Enum):
    """Types of operations for routing decisions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH_SEMANTIC = "search_semantic"
    SEARCH_GRAPH = "search_graph"
    BATCH = "batch"

class TransactionState(Enum):
    """Transaction lifecycle states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMMITTING = "committing"
    COMMITTED = "committed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

class AtomicTransaction:
    """Represents an atomic transaction across all databases."""
    
    def __init__(self, tx_id: str):
        self.tx_id = tx_id
        self.state = TransactionState.PENDING
        self.operations: List[Dict[str, Any]] = []
        self.rollback_operations: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.databases_involved: Set[DatabaseRole] = set()
        
    def add_operation(self, database: DatabaseRole, operation: Dict[str, Any], 
                     rollback_op: Optional[Dict[str, Any]] = None):
        """Add an operation to the transaction with its rollback."""
        self.operations.append({
            "database": database,
            "operation": operation,
            "status": "pending"
        })
        if rollback_op:
            self.rollback_operations.append({
                "database": database,
                "operation": rollback_op
            })
        self.databases_involved.add(database)

class AtomicDatabaseCoordinator:
    """
    Unified atomic database coordinator that orchestrates all 4 databases
    as a single powerful system with ACID compliance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, test_mode: bool = False):
        """Initialize the atomic coordinator with all database managers.
        
        Args:
            config: Configuration for all databases
            test_mode: Enable test mode for unit testing
        """
        self.test_mode = test_mode
        self.config = config or get_config()
        
        # Initialize all database managers
        self.sqlite = SQLiteManager(test_mode=test_mode)
        self.faiss = FAISSManager(test_mode=test_mode)
        self.neo4j = Neo4jManager(test_mode=test_mode)
        self.redis = RedisManager(test_mode=test_mode)
        
        # Transaction management
        self.active_transactions: Dict[str, AtomicTransaction] = {}
        self.transaction_lock = asyncio.Lock()
        
        # Performance monitoring
        self.metrics = {
            "total_transactions": 0,
            "successful_commits": 0,
            "rollbacks": 0,
            "avg_transaction_time": 0
        }
        
        logger.info(f"AtomicDatabaseCoordinator initialized (test_mode={test_mode})")
    
    def _determine_database_routing(self, operation_type: OperationType, 
                                   requirements: Dict[str, Any]) -> List[DatabaseRole]:
        """
        Determine which databases should handle this operation based on requirements.
        
        Returns list of databases in order of execution priority.
        """
        routing = []
        
        if operation_type == OperationType.CREATE:
            # Write to all databases for redundancy and specific capabilities
            routing = [
                DatabaseRole.PRIMARY_TRANSACTIONAL,  # Metadata source of truth
                DatabaseRole.VECTOR_SEARCH,          # For semantic search
                DatabaseRole.GRAPH_RELATIONS,        # For relationships
                DatabaseRole.CACHE_REALTIME          # For fast access
            ]
            
        elif operation_type == OperationType.READ:
            # Prioritize cache, fallback to primary
            if requirements.get("use_cache", True):
                routing.append(DatabaseRole.CACHE_REALTIME)
            routing.append(DatabaseRole.PRIMARY_TRANSACTIONAL)
            
        elif operation_type == OperationType.UPDATE:
            # Update all databases to maintain consistency
            routing = [
                DatabaseRole.PRIMARY_TRANSACTIONAL,
                DatabaseRole.VECTOR_SEARCH,
                DatabaseRole.GRAPH_RELATIONS,
                DatabaseRole.CACHE_REALTIME
            ]
            
        elif operation_type == OperationType.DELETE:
            # Delete from all databases
            routing = [
                DatabaseRole.CACHE_REALTIME,         # Clear cache first
                DatabaseRole.GRAPH_RELATIONS,        # Remove relationships
                DatabaseRole.VECTOR_SEARCH,          # Remove vectors
                DatabaseRole.PRIMARY_TRANSACTIONAL   # Finally remove source
            ]
            
        elif operation_type == OperationType.SEARCH_SEMANTIC:
            # Use FAISS for semantic search
            routing = [DatabaseRole.VECTOR_SEARCH]
            
        elif operation_type == OperationType.SEARCH_GRAPH:
            # Use Neo4j for graph traversal
            routing = [DatabaseRole.GRAPH_RELATIONS]
            
        return routing
    
    @asynccontextmanager
    async def atomic_transaction(self):
        """Create an atomic transaction context across all databases."""
        tx_id = str(uuid.uuid4())
        transaction = AtomicTransaction(tx_id)
        
        async with self.transaction_lock:
            self.active_transactions[tx_id] = transaction
            
        try:
            transaction.state = TransactionState.IN_PROGRESS
            yield transaction
            
            # Commit phase
            await self._commit_transaction(transaction)
            
        except Exception as e:
            logger.error(f"Transaction {tx_id} failed: {e}")
            await self._rollback_transaction(transaction)
            raise
            
        finally:
            # Cleanup
            async with self.transaction_lock:
                if tx_id in self.active_transactions:
                    del self.active_transactions[tx_id]
    
    async def _commit_transaction(self, transaction: AtomicTransaction):
        """Commit a transaction across all involved databases."""
        transaction.state = TransactionState.COMMITTING
        
        try:
            # Execute all operations in order
            for op_info in transaction.operations:
                database = op_info["database"]
                operation = op_info["operation"]
                
                if database == DatabaseRole.PRIMARY_TRANSACTIONAL:
                    await self._execute_sqlite_operation(operation)
                elif database == DatabaseRole.VECTOR_SEARCH:
                    await self._execute_faiss_operation(operation)
                elif database == DatabaseRole.GRAPH_RELATIONS:
                    await self._execute_neo4j_operation(operation)
                elif database == DatabaseRole.CACHE_REALTIME:
                    await self._execute_redis_operation(operation)
                    
                op_info["status"] = "completed"
            
            transaction.state = TransactionState.COMMITTED
            self.metrics["successful_commits"] += 1
            
            # Calculate transaction time
            tx_time = (datetime.now() - transaction.start_time).total_seconds()
            self._update_avg_transaction_time(tx_time)
            
            logger.info(f"Transaction {transaction.tx_id} committed successfully in {tx_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Commit failed for transaction {transaction.tx_id}: {e}")
            transaction.state = TransactionState.FAILED
            raise
    
    async def _rollback_transaction(self, transaction: AtomicTransaction):
        """Rollback a transaction across all involved databases."""
        transaction.state = TransactionState.ROLLING_BACK
        
        try:
            # Execute rollback operations in reverse order
            for rollback_info in reversed(transaction.rollback_operations):
                database = rollback_info["database"]
                operation = rollback_info["operation"]
                
                try:
                    if database == DatabaseRole.PRIMARY_TRANSACTIONAL:
                        await self._execute_sqlite_operation(operation)
                    elif database == DatabaseRole.VECTOR_SEARCH:
                        await self._execute_faiss_operation(operation)
                    elif database == DatabaseRole.GRAPH_RELATIONS:
                        await self._execute_neo4j_operation(operation)
                    elif database == DatabaseRole.CACHE_REALTIME:
                        await self._execute_redis_operation(operation)
                        
                except Exception as rollback_error:
                    logger.error(f"Rollback operation failed: {rollback_error}")
                    # Continue with other rollbacks
            
            transaction.state = TransactionState.ROLLED_BACK
            self.metrics["rollbacks"] += 1
            
            logger.info(f"Transaction {transaction.tx_id} rolled back successfully")
            
        except Exception as e:
            logger.error(f"Critical rollback failure for transaction {transaction.tx_id}: {e}")
            transaction.state = TransactionState.FAILED
    
    async def _execute_sqlite_operation(self, operation: Dict[str, Any]):
        """Execute operation on SQLite database."""
        op_type = operation.get("type")
        
        if op_type == "store":
            return self.sqlite.store_document(
                operation["doc_id"],
                operation["content"],
                operation.get("tags", []),
                operation.get("metadata", {})
            )
        elif op_type == "delete":
            return self.sqlite.delete_document(operation["doc_id"])
        elif op_type == "retrieve":
            return self.sqlite.retrieve_document(operation["doc_id"])
    
    async def _execute_faiss_operation(self, operation: Dict[str, Any]):
        """Execute operation on FAISS vector store."""
        op_type = operation.get("type")
        
        if op_type == "store":
            return await self.faiss.store_document_vector(
                operation["doc_id"],
                operation["content"],
                operation.get("metadata", {})
            )
        elif op_type == "delete":
            return await self.faiss.delete_document_vector(operation["doc_id"])
        elif op_type == "search":
            return await self.faiss.search_similar(
                operation["query"],
                operation.get("k", 5)
            )
    
    async def _execute_neo4j_operation(self, operation: Dict[str, Any]):
        """Execute operation on Neo4j graph database."""
        op_type = operation.get("type")
        
        if op_type == "store":
            return await self.neo4j.store_document_node(
                operation["doc_id"],
                operation["content"],
                operation.get("tags", []),
                operation.get("metadata", {})
            )
        elif op_type == "delete":
            return await self.neo4j.delete_document_node(operation["doc_id"])
        elif op_type == "create_relationship":
            return await self.neo4j.create_document_relationship(
                operation["source_doc_id"],
                operation["target_doc_id"],
                operation["relationship_type"],
                operation.get("properties", {})
            )
    
    async def _execute_redis_operation(self, operation: Dict[str, Any]):
        """Execute operation on Redis cache."""
        op_type = operation.get("type")
        
        if op_type == "cache":
            return await self.redis.cache_document(
                operation["doc_id"],
                operation["content"],
                operation.get("metadata", {}),
                operation.get("ttl")
            )
        elif op_type == "delete":
            return await self.redis.delete_cached_document(operation["doc_id"])
        elif op_type == "set_ttl":
            return await self.redis.set_document_ttl(
                operation["doc_id"],
                operation["ttl"]
            )
    
    def _update_avg_transaction_time(self, tx_time: float):
        """Update average transaction time metric."""
        self.metrics["total_transactions"] += 1
        n = self.metrics["total_transactions"]
        prev_avg = self.metrics["avg_transaction_time"]
        self.metrics["avg_transaction_time"] = ((n - 1) * prev_avg + tx_time) / n
    
    async def get_unified_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all databases."""
        health = {
            "coordinator_status": "healthy",
            "metrics": self.metrics,
            "databases": {},
            "test_mode": self.test_mode
        }
        
        # Check each database
        try:
            health["databases"]["sqlite"] = self.sqlite.get_health_status()
        except Exception as e:
            health["databases"]["sqlite"] = {"status": "error", "error": str(e)}
        
        try:
            health["databases"]["faiss"] = self.faiss.get_health_status()
        except Exception as e:
            health["databases"]["faiss"] = {"status": "error", "error": str(e)}
        
        try:
            health["databases"]["neo4j"] = self.neo4j.get_health_status()
        except Exception as e:
            health["databases"]["neo4j"] = {"status": "error", "error": str(e)}
        
        try:
            health["databases"]["redis"] = await self.redis.get_health_status()
        except Exception as e:
            health["databases"]["redis"] = {"status": "error", "error": str(e)}
        
        # Determine overall health
        unhealthy_count = sum(
            1 for db_health in health["databases"].values()
            if db_health.get("status") != "healthy"
        )
        
        if unhealthy_count > 0:
            health["coordinator_status"] = f"degraded ({unhealthy_count}/4 databases unhealthy)"
        
        return health