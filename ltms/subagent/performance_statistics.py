"""
MCP Performance Statistics and Monitoring
Tracks performance metrics and provides comprehensive statistics for optimization.

File: ltms/subagent/performance_statistics.py
Lines: ~143 (under 300 limit)
Purpose: Performance monitoring and statistics collection
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class MCPPerformanceStatistics:
    """
    Performance statistics and monitoring for MCP tool optimization.
    
    Tracks execution times, cache hit rates, batch performance,
    and provides comprehensive reporting for optimization analysis.
    """
    
    def __init__(self):
        self.execution_stats: Dict[str, Any] = defaultdict(lambda: {
            "total_calls": 0,
            "total_time_ms": 0,
            "total_tokens": 0,
            "cache_hits": 0,
            "batch_count": 0
        })
        self.batch_stats = {
            "total_batches": 0,
            "total_calls_batched": 0
        }
        
    async def update_execution_stats(self, tool_name: str, execution_time_ms: float,
                                   arguments: Dict[str, Any], result: Any,
                                   cache_hit: bool = False):
        """Update execution statistics for performance monitoring."""
        stats = self.execution_stats[tool_name]
        stats["total_calls"] += 1
        stats["total_time_ms"] += execution_time_ms
        stats["total_tokens"] += self._estimate_tokens_from_call(tool_name, arguments)
        
        if cache_hit:
            stats["cache_hits"] += 1
    
    async def update_batch_stats(self, batch_size: int):
        """Update batch execution statistics."""
        self.batch_stats["total_batches"] += 1
        self.batch_stats["total_calls_batched"] += batch_size
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        total_calls = sum(stats["total_calls"] for stats in self.execution_stats.values())
        total_cache_hits = sum(stats["cache_hits"] for stats in self.execution_stats.values())
        
        # Calculate per-tool averages
        tool_performance = {}
        for tool_name, stats in self.execution_stats.items():
            if stats["total_calls"] > 0:
                tool_performance[tool_name] = {
                    "total_calls": stats["total_calls"],
                    "avg_execution_time_ms": stats["total_time_ms"] / stats["total_calls"],
                    "cache_hit_rate": stats["cache_hits"] / stats["total_calls"],
                    "avg_tokens_per_call": stats["total_tokens"] / stats["total_calls"]
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "total_tool_calls": total_calls,
                "cache_hit_rate": (total_cache_hits / total_calls) if total_calls > 0 else 0,
                "total_batches": self.batch_stats["total_batches"],
                "total_calls_batched": self.batch_stats["total_calls_batched"],
                "batch_efficiency": (
                    self.batch_stats["total_calls_batched"] / total_calls
                ) if total_calls > 0 else 0
            },
            "tool_performance": tool_performance,
            "optimization_features": {
                "caching_enabled": True,
                "batching_enabled": True,
                "context_compression_enabled": True,
                "argument_optimization_enabled": True
            },
            "recommendations": self._generate_performance_recommendations(tool_performance)
        }
    
    def _estimate_tokens_from_call(self, tool_name: str, arguments: Dict[str, Any]) -> int:
        """Estimate token count for a tool call."""
        # Simple token estimation based on argument size
        args_str = json.dumps(arguments)
        estimated_tokens = len(args_str) // 4  # Rough approximation
        
        # Add base cost per tool
        base_tokens = {
            "memory_action": 50,
            "graph_action": 75,
            "pattern_action": 100,
            "blueprint_action": 60,
            "unix_action": 40
        }
        
        estimated_tokens += base_tokens.get(tool_name, 30)
        return estimated_tokens
    
    def _generate_performance_recommendations(self, tool_performance: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Check for tools with low cache hit rates
        for tool_name, perf in tool_performance.items():
            if perf["cache_hit_rate"] < 0.3 and perf["total_calls"] > 10:
                recommendations.append(
                    f"Consider increasing cache TTL for {tool_name} (hit rate: {perf['cache_hit_rate']:.2%})"
                )
            
            if perf["avg_execution_time_ms"] > 1000:
                recommendations.append(
                    f"High execution time for {tool_name}: {perf['avg_execution_time_ms']:.1f}ms - consider optimization"
                )
            
            if perf["avg_tokens_per_call"] > 200:
                recommendations.append(
                    f"High token usage for {tool_name}: {perf['avg_tokens_per_call']:.0f} tokens - consider compression"
                )
        
        # Overall recommendations
        total_calls = sum(perf["total_calls"] for perf in tool_performance.values())
        if total_calls > 100:
            avg_cache_rate = sum(
                perf["cache_hit_rate"] * perf["total_calls"] for perf in tool_performance.values()
            ) / total_calls
            
            if avg_cache_rate < 0.4:
                recommendations.append(
                    f"Overall cache hit rate is low ({avg_cache_rate:.2%}) - consider cache strategy review"
                )
        
        # Batching recommendations
        batch_efficiency = self.batch_stats["total_calls_batched"] / total_calls if total_calls > 0 else 0
        if batch_efficiency < 0.3 and total_calls > 50:
            recommendations.append(
                f"Low batching efficiency ({batch_efficiency:.2%}) - more calls could benefit from batching"
            )
        
        return recommendations
    
    async def get_tool_ranking(self, metric: str = "total_calls") -> List[Dict[str, Any]]:
        """Get tools ranked by specified metric."""
        valid_metrics = ["total_calls", "avg_execution_time_ms", "cache_hit_rate", "avg_tokens_per_call"]
        if metric not in valid_metrics:
            metric = "total_calls"
        
        tool_list = []
        for tool_name, stats in self.execution_stats.items():
            if stats["total_calls"] > 0:
                tool_data = {
                    "tool_name": tool_name,
                    "total_calls": stats["total_calls"],
                    "avg_execution_time_ms": stats["total_time_ms"] / stats["total_calls"],
                    "cache_hit_rate": stats["cache_hits"] / stats["total_calls"],
                    "avg_tokens_per_call": stats["total_tokens"] / stats["total_calls"]
                }
                tool_list.append(tool_data)
        
        # Sort by metric (descending for most metrics, ascending for execution time)
        reverse_sort = metric != "avg_execution_time_ms"
        return sorted(tool_list, key=lambda x: x[metric], reverse=reverse_sort)
    
    async def reset_statistics(self):
        """Reset all performance statistics."""
        self.execution_stats.clear()
        self.batch_stats = {
            "total_batches": 0,
            "total_calls_batched": 0
        }
        logger.info("Performance statistics reset")
    
    async def export_statistics(self) -> Dict[str, Any]:
        """Export complete statistics for external analysis."""
        return {
            "export_timestamp": datetime.now().isoformat(),
            "execution_stats": dict(self.execution_stats),
            "batch_stats": self.batch_stats.copy(),
            "summary": await self.get_performance_stats()
        }