"""
Centralized database connection management for LTMC MCP tools.
Provides singleton access to all database systems used by LTMC.

File: ltms/tools/core/database_manager.py
Lines: ~280 (under 300 limit)
Purpose: Centralized database connection management
"""

import logging
import sqlite3
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import asyncio
from threading import Lock

# Import existing LTMC database managers
from ltms.config.json_config_loader import get_config
from ltms.database.faiss_manager import FAISSManager
from ltms.database.neo4j_manager import Neo4jManager
from ltms.services.redis_service import get_redis_manager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database connection management for MCP tools.
    
    Provides singleton access to SQLite, Redis, Neo4j, and FAISS connections
    with proper connection pooling and resource management.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._config = get_config()
            self._sqlite_conn: Optional[sqlite3.Connection] = None
            self._redis_manager = None
            self._neo4j_manager: Optional[Neo4jManager] = None
            self._faiss_manager: Optional[FAISSManager] = None
            self._connection_lock = Lock()
            self._initialized = True
            logger.info("DatabaseManager singleton initialized")
    
    @property
    def sqlite(self) -> sqlite3.Connection:
        """Get or create SQLite connection with proper configuration."""
        if self._sqlite_conn is None:
            with self._connection_lock:
                if self._sqlite_conn is None:
                    db_path = self._config.get_db_path()
                    # Ensure database directory exists
                    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                    
                    self._sqlite_conn = sqlite3.connect(
                        db_path,
                        check_same_thread=False,
                        timeout=30.0
                    )
                    self._sqlite_conn.row_factory = sqlite3.Row
                    
                    # Enable WAL mode for better concurrency
                    self._sqlite_conn.execute("PRAGMA journal_mode=WAL")
                    self._sqlite_conn.execute("PRAGMA synchronous=NORMAL")
                    self._sqlite_conn.execute("PRAGMA cache_size=10000")
                    self._sqlite_conn.execute("PRAGMA foreign_keys=ON")
                    
                    logger.info(f"SQLite connection established: {db_path}")
        
        return self._sqlite_conn
    
    @property
    def redis(self):
        """Get or create Redis manager using existing service."""
        if self._redis_manager is None:
            with self._connection_lock:
                if self._redis_manager is None:
                    try:
                        # get_redis_manager() is async, need to handle it properly
                        import asyncio
                        # Always use RedisManager directly for proper interface
                        from ltms.database.redis_manager import RedisManager
                        redis_config = {
                            'host': self._config.redis_host,
                            'port': self._config.redis_port, 
                            'db': self._config.redis_db,
                            'password': self._config.redis_password
                        }
                        self._redis_manager = RedisManager(redis_config)
                        logger.info("Redis manager connection established")
                    except Exception as e:
                        logger.error(f"Failed to initialize Redis manager: {e}")
                        # Return None to indicate Redis unavailable
                        return None
        
        return self._redis_manager
    
    @property
    def neo4j(self) -> Neo4jManager:
        """Get or create Neo4j manager connection."""
        if self._neo4j_manager is None:
            with self._connection_lock:
                if self._neo4j_manager is None:
                    try:
                        self._neo4j_manager = Neo4jManager()
                        logger.info("Neo4j manager connection established")
                    except Exception as e:
                        logger.error(f"Failed to initialize Neo4j manager: {e}")
                        # Return test mode manager if connection fails
                        self._neo4j_manager = Neo4jManager(test_mode=True)
        
        return self._neo4j_manager
    
    @property
    def faiss(self) -> FAISSManager:
        """Get or create FAISS manager connection."""
        if self._faiss_manager is None:
            with self._connection_lock:
                if self._faiss_manager is None:
                    try:
                        self._faiss_manager = FAISSManager()
                        logger.info("FAISS manager connection established")
                    except Exception as e:
                        logger.error(f"Failed to initialize FAISS manager: {e}")
                        # Return None instead of test mode to prevent issues
                        self._faiss_manager = None
                        raise
        
        return self._faiss_manager
    
    def execute_sqlite(self, query: str, params: tuple = None, fetch: str = None) -> Any:
        """Execute SQLite query with proper error handling.
        
        Args:
            query: SQL query to execute
            params: Query parameters tuple
            fetch: 'all', 'one', or None (for non-select queries)
            
        Returns:
            Query results based on fetch parameter
        """
        try:
            cursor = self.sqlite.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch == 'all':
                return cursor.fetchall()
            elif fetch == 'one':
                return cursor.fetchone()
            else:
                self.sqlite.commit()
                return cursor.rowcount
                
        except sqlite3.Error as e:
            logger.error(f"SQLite execution error: {e}")
            self.sqlite.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in SQLite execution: {e}")
            self.sqlite.rollback()
            raise
    
    async def execute_redis_operation(self, operation: str, *args, **kwargs) -> Any:
        """Execute Redis operation with proper error handling.
        
        Args:
            operation: Redis operation name (get, set, hget, etc.)
            *args, **kwargs: Operation arguments
            
        Returns:
            Redis operation result
        """
        try:
            redis_manager = self.redis
            if hasattr(redis_manager, 'get_client'):
                redis_client = redis_manager.get_client()
            else:
                # Direct access if it's already a client
                redis_client = redis_manager
            
            operation_func = getattr(redis_client, operation)
            
            if asyncio.iscoroutinefunction(operation_func):
                return await operation_func(*args, **kwargs)
            else:
                return operation_func(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"Redis operation '{operation}' failed: {e}")
            raise
    
    def is_available(self) -> Dict[str, bool]:
        """Check availability of all database systems.
        
        Returns:
            Dictionary of system availability status
        """
        status = {}
        
        # SQLite availability
        try:
            self.sqlite.execute("SELECT 1")
            status['sqlite'] = True
        except Exception as e:
            logger.error(f"SQLite unavailable: {e}")
            status['sqlite'] = False
        
        # Redis availability - use synchronous check to avoid async/sync mismatch
        try:
            redis_manager = self.redis
            if hasattr(redis_manager, 'is_available'):
                # Use the is_available method if it exists (synchronous)
                status['redis'] = redis_manager.is_available()
            else:
                # Fallback: assume available if manager exists and has connection_manager
                status['redis'] = (redis_manager is not None and 
                                 hasattr(redis_manager, '_connection_manager') and
                                 redis_manager._connection_manager is not None)
        except Exception as e:
            logger.error(f"Redis unavailable: {e}")
            status['redis'] = False
        
        # Neo4j availability
        try:
            status['neo4j'] = self.neo4j.is_available()
        except Exception as e:
            logger.error(f"Neo4j unavailable: {e}")
            status['neo4j'] = False
        
        # FAISS availability
        try:
            status['faiss'] = self.faiss is not None and self.faiss.is_available()
        except Exception as e:
            logger.error(f"FAISS unavailable: {e}")
            status['faiss'] = False
        
        return status
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all database systems.
        
        Returns:
            Health status dictionary with detailed information
        """
        availability = self.is_available()
        
        health_status = {
            'overall': all(availability.values()),
            'systems': availability,
            'details': {}
        }
        
        # Get detailed status for each system
        if availability['sqlite']:
            try:
                cursor = self.sqlite.cursor()
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                health_status['details']['sqlite'] = {
                    'status': 'healthy',
                    'integrity': integrity,
                    'path': self._config.get_db_path()
                }
            except Exception as e:
                health_status['details']['sqlite'] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        if availability['neo4j']:
            health_status['details']['neo4j'] = self.neo4j.get_health_status()
        
        if availability['redis']:
            try:
                redis_manager = self.redis
                if hasattr(redis_manager, 'get_client'):
                    redis_client = redis_manager.get_client()
                    info = redis_client.info()
                    health_status['details']['redis'] = {
                        'status': 'healthy',
                        'memory_usage': info.get('used_memory_human', 'unknown'),
                        'connections': info.get('connected_clients', 'unknown')
                    }
                else:
                    health_status['details']['redis'] = {
                        'status': 'healthy',
                        'note': 'Redis manager available but detailed info not accessible'
                    }
            except Exception as e:
                health_status['details']['redis'] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        if availability['faiss'] and self.faiss:
            health_status['details']['faiss'] = {
                'status': 'healthy',
                'index_path': str(self.faiss.index_path) if hasattr(self.faiss, 'index_path') else 'unknown'
            }
        
        return health_status
    
    def close_all(self):
        """Close all database connections properly."""
        if self._sqlite_conn:
            try:
                self._sqlite_conn.close()
                self._sqlite_conn = None
                logger.info("SQLite connection closed")
            except Exception as e:
                logger.error(f"Error closing SQLite connection: {e}")
        
        if self._neo4j_manager:
            try:
                self._neo4j_manager.close()
                self._neo4j_manager = None
                logger.info("Neo4j connection closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
        
        # Redis manager handles its own connection pooling
        if self._redis_manager:
            self._redis_manager = None
            logger.info("Redis manager reference cleared")
        
        # FAISS is file-based, no connection to close
        if self._faiss_manager:
            self._faiss_manager = None
            logger.info("FAISS manager reference cleared")
    
    def __del__(self):
        """Cleanup connections on object deletion."""
        try:
            self.close_all()
        except Exception:
            pass  # Suppress errors during cleanup