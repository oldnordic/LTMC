"""
Connection Pooling Manager for LTMC MCP Server.

This module provides high-performance connection pooling for database connections,
Redis connections, and Neo4j connections to support high concurrency workloads.

Performance Targets:
- Support 100+ concurrent requests
- <1ms connection acquisition time
- Automatic connection health monitoring
- Graceful degradation under load
"""

import asyncio
import logging
import sqlite3
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Dict, Any, Optional, AsyncIterator, Iterator
from queue import Queue, Empty
from threading import Lock, RLock
import redis.asyncio as redis
from neo4j import GraphDatabase, BoltDriver

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for connection pools."""
    min_connections: int = 2
    max_connections: int = 20
    connection_timeout_ms: int = 5000
    idle_timeout_ms: int = 60000
    health_check_interval_ms: int = 30000
    max_retries: int = 3


@dataclass
class PoolMetrics:
    """Connection pool performance metrics."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    acquired_count: int = 0
    released_count: int = 0
    creation_errors: int = 0
    timeout_errors: int = 0
    avg_acquisition_time_ms: float = 0.0
    max_acquisition_time_ms: float = 0.0


class DatabaseConnectionPool:
    """High-performance SQLite connection pool with thread safety."""
    
    def __init__(self, db_path: str, pool_config: PoolConfig = None):
        self.db_path = db_path
        self.config = pool_config or PoolConfig()
        self._pool = Queue(maxsize=self.config.max_connections)
        self._lock = RLock()
        self._metrics = PoolMetrics()
        self._acquisition_times = []
        self._initialized = False
        
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimizations."""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.connection_timeout_ms / 1000.0,
                check_same_thread=False
            )
            # SQLite optimizations for performance
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=memory")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            with self._lock:
                self._metrics.creation_errors += 1
            logger.error(f"Failed to create database connection: {e}")
            raise
    
    def initialize_pool(self) -> None:
        """Initialize the connection pool with minimum connections."""
        if self._initialized:
            return
            
        with self._lock:
            for _ in range(self.config.min_connections):
                try:
                    conn = self._create_connection()
                    self._pool.put_nowait(conn)
                    self._metrics.total_connections += 1
                except Exception as e:
                    logger.error(f"Failed to initialize pool connection: {e}")
                    break
            self._initialized = True
            logger.info(f"Database pool initialized with {self._metrics.total_connections} connections")
    
    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Get a connection from the pool with automatic return."""
        start_time = time.perf_counter()
        conn = None
        
        try:
            # Try to get connection from pool
            try:
                conn = self._pool.get_nowait()
                with self._lock:
                    self._metrics.active_connections += 1
                    self._metrics.acquired_count += 1
            except Empty:
                # Pool empty, create new connection if under limit
                with self._lock:
                    if self._metrics.total_connections < self.config.max_connections:
                        conn = self._create_connection()
                        self._metrics.total_connections += 1
                        self._metrics.active_connections += 1
                        self._metrics.acquired_count += 1
                    else:
                        self._metrics.timeout_errors += 1
                        raise Exception("Connection pool exhausted")
            
            # Record acquisition time
            acquisition_time = (time.perf_counter() - start_time) * 1000
            self._acquisition_times.append(acquisition_time)
            with self._lock:
                self._metrics.avg_acquisition_time_ms = sum(self._acquisition_times[-100:]) / min(len(self._acquisition_times), 100)
                self._metrics.max_acquisition_time_ms = max(self._metrics.max_acquisition_time_ms, acquisition_time)
            
            yield conn
            
        finally:
            if conn:
                # Return connection to pool
                try:
                    self._pool.put_nowait(conn)
                    with self._lock:
                        self._metrics.active_connections -= 1
                        self._metrics.released_count += 1
                except Exception as e:
                    logger.warning(f"Failed to return connection to pool: {e}")
                    # Connection might be corrupted, don't return to pool
                    with self._lock:
                        self._metrics.total_connections -= 1
                        self._metrics.active_connections -= 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current pool metrics."""
        with self._lock:
            return {
                "total_connections": self._metrics.total_connections,
                "active_connections": self._metrics.active_connections,
                "idle_connections": self._pool.qsize(),
                "acquired_count": self._metrics.acquired_count,
                "released_count": self._metrics.released_count,
                "creation_errors": self._metrics.creation_errors,
                "timeout_errors": self._metrics.timeout_errors,
                "avg_acquisition_time_ms": round(self._metrics.avg_acquisition_time_ms, 2),
                "max_acquisition_time_ms": round(self._metrics.max_acquisition_time_ms, 2),
                "pool_utilization": (self._metrics.active_connections / self.config.max_connections) * 100
            }
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except Empty:
                    break
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            self._metrics.total_connections = 0
            self._metrics.active_connections = 0


class AsyncRedisConnectionPool:
    """High-performance async Redis connection pool."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", pool_config: PoolConfig = None):
        self.redis_url = redis_url
        self.config = pool_config or PoolConfig()
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._metrics = PoolMetrics()
        self._lock = asyncio.Lock()
        self._acquisition_times = []
    
    async def initialize_pool(self) -> None:
        """Initialize the async Redis connection pool."""
        if self._pool is not None:
            return
            
        try:
            self._pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.connection_timeout_ms / 1000.0,
                socket_connect_timeout=self.config.connection_timeout_ms / 1000.0,
                retry_on_timeout=True,
                health_check_interval=self.config.health_check_interval_ms / 1000.0
            )
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("Redis connection pool initialized successfully")
            
        except Exception as e:
            async with self._lock:
                self._metrics.creation_errors += 1
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[redis.Redis]:
        """Get a Redis connection from the pool."""
        if not self._client:
            await self.initialize_pool()
        
        start_time = time.perf_counter()
        
        try:
            async with self._lock:
                self._metrics.active_connections += 1
                self._metrics.acquired_count += 1
            
            yield self._client
            
        except Exception as e:
            async with self._lock:
                self._metrics.timeout_errors += 1
            logger.error(f"Redis connection error: {e}")
            raise
        finally:
            # Record acquisition time
            acquisition_time = (time.perf_counter() - start_time) * 1000
            self._acquisition_times.append(acquisition_time)
            async with self._lock:
                self._metrics.active_connections -= 1
                self._metrics.released_count += 1
                self._metrics.avg_acquisition_time_ms = sum(self._acquisition_times[-100:]) / min(len(self._acquisition_times), 100)
                self._metrics.max_acquisition_time_ms = max(self._metrics.max_acquisition_time_ms, acquisition_time)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current pool metrics."""
        async with self._lock:
            pool_info = {}
            if self._pool:
                pool_info = {
                    "created_connections": self._pool.created_connections,
                    "available_connections": len(self._pool._available_connections),
                    "in_use_connections": len(self._pool._in_use_connections)
                }
            
            return {
                "pool_info": pool_info,
                "active_connections": self._metrics.active_connections,
                "acquired_count": self._metrics.acquired_count,
                "released_count": self._metrics.released_count,
                "creation_errors": self._metrics.creation_errors,
                "timeout_errors": self._metrics.timeout_errors,
                "avg_acquisition_time_ms": round(self._metrics.avg_acquisition_time_ms, 2),
                "max_acquisition_time_ms": round(self._metrics.max_acquisition_time_ms, 2)
            }
    
    async def close_pool(self) -> None:
        """Close the Redis connection pool."""
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None


class Neo4jConnectionPool:
    """High-performance Neo4j connection pool."""
    
    def __init__(self, uri: str, user: str, password: str, pool_config: PoolConfig = None):
        self.uri = uri
        self.user = user
        self.password = password
        self.config = pool_config or PoolConfig()
        self._driver: Optional[BoltDriver] = None
        self._metrics = PoolMetrics()
        self._lock = Lock()
        self._acquisition_times = []
    
    def initialize_pool(self) -> None:
        """Initialize the Neo4j connection pool."""
        if self._driver is not None:
            return
            
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=self.config.idle_timeout_ms,
                max_connection_pool_size=self.config.max_connections,
                connection_timeout=self.config.connection_timeout_ms / 1000.0
            )
            
            # Test connection
            with self._driver.session() as session:
                session.run("RETURN 1 as test").single()
            
            logger.info("Neo4j connection pool initialized successfully")
            
        except Exception as e:
            with self._lock:
                self._metrics.creation_errors += 1
            logger.error(f"Failed to initialize Neo4j pool: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get a Neo4j session from the pool."""
        if not self._driver:
            self.initialize_pool()
        
        start_time = time.perf_counter()
        
        try:
            with self._lock:
                self._metrics.active_connections += 1
                self._metrics.acquired_count += 1
            
            with self._driver.session() as session:
                yield session
                
        except Exception as e:
            with self._lock:
                self._metrics.timeout_errors += 1
            logger.error(f"Neo4j session error: {e}")
            raise
        finally:
            # Record acquisition time
            acquisition_time = (time.perf_counter() - start_time) * 1000
            self._acquisition_times.append(acquisition_time)
            with self._lock:
                self._metrics.active_connections -= 1
                self._metrics.released_count += 1
                self._metrics.avg_acquisition_time_ms = sum(self._acquisition_times[-100:]) / min(len(self._acquisition_times), 100)
                self._metrics.max_acquisition_time_ms = max(self._metrics.max_acquisition_time_ms, acquisition_time)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current pool metrics."""
        with self._lock:
            return {
                "active_connections": self._metrics.active_connections,
                "acquired_count": self._metrics.acquired_count,
                "released_count": self._metrics.released_count,
                "creation_errors": self._metrics.creation_errors,
                "timeout_errors": self._metrics.timeout_errors,
                "avg_acquisition_time_ms": round(self._metrics.avg_acquisition_time_ms, 2),
                "max_acquisition_time_ms": round(self._metrics.max_acquisition_time_ms, 2)
            }
    
    def close_pool(self) -> None:
        """Close the Neo4j connection pool."""
        if self._driver:
            self._driver.close()
            self._driver = None


class UnifiedConnectionManager:
    """Unified connection pool manager for all database types."""
    
    def __init__(self, 
                 db_path: str, 
                 redis_url: str = "redis://localhost:6379/0",
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "kwe_password",
                 pool_config: PoolConfig = None):
        self.pool_config = pool_config or PoolConfig()
        
        # Initialize all pools
        self.db_pool = DatabaseConnectionPool(db_path, self.pool_config)
        self.redis_pool = AsyncRedisConnectionPool(redis_url, self.pool_config)
        self.neo4j_pool = Neo4jConnectionPool(neo4j_uri, neo4j_user, neo4j_password, self.pool_config)
        
        self._initialized = False
    
    def initialize_all_pools(self) -> None:
        """Initialize all connection pools."""
        if self._initialized:
            return
            
        self.db_pool.initialize_pool()
        self.neo4j_pool.initialize_pool()
        # Redis pool is initialized on first use (async)
        
        self._initialized = True
        logger.info("All connection pools initialized successfully")
    
    async def initialize_async_pools(self) -> None:
        """Initialize async connection pools."""
        await self.redis_pool.initialize_pool()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all connection pools."""
        return {
            "database": self.db_pool.get_metrics(),
            "redis": asyncio.run(self.redis_pool.get_metrics()) if self.redis_pool._pool else {},
            "neo4j": self.neo4j_pool.get_metrics(),
            "pool_config": {
                "min_connections": self.pool_config.min_connections,
                "max_connections": self.pool_config.max_connections,
                "connection_timeout_ms": self.pool_config.connection_timeout_ms,
                "idle_timeout_ms": self.pool_config.idle_timeout_ms
            }
        }
    
    def close_all_pools(self) -> None:
        """Close all connection pools gracefully."""
        self.db_pool.close_all()
        self.neo4j_pool.close_pool()
        asyncio.run(self.redis_pool.close_pool())
        logger.info("All connection pools closed")


# Global connection manager instance
_connection_manager: Optional[UnifiedConnectionManager] = None
_connection_manager_lock = Lock()


def get_connection_manager(
    db_path: str = None,
    redis_url: str = "redis://localhost:6379/0",
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "kwe_password",
    pool_config: PoolConfig = None
) -> UnifiedConnectionManager:
    """Get or create the global connection manager instance."""
    global _connection_manager
    
    with _connection_manager_lock:
        if _connection_manager is None:
            if db_path is None:
                from ltms.config import config
                db_path = config.get_db_path()
            
            _connection_manager = UnifiedConnectionManager(
                db_path=db_path,
                redis_url=redis_url,
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password,
                pool_config=pool_config
            )
            _connection_manager.initialize_all_pools()
        
        return _connection_manager


def shutdown_connection_manager() -> None:
    """Shutdown the global connection manager."""
    global _connection_manager
    
    with _connection_manager_lock:
        if _connection_manager:
            _connection_manager.close_all_pools()
            _connection_manager = None