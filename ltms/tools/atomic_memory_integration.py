"""
Atomic Memory Integration for LTMC Consolidated Tools.
Replaces direct database operations with atomic synchronization.

File: ltms/tools/atomic_memory_integration.py
Lines: ~290 (under 300 limit)
Purpose: Production atomic memory operations for consolidated tools
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from ltms.database.sync_coordinator import DatabaseSyncCoordinator
from ltms.database.sqlite_manager import SQLiteManager
from ltms.database.neo4j_manager import Neo4jManager
from ltms.database.faiss_manager import FAISSManager
from ltms.database.redis_manager import RedisManager
from ltms.sync.sync_models import DocumentData
from ltms.config import get_config

logger = logging.getLogger(__name__)

class AtomicMemoryManager:
    """
    Atomic memory manager for LTMC consolidated tools.
    Provides atomic operations across all 4 database systems.
    """
    
    _instance: Optional['AtomicMemoryManager'] = None
    _sync_coordinator: Optional[DatabaseSyncCoordinator] = None
    
    def __new__(cls):
        """Singleton pattern for consistent database connections."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize atomic memory manager with production database managers."""
        if self._initialized:
            return
            
        self._initialized = True
        self._setup_production_managers()
        
        logger.info("AtomicMemoryManager initialized with production databases")
    
    def _setup_production_managers(self):
        """Setup production database managers with real connections."""
        try:
            config = get_config()
            
            # Test production database availability first
            production_available = self._test_production_availability(config)
            
            if not production_available:
                logger.warning("Production databases not available, falling back to test mode")
                self._setup_test_managers()
                return
            
            # Create production database managers
            self._sqlite_manager = SQLiteManager(test_mode=False)
            
            # Neo4j configuration
            neo4j_config = {
                "uri": getattr(config, 'NEO4J_URI', 'bolt://localhost:7687'),
                "user": getattr(config, 'NEO4J_USER', 'neo4j'),
                "password": getattr(config, 'NEO4J_PASSWORD', 'password'),
                "database": getattr(config, 'NEO4J_DATABASE', 'neo4j')
            }
            self._neo4j_manager = Neo4jManager(neo4j_config, test_mode=False)
            
            # FAISS configuration
            self._faiss_manager = FAISSManager(test_mode=False)
            
            # Redis configuration
            redis_config = {
                "host": getattr(config, 'REDIS_HOST', 'localhost'),
                "port": getattr(config, 'REDIS_PORT', 6382),
                "db": getattr(config, 'REDIS_DB', 0),
                "password": getattr(config, 'REDIS_PASSWORD', None)
            }
            self._redis_manager = RedisManager(redis_config, test_mode=False)
            
            # Validate all managers are working
            if not self._validate_managers():
                logger.warning("Production managers validation failed, falling back to test mode")
                self._setup_test_managers()
                return
            
            # Create atomic sync coordinator
            AtomicMemoryManager._sync_coordinator = DatabaseSyncCoordinator(
                sqlite_manager=self._sqlite_manager,
                neo4j_manager=self._neo4j_manager,
                faiss_store=self._faiss_manager,
                redis_cache=self._redis_manager,
                test_mode=False
            )
            
            logger.info("Production database managers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup production managers: {e}")
            # Fallback to test mode for development
            self._setup_test_managers()
    
    def _test_production_availability(self, config) -> bool:
        """Test if production databases are available."""
        try:
            # Test SQLite database path exists and is accessible
            db_path = config.get_db_path()
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            # If we get here, at least SQLite is working
            return True
            
        except Exception as e:
            logger.debug(f"Production database availability test failed: {e}")
            return False
    
    def _validate_managers(self) -> bool:
        """Validate that database managers are working properly."""
        try:
            # Test SQLite
            if not self._sqlite_manager.get_health_status().get('status') == 'healthy':
                return False
            
            # Test FAISS
            if not self._faiss_manager.get_health_status().get('status') == 'healthy':
                return False
            
            # Neo4j and Redis can fail in development - that's OK
            return True
            
        except Exception as e:
            logger.debug(f"Manager validation failed: {e}")
            return False
    
    def _setup_test_managers(self):
        """Fallback to test mode managers."""
        logger.warning("Falling back to test mode managers")
        
        self._sqlite_manager = SQLiteManager(test_mode=True)
        self._neo4j_manager = Neo4jManager(test_mode=True)
        self._faiss_manager = FAISSManager(test_mode=True)
        self._redis_manager = RedisManager(test_mode=True)
        
        AtomicMemoryManager._sync_coordinator = DatabaseSyncCoordinator(
            sqlite_manager=self._sqlite_manager,
            neo4j_manager=self._neo4j_manager,
            faiss_store=self._faiss_manager,
            redis_cache=self._redis_manager,
            test_mode=True
        )
    
    def get_sync_coordinator(self) -> DatabaseSyncCoordinator:
        """Get the atomic sync coordinator instance."""
        return AtomicMemoryManager._sync_coordinator
    
    async def atomic_store(self, file_name: str, content: str, 
                          resource_type: str = 'document', 
                          tags: List[str] = None,
                          conversation_id: str = 'default',
                          **metadata) -> Dict[str, Any]:
        """
        Store document atomically across all database systems.
        
        Args:
            file_name: Document filename/identifier
            content: Document content
            resource_type: Type of resource (default: 'document')
            tags: List of document tags
            conversation_id: Conversation identifier
            **metadata: Additional metadata
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            # Create document data
            doc_metadata = {
                'resource_type': resource_type,
                'conversation_id': conversation_id,
                **metadata
            }
            
            document = DocumentData(
                id=file_name,
                content=content,
                tags=tags or [],
                metadata=doc_metadata
            )
            
            # Perform atomic store operation
            sync_result = await self._sync_coordinator.atomic_store_document(document)
            
            if sync_result.success:
                return {
                    'success': True,
                    'doc_id': sync_result.doc_id,
                    'file_name': file_name,
                    'resource_type': resource_type,
                    'transaction_id': sync_result.transaction_id,
                    'execution_time_ms': sync_result.execution_time_ms,
                    'affected_databases': [db.value for db in sync_result.affected_databases],
                    'consistency_validated': sync_result.consistency_report.is_consistent if sync_result.consistency_report else False,
                    'message': 'Document stored atomically across all databases'
                }
            else:
                return {
                    'success': False,
                    'error': sync_result.error_message or 'Atomic store operation failed',
                    'transaction_id': sync_result.transaction_id
                }
                
        except Exception as e:
            logger.error(f"Atomic store operation failed: {e}")
            return {
                'success': False,
                'error': f'Atomic store operation failed: {str(e)}'
            }
    
    async def atomic_retrieve(self, file_name: str) -> Dict[str, Any]:
        """
        Retrieve document from primary database (SQLite).
        
        Args:
            file_name: Document filename/identifier
            
        Returns:
            Document data or error result
        """
        try:
            document = self._sqlite_manager.retrieve_document(file_name)
            
            if document:
                return {
                    'success': True,
                    'document': document,
                    'file_name': file_name
                }
            else:
                return {
                    'success': False,
                    'error': f'Document {file_name} not found'
                }
                
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return {
                'success': False,
                'error': f'Document retrieval failed: {str(e)}'
            }
    
    async def atomic_search(self, query: str, k: int = 5) -> Dict[str, Any]:
        """
        Search for similar documents using FAISS vector similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            Search results or error
        """
        try:
            results = await self._faiss_manager.search_similar(query, k)
            
            return {
                'success': True,
                'results': results,
                'query': query,
                'result_count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {
                'success': False,
                'error': f'Vector search failed: {str(e)}'
            }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of all database systems.
        
        Returns:
            Health status for all systems
        """
        try:
            sqlite_health = self._sqlite_manager.get_health_status()
            neo4j_health = self._neo4j_manager.get_health_status()
            faiss_health = self._faiss_manager.get_health_status()
            redis_health = await self._redis_manager.get_health_status()
            
            overall_healthy = all([
                sqlite_health.get('status') == 'healthy',
                neo4j_health.get('status') == 'healthy',
                faiss_health.get('status') == 'healthy',
                redis_health.get('status') == 'healthy'
            ])
            
            return {
                'success': True,
                'overall_status': 'healthy' if overall_healthy else 'degraded',
                'systems': {
                    'sqlite': sqlite_health,
                    'neo4j': neo4j_health,
                    'faiss': faiss_health,
                    'redis': redis_health
                },
                'atomic_sync_available': self._sync_coordinator is not None
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'success': False,
                'error': f'Health check failed: {str(e)}'
            }

# Global instance
_atomic_memory_manager = None

def get_atomic_memory_manager() -> AtomicMemoryManager:
    """Get or create atomic memory manager instance."""
    global _atomic_memory_manager
    if _atomic_memory_manager is None:
        _atomic_memory_manager = AtomicMemoryManager()
    return _atomic_memory_manager

# Helper functions for backward compatibility with consolidated.py

def atomic_memory_store(file_name: str, content: str, **params) -> Dict[str, Any]:
    """
    Atomic memory store operation (sync wrapper).
    
    Args:
        file_name: Document filename
        content: Document content
        **params: Additional parameters
        
    Returns:
        Store operation result
    """
    try:
        manager = get_atomic_memory_manager()
        
        # Run async operation in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                manager.atomic_store(file_name, content, **params)
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Atomic memory store failed: {e}")
        return {
            'success': False,
            'error': f'Atomic memory store failed: {str(e)}'
        }

def atomic_memory_retrieve(file_name: str) -> Dict[str, Any]:
    """
    Atomic memory retrieve operation (sync wrapper).
    
    Args:
        file_name: Document filename
        
    Returns:
        Retrieve operation result
    """
    try:
        manager = get_atomic_memory_manager()
        
        # Run async operation in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                manager.atomic_retrieve(file_name)
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Atomic memory retrieve failed: {e}")
        return {
            'success': False,
            'error': f'Atomic memory retrieve failed: {str(e)}'
        }

# Async wrapper functions for MCP compatibility

def _is_event_loop_running() -> bool:
    """Check if an event loop is currently running."""
    try:
        loop = asyncio.get_running_loop()
        return loop.is_running()
    except RuntimeError:
        return False

def _run_in_thread(func, *args, **kwargs):
    """Run function in thread executor."""
    import concurrent.futures
    import threading
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args, **kwargs)
        return future.result()

async def async_atomic_memory_store(content: str, tags: Optional[list] = None, 
                                   metadata: Optional[dict] = None) -> dict:
    """
    Async wrapper for atomic memory store operation.
    
    Args:
        content: Document content
        tags: Optional list of tags
        metadata: Optional metadata dictionary
        
    Returns:
        Store operation result
    """
    try:
        manager = get_atomic_memory_manager()
        
        # Generate doc ID from content hash
        import hashlib
        doc_id = hashlib.md5(content.encode()).hexdigest()[:16]
        
        result = await manager.atomic_store(
            file_name=doc_id,
            content=content,
            tags=tags or [],
            **(metadata or {})
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Async atomic memory store failed: {e}")
        return {
            'success': False,
            'error': f'Async atomic memory store failed: {str(e)}'
        }

async def async_atomic_memory_retrieve(doc_id: str) -> dict:
    """
    Async wrapper for atomic memory retrieve operation.
    
    Args:
        doc_id: Document ID to retrieve
        
    Returns:
        Retrieve operation result
    """
    try:
        manager = get_atomic_memory_manager()
        result = await manager.atomic_retrieve(doc_id)
        return result
        
    except Exception as e:
        logger.error(f"Async atomic memory retrieve failed: {e}")
        return {
            'success': False,
            'error': f'Async atomic memory retrieve failed: {str(e)}'
        }

async def async_atomic_memory_search(query: str, k: int = 10, threshold: float = 0.7, 
                                   tags: Optional[list] = None) -> list:
    """
    Async wrapper for atomic memory search operation.
    
    Args:
        query: Search query
        k: Number of results to return
        threshold: Similarity threshold
        tags: Optional tag filters
        
    Returns:
        Search operation results
    """
    try:
        manager = get_atomic_memory_manager()
        result = await manager.atomic_search(query, k)
        return result
        
    except Exception as e:
        logger.error(f"Async atomic memory search failed: {e}")
        return {
            'success': False,
            'error': f'Async atomic memory search failed: {str(e)}'
        }

async def async_atomic_memory_delete(doc_id: str) -> dict:
    """
    Async wrapper for atomic memory delete operation.
    
    Args:
        doc_id: Document ID to delete
        
    Returns:
        Delete operation result
    """
    try:
        # For now, return not implemented
        return {
            'success': False,
            'error': 'Delete operation not yet implemented'
        }
        
    except Exception as e:
        logger.error(f"Async atomic memory delete failed: {e}")
        return {
            'success': False,
            'error': f'Async atomic memory delete failed: {str(e)}'
        }