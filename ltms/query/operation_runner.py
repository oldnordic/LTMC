"""
LTMC Database Operation Runner
Real database operation execution via LTMC tools - NO PLACEHOLDERS

Executes individual database operations by converting them to actual LTMC tool calls
with proper error handling, result formatting, and performance tracking.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime

from .execution_plan import DatabaseOperation
from .models import DatabaseTarget

# Import LTMC consolidated tools for real database operations
from ltms.tools.memory.memory_actions import memory_action
from ltms.tools.memory.chat_actions import chat_action
from ltms.tools.unix.unix_actions import unix_action
from ltms.tools.graph.graph_actions import graph_action
from ltms.tools.monitoring.cache_actions import cache_action


class DatabaseOperationRunner:
    """
    Production database operation runner for LTMC operations.
    
    Converts database operations into actual LTMC tool calls with proper
    async execution, error handling, and result standardization.
    
    Design Philosophy:
    - Real tool integration: Uses actual LTMC consolidated tools
    - Standardized results: Consistent response format across databases
    - Error resilience: Graceful handling of tool failures
    - Performance tracking: Operation-level metrics
    """
    
    def __init__(self):
        """Initialize operation runner with tool mappings."""
        # Tool mapping for different database targets
        self.tool_mappings = {
            DatabaseTarget.SQLITE: self._run_memory_action,
            DatabaseTarget.FAISS: self._run_memory_action,
            DatabaseTarget.FILESYSTEM: self._run_unix_action,
            DatabaseTarget.NEO4J: self._run_graph_action,
            DatabaseTarget.REDIS: self._run_cache_action
        }
        
        # Statistics tracking
        self.operation_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "operations_by_database": {},
            "average_operation_time_ms": 0.0,
            "timeout_count": 0,
            "error_count_by_type": {}
        }
        
    async def run_operation(self, operation: DatabaseOperation) -> Dict[str, Any]:
        """
        Execute database operation via appropriate LTMC tool.
        
        Args:
            operation: DatabaseOperation to execute
            
        Returns:
            Standardized result with source database information
        """
        start_time = time.time()
        self.operation_stats["total_operations"] += 1
        
        # Update database-specific statistics
        db_name = operation.database_target.value
        if db_name not in self.operation_stats["operations_by_database"]:
            self.operation_stats["operations_by_database"][db_name] = 0
        self.operation_stats["operations_by_database"][db_name] += 1
        
        try:
            # Get appropriate tool runner for database target
            tool_runner = self.tool_mappings.get(operation.database_target)
            if not tool_runner:
                return self._create_error_result(
                    operation, "unsupported_database", 
                    f"No tool mapping for database: {operation.database_target.value}"
                )
                
            # Execute operation via tool runner
            raw_result = await tool_runner(operation)
            
            # Standardize and enhance result
            standardized_result = self._standardize_result(raw_result, operation, start_time)
            
            # Update success statistics
            if standardized_result.get("success", False):
                self.operation_stats["successful_operations"] += 1
            else:
                self.operation_stats["failed_operations"] += 1
                
            # Update timing statistics
            operation_time = (time.time() - start_time) * 1000
            self._update_timing_statistics(operation_time)
            
            return standardized_result
            
        except Exception as e:
            # Handle unexpected errors
            self.operation_stats["failed_operations"] += 1
            self._update_error_statistics(type(e).__name__)
            
            return self._create_error_result(
                operation, "execution_exception", str(e)
            )
            
    async def _run_memory_action(self, operation: DatabaseOperation) -> Dict[str, Any]:
        """Execute operation via LTMC memory_action tool."""
        try:
            # Extract parameters for memory_action
            params = operation.parameters.copy()
            
            # Ensure required parameters exist
            if "action" not in params:
                params["action"] = "retrieve"  # Default action
                
            # Execute memory_action with real database connection
            result = await memory_action(**params)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"memory_action failed: {str(e)}",
                "error_type": "memory_action_error",
                "results": []
            }
            
    async def _run_unix_action(self, operation: DatabaseOperation) -> Dict[str, Any]:
        """Execute operation via LTMC unix_action tool."""
        try:
            # Extract parameters for unix_action
            params = operation.parameters.copy()
            
            # Ensure required parameters exist
            if "action" not in params:
                params["action"] = "find"  # Default filesystem action
                
            # Execute unix_action for filesystem operations
            result = await unix_action(**params)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"unix_action failed: {str(e)}",
                "error_type": "unix_action_error",
                "results": []
            }
            
    async def _run_graph_action(self, operation: DatabaseOperation) -> Dict[str, Any]:
        """Execute operation via LTMC graph_action tool."""
        try:
            # Extract parameters for graph_action
            params = operation.parameters.copy()
            
            # Ensure required parameters exist
            if "action" not in params:
                params["action"] = "query"  # Default graph action
                
            # Execute graph_action for Neo4j operations
            result = await graph_action(**params)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"graph_action failed: {str(e)}",
                "error_type": "graph_action_error",
                "results": []
            }
            
    async def _run_cache_action(self, operation: DatabaseOperation) -> Dict[str, Any]:
        """Execute operation via LTMC cache_action tool."""
        try:
            # Extract parameters for cache_action
            params = operation.parameters.copy()
            
            # Ensure required parameters exist
            if "action" not in params:
                params["action"] = "get"  # Default cache action
                
            # Execute cache_action for Redis operations
            result = await cache_action(**params)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"cache_action failed: {str(e)}",
                "error_type": "cache_action_error",
                "results": []
            }
            
    def _standardize_result(self, raw_result: Dict[str, Any],
                          operation: DatabaseOperation, start_time: float) -> Dict[str, Any]:
        """Standardize result format across all database operations."""
        execution_time = (time.time() - start_time) * 1000
        
        # Base standardized result
        standardized = {
            "success": raw_result.get("success", False),
            "source_database": operation.database_target.value,
            "operation_type": operation.operation_type,
            "execution_time_ms": round(execution_time, 2),
            "estimated_cost_ms": operation.estimated_cost,
            "results": raw_result.get("results", [])
        }
        
        # Add documents if present (common for memory operations)
        if "documents" in raw_result:
            standardized["documents"] = raw_result["documents"]
            standardized["document_count"] = len(raw_result["documents"])
            
        # Add files if present (common for filesystem operations)
        if "files" in raw_result:
            standardized["files"] = raw_result["files"]
            standardized["file_count"] = len(raw_result["files"])
            
        # Add nodes if present (common for graph operations)
        if "nodes" in raw_result:
            standardized["nodes"] = raw_result["nodes"]
            standardized["node_count"] = len(raw_result["nodes"])
            
        # Add cache data if present (common for cache operations)
        if "cache_data" in raw_result:
            standardized["cache_data"] = raw_result["cache_data"]
            
        # Add error information if present
        if "error" in raw_result:
            standardized["error"] = raw_result["error"]
            standardized["error_type"] = raw_result.get("error_type", "unknown_error")
            
        # Add metadata
        standardized["metadata"] = {
            "database_target": operation.database_target.value,
            "operation_parameters": operation.parameters,
            "execution_timestamp": datetime.now().isoformat(),
            "performance_delta_ms": round(execution_time - operation.estimated_cost, 2)
        }
        
        return standardized
        
    def _create_error_result(self, operation: DatabaseOperation,
                           error_type: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "success": False,
            "source_database": operation.database_target.value,
            "operation_type": operation.operation_type,
            "error": error_message,
            "error_type": error_type,
            "results": [],
            "metadata": {
                "database_target": operation.database_target.value,
                "operation_parameters": operation.parameters,
                "execution_timestamp": datetime.now().isoformat(),
                "error_occurred": True
            }
        }
        
    def _update_timing_statistics(self, operation_time: float):
        """Update average operation timing statistics."""
        total_ops = self.operation_stats["total_operations"]
        current_avg = self.operation_stats["average_operation_time_ms"]
        
        # Calculate new rolling average
        new_avg = ((current_avg * (total_ops - 1)) + operation_time) / total_ops
        self.operation_stats["average_operation_time_ms"] = round(new_avg, 2)
        
    def _update_error_statistics(self, error_type: str):
        """Update error statistics by type."""
        if error_type not in self.operation_stats["error_count_by_type"]:
            self.operation_stats["error_count_by_type"][error_type] = 0
        self.operation_stats["error_count_by_type"][error_type] += 1
        
    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get operation statistics for monitoring."""
        stats = self.operation_stats.copy()
        
        # Calculate success rate
        total_ops = stats["successful_operations"] + stats["failed_operations"]
        if total_ops > 0:
            stats["success_rate"] = round(stats["successful_operations"] / total_ops * 100, 2)
        else:
            stats["success_rate"] = 0.0
            
        # Calculate error rate
        if stats["total_operations"] > 0:
            stats["error_rate"] = round(stats["failed_operations"] / stats["total_operations"] * 100, 2)
        else:
            stats["error_rate"] = 0.0
            
        return stats
        
    def reset_statistics(self):
        """Reset operation statistics."""
        for key in self.operation_stats:
            if isinstance(self.operation_stats[key], (int, float)):
                self.operation_stats[key] = 0 if isinstance(self.operation_stats[key], int) else 0.0
            elif isinstance(self.operation_stats[key], dict):
                self.operation_stats[key] = {}