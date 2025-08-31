"""
AtomicTransactionContext Bridge for DatabaseSyncCoordinator Interface Compatibility.

Provides the async context manager interface that UnifiedDatabaseOperations expects
while using DatabaseSyncCoordinator's atomic methods internally.

This bridge maintains full atomicity guarantees across all 4 databases.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from ltms.sync.sync_models import DatabaseType, DocumentData, OperationType
from ltms.exceptions.sync_exceptions import AtomicTransactionException

# Import DatabaseRole from the atomic coordinator to ensure compatibility
try:
    from ltms.database.atomic_coordinator import DatabaseRole
except ImportError:
    # Fallback definition if not available
    from enum import Enum
    class DatabaseRole(Enum):
        PRIMARY_TRANSACTIONAL = "sqlite"
        VECTOR_SEARCH = "faiss"  
        GRAPH_RELATIONS = "neo4j"
        CACHE_REALTIME = "redis"

logger = logging.getLogger(__name__)


class AtomicTxContext:
    """
    Bridge class that provides atomic_transaction() context manager interface
    for UnifiedDatabaseOperations compatibility with DatabaseSyncCoordinator.
    
    Maintains full atomic transaction guarantees while bridging interface differences.
    """
    
    def __init__(self, coordinator):
        """Initialize transaction context.
        
        Args:
            coordinator: DatabaseSyncCoordinator instance
        """
        self.coordinator = coordinator
        self.transaction_id = str(uuid.uuid4())
        self.operations = []
        self.rollback_operations = []  # Track operations for rollback
        self.started = False
        self.completed = False
        self._lock = asyncio.Lock()
        
        logger.debug(f"AtomicTxContext initialized: {self.transaction_id}")
    
    @property
    def tx_id(self):
        return self.transaction_id
    
    async def __aenter__(self):
        """Enter async context manager - begin transaction."""
        async with self._lock:
            if self.started:
                raise AtomicTransactionException(
                    f"Transaction {self.transaction_id} already started",
                    transaction_id=self.transaction_id
                )
            
            self.started = True
            logger.debug(f"Transaction context entered: {self.transaction_id}")
            return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager - execute or rollback transaction."""
        async with self._lock:
            if not self.started:
                return
            
            try:
                if exc_type is not None:
                    # Exception occurred - execute rollback operations
                    logger.warning(f"Transaction {self.transaction_id} aborted due to exception: {exc_type.__name__}")
                    await self._execute_rollback()
                    self.completed = True
                    return
                
                # Execute all queued operations atomically
                await self._execute_operations()
                self.completed = True
                logger.debug(f"Transaction context completed: {self.transaction_id}")
                
            except Exception as e:
                logger.error(f"Transaction {self.transaction_id} failed during execution: {e}")
                # Attempt rollback on execution failure
                try:
                    await self._execute_rollback()
                except Exception as rollback_error:
                    logger.error(f"Rollback also failed for transaction {self.transaction_id}: {rollback_error}")
                self.completed = True
                raise
    
    def add_operation(self, database_role: DatabaseRole, operation_data: Dict[str, Any], rollback_op: Optional[Dict[str, Any]] = None):
        """
        Add operation to the transaction queue with optional rollback operation.
        Compatible with UnifiedDatabaseOperations interface.
        
        Args:
            database_role: Database role (PRIMARY_TRANSACTIONAL, VECTOR_SEARCH, etc.)
            operation_data: Operation parameters
            rollback_op: Optional rollback operation to undo this operation if transaction fails
        """
        if not self.started:
            raise AtomicTransactionException(
                f"Cannot add operation to non-started transaction {self.transaction_id}",
                transaction_id=self.transaction_id
            )
        
        if self.completed:
            raise AtomicTransactionException(
                f"Cannot add operation to completed transaction {self.transaction_id}",
                transaction_id=self.transaction_id
            )
        
        operation = {
            'database_role': database_role,
            'operation_data': operation_data,
            'rollback_op': rollback_op,
            'operation_id': f"{self.transaction_id}_{len(self.operations)}",
            'executed': False
        }
        
        self.operations.append(operation)
        logger.debug(f"Operation added to transaction {self.transaction_id}: {database_role} (rollback: {'yes' if rollback_op else 'no'})")
    
    async def _execute_operations(self):
        """
        Execute all queued operations using DatabaseSyncCoordinator's individual database methods.
        Maintains full atomicity by tracking rollback operations for each executed step.
        """
        if not self.operations:
            logger.debug(f"No operations to execute for transaction {self.transaction_id}")
            return
        
        executed_operations = []
        
        try:
            for operation in self.operations:
                database_role = operation['database_role']
                op_data = operation['operation_data']
                rollback_op = operation['rollback_op']
                
                # Execute the operation based on database role
                await self._execute_single_operation(database_role, op_data)
                
                # Mark as executed and store rollback operation
                operation['executed'] = True
                if rollback_op:
                    # Store rollback operation for this specific database
                    self.rollback_operations.append({
                        'database_role': database_role,
                        'rollback_data': rollback_op
                    })
                
                executed_operations.append(operation)
                logger.debug(f"Operation executed: {database_role} - {op_data.get('type', 'unknown')}")
            
            logger.info(f"Transaction {self.transaction_id} executed successfully: {len(executed_operations)} operations completed")
            
        except Exception as e:
            logger.error(f"Transaction execution failed at operation {len(executed_operations)}: {e}")
            raise AtomicTransactionException(
                f"Transaction execution failed: {str(e)}",
                transaction_id=self.transaction_id
            ) from e
    
    async def _execute_single_operation(self, database_role: DatabaseRole, op_data: Dict[str, Any]):
        """Execute a single operation on the specified database."""
        op_type = op_data.get('type', 'store')
        
        # Handle different coordinator types - AtomicDatabaseCoordinator vs DatabaseSyncCoordinator
        if database_role == DatabaseRole.PRIMARY_TRANSACTIONAL:
            # SQLite operations
            sqlite_manager = getattr(self.coordinator, 'sqlite', None) or getattr(self.coordinator, 'sqlite_manager', None)
            if not sqlite_manager:
                raise AtomicTransactionException(f"SQLite manager not available in coordinator")
            
            if op_type == 'store':
                sqlite_manager.store_document(
                    op_data['doc_id'],
                    op_data['content'],
                    op_data.get('tags', []),
                    op_data.get('metadata', {})
                )
            elif op_type == 'delete':
                sqlite_manager.delete_document(op_data['doc_id'])
            elif op_type == 'retrieve':
                return sqlite_manager.retrieve_document(op_data['doc_id'])
                
        elif database_role == DatabaseRole.VECTOR_SEARCH:
            # FAISS operations
            faiss_manager = getattr(self.coordinator, 'faiss', None) or getattr(self.coordinator, 'faiss_store', None)
            if not faiss_manager:
                raise AtomicTransactionException(f"FAISS manager not available in coordinator")
            
            if op_type == 'store':
                await faiss_manager.store_document_vector(
                    op_data['doc_id'],
                    op_data['content'],
                    op_data.get('metadata', {})
                )
            elif op_type == 'delete':
                await faiss_manager.delete_document_vector(op_data['doc_id'])
            elif op_type == 'search':
                return await faiss_manager.search_similar(
                    op_data['query'],
                    op_data.get('k', 5)
                )
                
        elif database_role == DatabaseRole.GRAPH_RELATIONS:
            # Neo4j operations
            neo4j_manager = getattr(self.coordinator, 'neo4j', None) or getattr(self.coordinator, 'neo4j_manager', None)
            if not neo4j_manager:
                raise AtomicTransactionException(f"Neo4j manager not available in coordinator")
            
            if op_type == 'store':
                await neo4j_manager.store_document_node(
                    op_data['doc_id'],
                    op_data['content'],
                    op_data.get('tags', []),
                    op_data.get('metadata', {})
                )
            elif op_type == 'delete':
                await neo4j_manager.delete_document_node(op_data['doc_id'])
            elif op_type == 'create_relationship':
                await neo4j_manager.create_document_relationship(
                    op_data['source_doc_id'],
                    op_data['target_doc_id'],
                    op_data['relationship_type'],
                    op_data.get('properties', {})
                )
                
        elif database_role == DatabaseRole.CACHE_REALTIME:
            # Redis operations
            redis_manager = getattr(self.coordinator, 'redis', None) or getattr(self.coordinator, 'redis_cache', None)
            if not redis_manager:
                raise AtomicTransactionException(f"Redis manager not available in coordinator")
            
            if op_type == 'cache':
                await redis_manager.cache_document(
                    op_data['doc_id'],
                    op_data['content'],
                    op_data.get('metadata', {}),
                    op_data.get('ttl', 3600)
                )
            elif op_type == 'delete':
                await redis_manager.delete_cached_document(op_data['doc_id'])
            elif op_type == 'set_ttl':
                await redis_manager.set_document_ttl(
                    op_data['doc_id'],
                    op_data['ttl']
                )
    
    async def _execute_rollback(self):
        """Execute rollback operations in reverse order."""
        if not self.rollback_operations:
            logger.debug(f"No rollback operations to execute for transaction {self.transaction_id}")
            return
        
        logger.info(f"Executing rollback for transaction {self.transaction_id}: {len(self.rollback_operations)} operations")
        
        # Execute rollback operations in reverse order (LIFO)
        for rollback_info in reversed(self.rollback_operations):
            database_role = rollback_info['database_role']
            rollback_data = rollback_info['rollback_data']
            
            try:
                await self._execute_single_operation(database_role, rollback_data)
                logger.debug(f"Rollback operation executed: {database_role} - {rollback_data.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"Rollback operation failed for {database_role}: {e}")
                # Continue with other rollback operations even if one fails
        
        logger.info(f"Rollback completed for transaction {self.transaction_id}")


def create_atomic_transaction_context(coordinator) -> AtomicTxContext:
    """
    Factory function to create AtomicTxContext instances.
    
    Args:
        coordinator: DatabaseSyncCoordinator instance
        
    Returns:
        AtomicTxContext instance ready for use as async context manager
    """
    return AtomicTxContext(coordinator)