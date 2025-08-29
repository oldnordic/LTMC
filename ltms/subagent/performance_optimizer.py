"""
MCP Performance Optimization System
Unified interface for optimized MCP tool calls with modular architecture.

File: ltms/subagent/performance_optimizer.py
Lines: ~100 (under 300 limit)
Purpose: Main interface for performance optimization with modular components
"""

import logging
from typing import Dict, Any, List, Optional

from .optimization_core import MCPCoreOptimizer
from .batch_execution import MCPBatchExecutor
from .performance_statistics import MCPPerformanceStatistics

logger = logging.getLogger(__name__)


class MCPPerformanceOptimizer:
    """
    Unified performance optimization system for MCP tool calls.
    
    Provides a clean interface to modular optimization components:
    - Core optimization for single tool calls
    - Batch execution for multiple tool calls
    - Performance statistics and monitoring
    """
    
    def __init__(self):
        self.core_optimizer = MCPCoreOptimizer()
        self.batch_executor = MCPBatchExecutor(self.core_optimizer)
        self.statistics = MCPPerformanceStatistics()
        
    async def optimize_tool_call(self, tool_name: str, arguments: Dict[str, Any],
                               session_id: str, priority: str = "normal") -> Any:
        """
        Execute optimized single tool call with caching and context optimization.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            session_id: Session identifier
            priority: Execution priority
            
        Returns:
            Tool execution result
        """
        from datetime import datetime
        start_time = datetime.now()
        
        # Check cache first
        cache_result = await self.core_optimizer._check_result_cache(tool_name, arguments, session_id)
        cache_hit = cache_result is not None
        
        if cache_result:
            logger.debug(f"Cache hit for {tool_name} in session {session_id}")
        else:
            # Execute through core optimizer
            cache_result = await self.core_optimizer.optimize_tool_call(
                tool_name, arguments, session_id, priority
            )
        
        # Update statistics
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        await self.statistics.update_execution_stats(
            tool_name, execution_time, arguments, cache_result, cache_hit
        )
        
        return cache_result
    
    async def batch_optimize_tools(self, tool_calls: List[Dict[str, Any]], 
                                 session_id: str) -> List[Any]:
        """
        Execute multiple tool calls with batch optimization.
        
        Args:
            tool_calls: List of tool call specifications
            session_id: Session identifier
            
        Returns:
            List of tool execution results
        """
        results = await self.batch_executor.batch_optimize_tools(tool_calls, session_id)
        
        # Update batch statistics
        await self.statistics.update_batch_stats(len(tool_calls))
        
        return results
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return await self.statistics.get_performance_stats()
    
    async def get_tool_ranking(self, metric: str = "total_calls") -> List[Dict[str, Any]]:
        """Get tools ranked by specified metric."""
        return await self.statistics.get_tool_ranking(metric)
    
    async def reset_statistics(self):
        """Reset all performance statistics."""
        await self.statistics.reset_statistics()
    
    async def export_statistics(self) -> Dict[str, Any]:
        """Export complete statistics for external analysis."""
        return await self.statistics.export_statistics()