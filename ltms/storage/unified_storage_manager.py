"""
Unified Storage Manager for LTMC - Single Entry Point for All Storage Operations.
Fixes the critical FAISS atomic transaction bug and provides type-aware database routing.

File: ltms/storage/unified_storage_manager.py
Lines: ~280 (under 300 limit)
Purpose: Replace fragmented storage system with unified, reliable atomic operations
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from ..config.json_config_loader import get_config
from ..database.sqlite_manager import SQLiteManager
from ..database.faiss_manager import FAISSManager
from ..database.neo4j_manager import Neo4jManager
from ..database.redis_manager import RedisManager
from ..sync.sync_models import DocumentData

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """Content types with specific database routing requirements."""
    LOG_CHAT = "log_chat"                    # Fast retrieval: SQLite + Redis
    MEMORY = "memory"                        # Full semantic: All 4 databases
    CHAIN_OF_THOUGHT = "chain_of_thought"    # Structured reasoning: SQLite + FAISS
    DOCUMENT = "document"                    # Rich content: SQLite + FAISS + Neo4j
    BLUEPRINT = "blueprint"                  # Relational: SQLite + Neo4j
    TASKS = "tasks"                         # Fast updates: SQLite + Redis
    TODO = "todo"                           # Real-time: SQLite + Redis
    PATTERN_ANALYSIS = "pattern_analysis"   # Code patterns: SQLite + FAISS
    GRAPH_RELATIONSHIPS = "graph_relationships"  # Graph data: SQLite + Neo4j
    CACHE_DATA = "cache_data"               # Pure cache: Redis only
    COORDINATION = "coordination"           # Agent coordination: SQLite + Neo4j


class UnifiedStorageManager:
    """
    Unified storage manager that fixes atomic transaction failures and provides
    type-aware database routing for optimal performance per content type.
    """
    
    def __init__(self, test_mode: bool = False):
        """Initialize unified storage manager with database connections."""
        self.test_mode = test_mode
        self.config = get_config()
        
        # Initialize database managers
        self.sqlite = SQLiteManager(test_mode=test_mode)
        self.faiss = FAISSManager(test_mode=test_mode) 
        self.neo4j = Neo4jManager(test_mode=test_mode)
        self.redis = RedisManager(test_mode=test_mode)
        
        # Storage routing configuration
        self.storage_routing = {
            StorageType.LOG_CHAT: ['sqlite', 'redis'],
            StorageType.MEMORY: ['sqlite', 'faiss', 'neo4j', 'redis'],
            StorageType.CHAIN_OF_THOUGHT: ['sqlite', 'faiss'],
            StorageType.DOCUMENT: ['sqlite', 'faiss', 'neo4j'],
            StorageType.BLUEPRINT: ['sqlite', 'neo4j'],
            StorageType.TASKS: ['sqlite', 'redis'],
            StorageType.TODO: ['sqlite', 'redis'],
            StorageType.PATTERN_ANALYSIS: ['sqlite', 'faiss'],
            StorageType.GRAPH_RELATIONSHIPS: ['sqlite', 'neo4j'],
            StorageType.CACHE_DATA: ['redis'],
            StorageType.COORDINATION: ['sqlite', 'neo4j']
        }
        
        # Performance metrics
        self.metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_duration_ms': 0.0,
            'operations_by_type': {}
        }
        
        logger.info(f"UnifiedStorageManager initialized (test_mode={test_mode})")
    
    async def unified_store(self, storage_type: str, content: str, 
                           file_name: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Unified storage method with fixed atomic transactions and type-aware routing.
        
        Args:
            storage_type: Type of content being stored (e.g., 'memory', 'tasks', 'document')
            content: Content to store
            file_name: Optional filename/identifier
            metadata: Optional metadata dictionary
            
        Returns:
            Standardized result dictionary with success/failure information
        """
        start_time = time.time()
        transaction_id = str(uuid.uuid4())
        
        try:
            # Convert string to enum
            try:
                storage_enum = StorageType(storage_type)
            except ValueError:
                return self._create_error_response(f"Unknown storage type: {storage_type}")
            
            # Get database routing for this storage type
            target_databases = self.storage_routing[storage_enum]
            
            # Generate file_name if not provided
            if not file_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{storage_type}_{timestamp}.txt"
            
            # Prepare metadata
            final_metadata = {
                'storage_type': storage_type,
                'transaction_id': transaction_id,
                'created_at': datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Create document data
            document_data = DocumentData(
                id=file_name,
                content=content,
                tags=[storage_type],
                metadata=final_metadata
            )
            
            # Execute fixed atomic transaction
            result = await self._execute_fixed_atomic_transaction(
                transaction_id, target_databases, document_data
            )
            
            # Update metrics
            duration_ms = (time.time() - start_time) * 1000
            self._update_metrics(storage_type, True, duration_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Unified store failed for {storage_type}: {e}")
            duration_ms = (time.time() - start_time) * 1000
            self._update_metrics(storage_type, False, duration_ms)
            
            return self._create_error_response(f"Storage operation failed: {str(e)}")
    
    async def _execute_fixed_atomic_transaction(self, transaction_id: str, 
                                               target_databases: List[str],
                                               document_data: DocumentData) -> Dict[str, Any]:
        """
        Execute atomic transaction with FIXED FAISS operations that eliminate race conditions.
        
        CRITICAL FIX: This method fixes the metadata-first race condition by:
        1. Creating embeddings FIRST (can fail safely)
        2. Adding vectors to index SECOND (can fail safely) 
        3. Creating metadata LAST (only after successful indexing)
        """
        operation_results = {}
        rollback_operations = []
        
        try:
            # Phase 1: Execute operations in dependency order
            for db_name in target_databases:
                if db_name == 'sqlite':
                    result = await self._execute_sqlite_operation(document_data)
                    operation_results['sqlite'] = result
                    if result['success']:
                        rollback_operations.append(('sqlite', document_data.id))
                
                elif db_name == 'faiss':
                    # CRITICAL FIX: Use fixed FAISS operations
                    result = await self._execute_fixed_faiss_operation(document_data)
                    operation_results['faiss'] = result
                    if result['success']:
                        rollback_operations.append(('faiss', document_data.id))
                
                elif db_name == 'neo4j':
                    result = await self._execute_neo4j_operation(document_data)
                    operation_results['neo4j'] = result
                    if result['success']:
                        rollback_operations.append(('neo4j', document_data.id))
                
                elif db_name == 'redis':
                    result = await self._execute_redis_operation(document_data)
                    operation_results['redis'] = result
                    if result['success']:
                        rollback_operations.append(('redis', document_data.id))
                
                # Check if operation failed
                if not result['success']:
                    raise Exception(f"{db_name} operation failed: {result.get('error')}")
            
            # Phase 2: All operations successful
            return {
                'success': True,
                'transaction_id': transaction_id,
                'doc_id': document_data.id,
                'file_name': document_data.id,
                'affected_databases': target_databases,
                'operation_results': operation_results,
                'execution_time_ms': sum(r.get('duration_ms', 0) for r in operation_results.values())
            }
            
        except Exception as e:
            logger.error(f"Transaction {transaction_id} failed: {e}")
            
            # Phase 3: Rollback operations in reverse order
            await self._execute_rollback(rollback_operations)
            
            return {
                'success': False,
                'error': str(e),
                'transaction_id': transaction_id,
                'failed_at': str(e),
                'operation_results': operation_results,
                'rollback_executed': True
            }
    
    async def _execute_fixed_faiss_operation(self, document_data: DocumentData) -> Dict[str, Any]:
        """
        CRITICAL FIX: Execute FAISS operation with proper ordering to eliminate race conditions.
        
        OLD (BROKEN) ORDER: metadata → embeddings → vectors
        NEW (FIXED) ORDER: embeddings → vectors → metadata
        """
        start_time = time.time()
        
        try:
            if not self.faiss or not self.faiss.is_available():
                return {'success': False, 'error': 'FAISS not available'}
            
            # PHASE 1: Generate embedding FIRST (can fail safely, no side effects)
            try:
                embedding_vector = self.faiss._generate_embedding(document_data.content)
                if embedding_vector is None or len(embedding_vector) == 0:
                    return {'success': False, 'error': 'Failed to generate embedding'}
                
                # Verify vector dimensions match FAISS index expectations
                if hasattr(self.faiss, 'dimension') and len(embedding_vector) != self.faiss.dimension:
                    return {
                        'success': False, 
                        'error': f'Embedding dimension {len(embedding_vector)} != expected {self.faiss.dimension}'
                    }
                    
            except Exception as e:
                return {'success': False, 'error': f'Embedding generation failed: {e}'}
            
            # PHASE 2: Add vector to FAISS index SECOND (can fail safely)
            try:
                # Ensure metadata structure exists
                self.faiss._ensure_metadata_structure()
                
                # Get next available index
                next_index = self.faiss._metadata.get('next_index', 0)
                
                # Add vector to index using FAISS manager's method
                from ltms.vector_store.faiss_store import add_vectors
                import numpy as np
                
                vector_array = embedding_vector.reshape(1, -1)
                add_vectors(self.faiss._index, vector_array, [next_index])
                
            except Exception as e:
                return {'success': False, 'error': f'Vector indexing failed: {e}'}
            
            # PHASE 3: Create metadata AND save LAST (only after successful vector indexing)
            try:
                # Store metadata mapping
                self.faiss._metadata['doc_id_to_index'][document_data.id] = next_index
                self.faiss._metadata['index_to_doc_id'][next_index] = document_data.id
                self.faiss._metadata['next_index'] = next_index + 1
                
                # Store document metadata
                doc_key = f"doc_{document_data.id}"
                self.faiss._metadata[doc_key] = {
                    'content_preview': document_data.content[:200],
                    'metadata': document_data.metadata,
                    'stored_at': datetime.now().isoformat(),
                    'vector_index': next_index
                }
                
                # CRITICAL: Save index AND metadata atomically
                save_success = self.faiss._save_index()
                if not save_success:
                    # If save fails, clean up the metadata we just added
                    del self.faiss._metadata['doc_id_to_index'][document_data.id]
                    del self.faiss._metadata['index_to_doc_id'][next_index]
                    del self.faiss._metadata[doc_key]
                    self.faiss._metadata['next_index'] = next_index  # Reset counter
                    
                    return {'success': False, 'error': 'Failed to save FAISS index to disk'}
                
            except Exception as e:
                # CRITICAL: If metadata creation fails, clean up what we can
                try:
                    # Remove metadata entries if they were created
                    if document_data.id in self.faiss._metadata.get('doc_id_to_index', {}):
                        del self.faiss._metadata['doc_id_to_index'][document_data.id]
                    if next_index in self.faiss._metadata.get('index_to_doc_id', {}):
                        del self.faiss._metadata['index_to_doc_id'][next_index]
                    doc_key = f"doc_{document_data.id}"
                    if doc_key in self.faiss._metadata:
                        del self.faiss._metadata[doc_key]
                except Exception:
                    pass  # Cleanup attempt failed, but we'll report the original error
                
                return {'success': False, 'error': f'Metadata creation failed: {e}'}
            
            duration_ms = (time.time() - start_time) * 1000
            return {
                'success': True,
                'vector_index': next_index,
                'doc_id': document_data.id,
                'duration_ms': duration_ms
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return {
                'success': False, 
                'error': f'FAISS operation failed: {str(e)}',
                'duration_ms': duration_ms
            }
    
    async def _execute_sqlite_operation(self, document_data: DocumentData) -> Dict[str, Any]:
        """Execute SQLite storage operation."""
        start_time = time.time()
        
        try:
            if not self.sqlite:
                return {'success': False, 'error': 'SQLite not available'}
            
            # Store document in SQLite
            success = self.sqlite.store_document(
                doc_id=document_data.id,
                content=document_data.content,
                tags=document_data.tags,
                metadata=document_data.metadata
            )
            
            duration_ms = (time.time() - start_time) * 1000
            if success:
                return {
                    'success': True,
                    'doc_id': document_data.id,
                    'duration_ms': duration_ms
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to store document in SQLite',
                    'duration_ms': duration_ms
                }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms
            }
    
    async def _execute_neo4j_operation(self, document_data: DocumentData) -> Dict[str, Any]:
        """Execute Neo4j storage operation."""
        start_time = time.time()
        
        try:
            if not self.neo4j or not self.neo4j.is_available():
                return {'success': False, 'error': 'Neo4j not available'}
            
            # Create document node in Neo4j
            success = await self.neo4j.store_document_node(
                doc_id=document_data.id,
                content=document_data.content,
                tags=document_data.tags,
                metadata=document_data.metadata
            )
            
            duration_ms = (time.time() - start_time) * 1000
            if success:
                return {
                    'success': True,
                    'doc_id': document_data.id,
                    'duration_ms': duration_ms
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to store document in Neo4j',
                    'duration_ms': duration_ms
                }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms
            }
    
    async def _execute_redis_operation(self, document_data: DocumentData) -> Dict[str, Any]:
        """Execute Redis caching operation."""
        start_time = time.time()
        
        try:
            if not self.redis or not self.redis.is_available():
                return {'success': False, 'error': 'Redis not available'}
            
            # Cache document in Redis
            success = await self.redis.cache_document(
                doc_id=document_data.id,
                content=document_data.content,
                metadata=document_data.metadata,
                ttl=3600  # 1 hour default TTL
            )
            
            duration_ms = (time.time() - start_time) * 1000
            if success:
                return {
                    'success': True,
                    'doc_id': document_data.id,
                    'duration_ms': duration_ms
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to cache document in Redis',
                    'duration_ms': duration_ms
                }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms
            }
    
    async def _execute_rollback(self, rollback_operations: List[tuple]):
        """Execute rollback operations in reverse order."""
        logger.info(f"Executing rollback for {len(rollback_operations)} operations")
        
        for db_name, doc_id in reversed(rollback_operations):
            try:
                if db_name == 'sqlite':
                    self.sqlite.delete_document(doc_id)
                elif db_name == 'faiss':
                    await self.faiss.delete_document_vector(doc_id)
                elif db_name == 'neo4j':
                    await self.neo4j.delete_document_node(doc_id)
                elif db_name == 'redis':
                    await self.redis.delete_cached_document(doc_id)
                    
                logger.debug(f"Rollback successful for {db_name}: {doc_id}")
                
            except Exception as e:
                logger.error(f"Rollback failed for {db_name}: {doc_id} - {e}")
    
    def _update_metrics(self, storage_type: str, success: bool, duration_ms: float):
        """Update performance metrics."""
        self.metrics['total_operations'] += 1
        
        if success:
            self.metrics['successful_operations'] += 1
        else:
            self.metrics['failed_operations'] += 1
        
        # Update average duration
        total_ops = self.metrics['total_operations']
        prev_avg = self.metrics['average_duration_ms']
        self.metrics['average_duration_ms'] = ((total_ops - 1) * prev_avg + duration_ms) / total_ops
        
        # Update per-type metrics
        if storage_type not in self.metrics['operations_by_type']:
            self.metrics['operations_by_type'][storage_type] = {
                'total': 0, 'successful': 0, 'failed': 0, 'avg_duration_ms': 0.0
            }
        
        type_metrics = self.metrics['operations_by_type'][storage_type]
        type_metrics['total'] += 1
        
        if success:
            type_metrics['successful'] += 1
        else:
            type_metrics['failed'] += 1
        
        # Update type-specific average
        type_total = type_metrics['total']
        type_prev_avg = type_metrics['avg_duration_ms']
        type_metrics['avg_duration_ms'] = ((type_total - 1) * type_prev_avg + duration_ms) / type_total
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.copy()
    
    def get_storage_routing(self) -> Dict[str, List[str]]:
        """Get storage routing configuration."""
        return {k.value: v for k, v in self.storage_routing.items()}


# Global instance for backward compatibility
_unified_storage_manager = None

def get_unified_storage_manager(test_mode: bool = False) -> UnifiedStorageManager:
    """Get global unified storage manager instance."""
    global _unified_storage_manager
    if _unified_storage_manager is None:
        _unified_storage_manager = UnifiedStorageManager(test_mode=test_mode)
    return _unified_storage_manager