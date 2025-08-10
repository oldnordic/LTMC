"""
Performance Utilities
====================

Performance monitoring and measurement utilities.
Target: <15ms performance from research findings.
"""

import time
import functools
import logging
from typing import Any, Callable, Dict
from contextlib import contextmanager

from models.base_models import PerformanceMetrics


logger = logging.getLogger(__name__)


class PerformanceTimer:
    """Context manager for measuring execution time."""
    
    def __init__(self, operation_name: str = "operation"):
        self.operation_name = operation_name
        self.start_time = 0.0
        self.end_time = 0.0
        self.execution_time_ms = 0.0
        
    def __enter__(self) -> 'PerformanceTimer':
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.execution_time_ms = (self.end_time - self.start_time) * 1000
        
        # Log performance warning if over target
        if self.execution_time_ms > 15.0:  # 15ms target from research
            logger.warning(
                f"Performance warning: {self.operation_name} took {self.execution_time_ms:.2f}ms "
                f"(target: <15ms)"
            )
        else:
            logger.debug(f"{self.operation_name} completed in {self.execution_time_ms:.2f}ms")


def measure_performance(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Adds performance metrics to returned data if it's a dict.
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        operation_name = f"{func.__module__}.{func.__name__}"
        
        with PerformanceTimer(operation_name) as timer:
            result = await func(*args, **kwargs)
        
        # Add performance metrics if result is a dict
        if isinstance(result, dict) and 'performance' not in result:
            result['performance'] = PerformanceMetrics(
                execution_time_ms=timer.execution_time_ms,
                database_queries=1,  # Assume 1 DB query per operation
                cache_hits=0,
                cache_misses=0
            )
        
        return result
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        operation_name = f"{func.__module__}.{func.__name__}"
        
        with PerformanceTimer(operation_name) as timer:
            result = func(*args, **kwargs)
        
        # Add performance metrics if result is a dict
        if isinstance(result, dict) and 'performance' not in result:
            result['performance'] = PerformanceMetrics(
                execution_time_ms=timer.execution_time_ms,
                database_queries=1,
                cache_hits=0,
                cache_misses=0
            )
        
        return result
    
    # Return appropriate wrapper based on function type
    if hasattr(func, '__code__') and 'await' in func.__code__.co_names:
        return async_wrapper
    else:
        return sync_wrapper


@contextmanager
def performance_context(operation_name: str, target_ms: float = 15.0):
    """
    Context manager for measuring performance with custom targets.
    
    Args:
        operation_name: Name of the operation being measured
        target_ms: Performance target in milliseconds
    """
    start_time = time.perf_counter()
    
    try:
        yield
    finally:
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        
        if execution_time_ms > target_ms:
            logger.warning(
                f"Performance warning: {operation_name} took {execution_time_ms:.2f}ms "
                f"(target: <{target_ms}ms)"
            )
        else:
            logger.debug(f"{operation_name} completed in {execution_time_ms:.2f}ms")


class PerformanceMonitor:
    """Performance monitoring and statistics collection."""
    
    def __init__(self):
        self.operation_stats: Dict[str, Dict[str, Any]] = {}
        
    def record_operation(self, operation_name: str, execution_time_ms: float):
        """Record operation performance statistics."""
        if operation_name not in self.operation_stats:
            self.operation_stats[operation_name] = {
                'count': 0,
                'total_time_ms': 0.0,
                'min_time_ms': float('inf'),
                'max_time_ms': 0.0,
                'avg_time_ms': 0.0,
                'over_target_count': 0
            }
        
        stats = self.operation_stats[operation_name]
        stats['count'] += 1
        stats['total_time_ms'] += execution_time_ms
        stats['min_time_ms'] = min(stats['min_time_ms'], execution_time_ms)
        stats['max_time_ms'] = max(stats['max_time_ms'], execution_time_ms)
        stats['avg_time_ms'] = stats['total_time_ms'] / stats['count']
        
        if execution_time_ms > 15.0:  # 15ms target
            stats['over_target_count'] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        total_operations = sum(stats['count'] for stats in self.operation_stats.values())
        total_over_target = sum(stats['over_target_count'] for stats in self.operation_stats.values())
        
        return {
            'total_operations': total_operations,
            'total_over_target': total_over_target,
            'success_rate': ((total_operations - total_over_target) / total_operations * 100) if total_operations > 0 else 100,
            'operation_details': dict(self.operation_stats)
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()