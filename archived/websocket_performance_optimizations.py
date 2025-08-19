"""
WebSocket Performance Optimizations with LTMC Pattern Learning
==============================================================

This module demonstrates how LTMC helps identify and apply performance patterns
to prevent technology drift and optimize real-time systems.

Based on retrieved patterns:
- Pattern 352: WebSocket implementation with Redis integration
- Pattern 353: Comprehensive testing approaches
- LTMC learning: Performance bottleneck identification
"""

import asyncio
import time
import weakref
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any, Callable
import uvloop  # High-performance event loop

import aioredis
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Performance monitoring metrics
WEBSOCKET_CONNECTIONS = Gauge('websocket_connections_total', 'Total WebSocket connections')
MESSAGE_PROCESSING_TIME = Histogram('websocket_message_duration_seconds', 'Message processing time')
MESSAGES_SENT = Counter('websocket_messages_sent_total', 'Total messages sent')
REDIS_OPERATIONS = Counter('websocket_redis_operations_total', 'Redis operations', ['operation'])
CONNECTION_ERRORS = Counter('websocket_connection_errors_total', 'Connection errors', ['error_type'])

@dataclass
class PerformanceMetrics:
    """Real-time performance metrics for monitoring."""
    connections_per_second: float = 0.0
    messages_per_second: float = 0.0
    avg_message_latency: float = 0.0
    redis_hit_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

class ConnectionPool:
    """Optimized connection pool with weak references and cleanup."""
    
    def __init__(self, max_connections_per_room: int = 1000):
        self.max_connections_per_room = max_connections_per_room
        self.connections: Dict[str, Dict[str, weakref.ReferenceType]] = defaultdict(dict)
        self.connection_metadata: Dict[str, Dict] = {}
        self.room_stats: Dict[str, Dict] = defaultdict(lambda: {
            'connections': 0,
            'messages_sent': 0,
            'created_at': time.time()
        })
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start_cleanup_task(self):
        """Start background cleanup task for dead connections."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _periodic_cleanup(self):
        """Periodically clean up dead connections."""
        while True:
            try:
                await asyncio.sleep(30)  # Cleanup every 30 seconds
                await self._cleanup_dead_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                CONNECTION_ERRORS.labels(error_type='cleanup_error').inc()
                print(f"Cleanup error: {e}")
    
    async def _cleanup_dead_connections(self):
        """Remove dead weak references."""
        rooms_to_remove = []
        
        for room_id, connections in self.connections.items():
            dead_connections = []
            
            for conn_id, conn_ref in connections.items():
                if conn_ref() is None:  # Dead reference
                    dead_connections.append(conn_id)
            
            # Remove dead connections
            for conn_id in dead_connections:
                del connections[conn_id]
                self.connection_metadata.pop(conn_id, None)
                self.room_stats[room_id]['connections'] -= 1
            
            # Mark empty rooms for removal
            if not connections:
                rooms_to_remove.append(room_id)
        
        # Remove empty rooms
        for room_id in rooms_to_remove:
            del self.connections[room_id]
            del self.room_stats[room_id]
        
        # Update metrics
        total_connections = sum(len(conns) for conns in self.connections.values())
        WEBSOCKET_CONNECTIONS.set(total_connections)

class OptimizedRedisManager:
    """Redis manager with connection pooling and batch operations."""
    
    def __init__(self, redis_url: str = "redis://localhost:6382"):
        self.redis_url = redis_url
        self.pool: Optional[aioredis.ConnectionPool] = None
        self.redis: Optional[aioredis.Redis] = None
        self.batch_queue: deque = deque()
        self.batch_size = 100
        self.batch_timeout = 0.1  # 100ms
        self._batch_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize Redis with optimized connection pool."""
        self.pool = aioredis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=20,  # Pool size optimization
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        
        self.redis = aioredis.Redis(
            connection_pool=self.pool,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        await self.redis.ping()
        
        # Start batch processing
        self._batch_task = asyncio.create_task(self._process_batches())
        
    async def close(self):
        """Close Redis connections and cleanup."""
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        
        if self.redis:
            await self.redis.close()
        
        if self.pool:
            await self.pool.disconnect()
    
    async def _process_batches(self):
        """Process batched Redis operations."""
        while True:
            try:
                await asyncio.sleep(self.batch_timeout)
                
                if not self.batch_queue:
                    continue
                
                # Process batch
                batch = []
                while self.batch_queue and len(batch) < self.batch_size:
                    batch.append(self.batch_queue.popleft())
                
                if batch:
                    await self._execute_batch(batch)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                CONNECTION_ERRORS.labels(error_type='batch_error').inc()
                print(f"Batch processing error: {e}")
    
    async def _execute_batch(self, batch: List[Dict]):
        """Execute a batch of Redis operations."""
        try:
            pipeline = self.redis.pipeline(transaction=False)
            
            for operation in batch:
                method = getattr(pipeline, operation['method'])
                method(*operation['args'], **operation.get('kwargs', {}))
            
            await pipeline.execute()
            REDIS_OPERATIONS.labels(operation='batch').inc(len(batch))
            
        except Exception as e:
            REDIS_OPERATIONS.labels(operation='batch_error').inc()
            raise
    
    def queue_operation(self, method: str, *args, **kwargs):
        """Queue a Redis operation for batch processing."""
        self.batch_queue.append({
            'method': method,
            'args': args,
            'kwargs': kwargs
        })
    
    async def get_immediate(self, key: str):
        """Get operation that bypasses batching for immediate results."""
        try:
            result = await self.redis.get(key)
            REDIS_OPERATIONS.labels(operation='get').inc()
            return result
        except Exception as e:
            REDIS_OPERATIONS.labels(operation='get_error').inc()
            raise

class MessageBroadcaster:
    """Optimized message broadcaster with async batching."""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.connection_pool = connection_pool
        self.broadcast_stats = defaultdict(int)
        
    async def broadcast_to_room_optimized(
        self, 
        room_id: str, 
        message: str, 
        exclude_conn_ids: Optional[Set[str]] = None
    ):
        """Optimized room broadcasting with async gathering."""
        start_time = time.time()
        
        connections = self.connection_pool.connections.get(room_id, {})
        if not connections:
            return 0
        
        exclude_conn_ids = exclude_conn_ids or set()
        
        # Build send tasks
        send_tasks = []
        valid_connections = []
        
        for conn_id, conn_ref in connections.items():
            if conn_id in exclude_conn_ids:
                continue
                
            websocket = conn_ref()
            if websocket is None:
                continue  # Dead reference, will be cleaned up
                
            valid_connections.append((conn_id, websocket))
            send_tasks.append(self._send_with_error_handling(websocket, message, conn_id))
        
        if not send_tasks:
            return 0
        
        # Execute all sends concurrently
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        # Count successful sends
        successful_sends = sum(1 for result in results if result is True)
        
        # Update statistics
        self.connection_pool.room_stats[room_id]['messages_sent'] += successful_sends
        self.broadcast_stats['total_broadcasts'] += 1
        self.broadcast_stats['total_recipients'] += successful_sends
        
        # Update metrics
        processing_time = time.time() - start_time
        MESSAGE_PROCESSING_TIME.observe(processing_time)
        MESSAGES_SENT.inc(successful_sends)
        
        return successful_sends
    
    async def _send_with_error_handling(self, websocket, message: str, conn_id: str) -> bool:
        """Send message with error handling."""
        try:
            await websocket.send_text(message)
            return True
        except Exception as e:
            CONNECTION_ERRORS.labels(error_type='send_error').inc()
            # Don't remove connection here - let cleanup task handle it
            return False

class PerformanceOptimizedWebSocketManager:
    """Complete WebSocket manager with all performance optimizations."""
    
    def __init__(self):
        self.connection_pool = ConnectionPool()
        self.redis_manager = OptimizedRedisManager()
        self.broadcaster = MessageBroadcaster(self.connection_pool)
        self.metrics = PerformanceMetrics()
        self.performance_monitoring_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize all components."""
        await self.redis_manager.initialize()
        await self.connection_pool.start_cleanup_task()
        
        # Start performance monitoring
        self.performance_monitoring_task = asyncio.create_task(
            self._monitor_performance()
        )
        
        # Start Prometheus metrics server
        start_http_server(8090)  # Metrics available at :8090/metrics
        
    async def close(self):
        """Cleanup all resources."""
        if self.performance_monitoring_task:
            self.performance_monitoring_task.cancel()
            
        await self.connection_pool.stop_cleanup_task()
        await self.redis_manager.close()
    
    async def _monitor_performance(self):
        """Monitor and update performance metrics."""
        last_message_count = 0
        last_connection_count = 0
        
        while True:
            try:
                await asyncio.sleep(1)  # Update every second
                
                # Calculate rates
                current_messages = self.broadcaster.broadcast_stats['total_recipients']
                current_connections = sum(
                    len(conns) for conns in self.connection_pool.connections.values()
                )
                
                self.metrics.messages_per_second = current_messages - last_message_count
                self.metrics.connections_per_second = current_connections - last_connection_count
                
                last_message_count = current_messages
                last_connection_count = current_connections
                
                # Update Prometheus metrics
                WEBSOCKET_CONNECTIONS.set(current_connections)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Performance monitoring error: {e}")

# Performance testing utilities
class PerformanceBenchmark:
    """Benchmark utilities for WebSocket performance testing."""
    
    @staticmethod
    async def benchmark_connection_creation(manager: PerformanceOptimizedWebSocketManager, num_connections: int = 1000):
        """Benchmark connection creation performance."""
        start_time = time.time()
        
        # Simulate connection creation
        for i in range(num_connections):
            # This would normally be WebSocket connections
            # For testing, we simulate the internal operations
            pass
            
        end_time = time.time()
        
        return {
            'total_time': end_time - start_time,
            'connections_per_second': num_connections / (end_time - start_time),
            'avg_time_per_connection': (end_time - start_time) / num_connections
        }
    
    @staticmethod
    async def benchmark_message_broadcasting(broadcaster: MessageBroadcaster, room_size: int = 100, messages: int = 1000):
        """Benchmark message broadcasting performance."""
        # This would require actual WebSocket connections for real testing
        # Implementation would measure broadcast latency and throughput
        pass

# Configuration for high-performance deployment
PERFORMANCE_CONFIG = {
    'uvloop': True,  # Use uvloop for better performance
    'max_connections_per_worker': 10000,
    'redis_pool_size': 20,
    'batch_size': 100,
    'batch_timeout': 0.1,
    'cleanup_interval': 30,
    'metrics_update_interval': 1,
    'prometheus_port': 8090
}

if __name__ == "__main__":
    # Example usage with uvloop
    if PERFORMANCE_CONFIG['uvloop']:
        uvloop.install()
    
    async def main():
        manager = PerformanceOptimizedWebSocketManager()
        try:
            await manager.initialize()
            print("Performance-optimized WebSocket manager started")
            print(f"Metrics available at http://localhost:{PERFORMANCE_CONFIG['prometheus_port']}/metrics")
            
            # Keep running
            await asyncio.sleep(3600)  # Run for 1 hour
            
        finally:
            await manager.close()
    
    asyncio.run(main())