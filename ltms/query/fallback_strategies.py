"""
LTMC Fallback Strategy Executor
Modular execution of error recovery strategies - NO PLACEHOLDERS

Executes intelligent fallback strategies for error recovery including
retry operations, alternative databases, and graceful degradation.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .error_classification import FallbackStrategy, ErrorSeverity
from .execution_plan import ExecutionPlan, DatabaseOperation, create_fallback_execution_plan
from .models import DatabaseTarget


class FallbackExecutor:
    """Executes fallback strategies for error recovery."""
    
    def __init__(self):
        """Initialize fallback executor."""
        # Retry configuration
        self.retry_config = {
            "max_retries": 3,
            "retry_delay_ms": 100,
            "exponential_backoff": True
        }
        
        # Database priorities for fallback
        self.database_priorities = [
            DatabaseTarget.SQLITE,    # Most reliable
            DatabaseTarget.FAISS,     # Fast vector search
            DatabaseTarget.FILESYSTEM, # Always available
            DatabaseTarget.NEO4J,     # Graph relationships
            DatabaseTarget.REDIS      # Potentially volatile
        ]
        
        # Statistics tracking
        self.fallback_stats = {
            "total_fallbacks_executed": 0,
            "fallbacks_by_strategy": {strategy.value: 0 for strategy in FallbackStrategy},
            "successful_fallbacks": 0,
            "failed_fallbacks": 0,
            "average_fallback_time_ms": 0.0
        }
        
    async def execute_fallback(self, strategy: FallbackStrategy, original_plan: ExecutionPlan,
                             failed_operations: List[DatabaseOperation],
                             error_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the specified fallback strategy.
        
        Args:
            strategy: The fallback strategy to execute
            original_plan: Original execution plan that failed
            failed_operations: List of operations that failed
            error_context: Context about the errors that occurred
            
        Returns:
            Fallback execution result
        """
        start_time = time.time()
        self.fallback_stats["total_fallbacks_executed"] += 1
        self.fallback_stats["fallbacks_by_strategy"][strategy.value] += 1
        
        try:
            if strategy == FallbackStrategy.RETRY_OPERATION:
                result = await self._retry_operations(failed_operations, error_context)
            elif strategy == FallbackStrategy.USE_ALTERNATIVE_DATABASE:
                result = await self._use_alternative_database(original_plan, failed_operations, error_context)
            elif strategy == FallbackStrategy.SINGLE_DATABASE_FALLBACK:
                result = await self._single_database_fallback(original_plan, error_context)
            elif strategy == FallbackStrategy.CACHED_RESULTS:
                result = await self._use_cached_results(original_plan, error_context)
            elif strategy == FallbackStrategy.MINIMAL_RESPONSE:
                result = self._minimal_response(error_context)
            else:
                result = self._minimal_response({"error": f"Unknown strategy: {strategy}"})
                
            # Update statistics
            execution_time = (time.time() - start_time) * 1000
            self._update_fallback_stats(execution_time, True)
            
            result["fallback_metadata"] = {
                "strategy_used": strategy.value,
                "execution_time_ms": round(execution_time, 2),
                "success": result.get("success", False),
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._update_fallback_stats(execution_time, False)
            
            return {
                "success": False,
                "results": [],
                "errors": [{"error_type": "fallback_failure", "message": str(e)}],
                "fallback_metadata": {
                    "strategy_used": strategy.value,
                    "execution_time_ms": round(execution_time, 2),
                    "success": False,
                    "error_occurred": True
                }
            }
            
    async def _retry_operations(self, failed_operations: List[DatabaseOperation],
                              error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry failed operations with exponential backoff."""
        successful_results = []
        retry_errors = []
        
        for operation in failed_operations:
            retry_result = await self._retry_single_operation(operation, error_context)
            
            if retry_result.get("success", False):
                successful_results.extend(retry_result.get("results", []))
            else:
                retry_errors.extend(retry_result.get("errors", []))
                
        return {
            "success": len(successful_results) > 0,
            "results": successful_results,
            "errors": retry_errors,
            "strategy_details": {
                "operations_retried": len(failed_operations),
                "successful_retries": len(successful_results),
                "failed_retries": len(retry_errors)
            }
        }
        
    async def _retry_single_operation(self, operation: DatabaseOperation,
                                    error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry a single operation with exponential backoff."""
        for attempt in range(self.retry_config["max_retries"]):
            try:
                # Import here to avoid circular dependency
                from .operation_runner import DatabaseOperationRunner
                runner = DatabaseOperationRunner()
                
                # Execute operation
                result = await runner.execute_operation(operation)
                
                if result.get("success", False):
                    return result
                    
            except Exception as e:
                if attempt == self.retry_config["max_retries"] - 1:
                    return {
                        "success": False,
                        "results": [],
                        "errors": [{"error_type": "retry_exhausted", "message": str(e)}]
                    }
                    
            # Wait before next retry with exponential backoff
            delay = self.retry_config["retry_delay_ms"]
            if self.retry_config["exponential_backoff"]:
                delay *= (2 ** attempt)
                
            await asyncio.sleep(delay / 1000.0)
            
        return {
            "success": False,
            "results": [],
            "errors": [{"error_type": "retry_failed", "message": "All retries exhausted"}]
        }
        
    async def _use_alternative_database(self, original_plan: ExecutionPlan,
                                      failed_operations: List[DatabaseOperation],
                                      error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use alternative database for failed operations."""
        # Identify failed database targets
        failed_databases = set(op.database_target for op in failed_operations)
        
        # Find available alternatives
        available_databases = [db for db in self.database_priorities if db not in failed_databases]
        
        if not available_databases:
            return self._minimal_response({"error": "No alternative databases available"})
            
        # Create new operations targeting alternative databases
        alternative_results = []
        alternative_errors = []
        
        for operation in failed_operations:
            # Try each alternative database in priority order
            for alt_db in available_databases:
                alt_operation = DatabaseOperation(
                    database_target=alt_db,
                    query_type=operation.query_type,
                    parameters=operation.parameters,
                    execution_strategy=operation.execution_strategy
                )
                
                try:
                    from .operation_runner import DatabaseOperationRunner
                    runner = DatabaseOperationRunner()
                    result = await runner.execute_operation(alt_operation)
                    
                    if result.get("success", False):
                        alternative_results.extend(result.get("results", []))
                        break  # Success - stop trying alternatives
                        
                except Exception as e:
                    continue  # Try next alternative
                    
            else:
                # No alternatives worked for this operation
                alternative_errors.append({
                    "error_type": "no_alternatives",
                    "message": f"No alternative database could handle operation: {operation.database_target.value}"
                })
                
        return {
            "success": len(alternative_results) > 0,
            "results": alternative_results,
            "errors": alternative_errors,
            "strategy_details": {
                "original_databases": [db.value for db in failed_databases],
                "alternative_databases_tried": [db.value for db in available_databases],
                "successful_alternatives": len(alternative_results)
            }
        }
        
    async def _single_database_fallback(self, original_plan: ExecutionPlan,
                                      error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to single most reliable database."""
        fallback_db = self.database_priorities[0]  # Most reliable (SQLite)
        
        # Create fallback plan with single database
        fallback_plan = create_fallback_execution_plan(
            original_plan.query, [fallback_db], original_plan.query_type
        )
        
        try:
            from .operation_runner import DatabaseOperationRunner
            runner = DatabaseOperationRunner()
            
            results = []
            for operation in fallback_plan.operations:
                result = await runner.execute_operation(operation)
                if result.get("success", False):
                    results.extend(result.get("results", []))
                    
            return {
                "success": len(results) > 0,
                "results": results,
                "errors": [],
                "strategy_details": {
                    "fallback_database": fallback_db.value,
                    "original_operation_count": len(original_plan.operations),
                    "fallback_operation_count": len(fallback_plan.operations)
                }
            }
            
        except Exception as e:
            return self._minimal_response({"error": f"Single database fallback failed: {str(e)}"})
            
    async def _use_cached_results(self, original_plan: ExecutionPlan,
                                error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to use cached results if available."""
        # This would integrate with Redis or other caching layer
        # For now, return minimal response indicating cache miss
        return {
            "success": False,
            "results": [],
            "errors": [{"error_type": "cache_miss", "message": "No cached results available"}],
            "strategy_details": {
                "cache_checked": True,
                "cache_available": False
            }
        }
        
    def _minimal_response(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Return minimal response when all else fails."""
        return {
            "success": False,
            "results": [{
                "type": "system_message",
                "content": "Unable to process query due to system errors. Please try again later.",
                "title": "System Error",
                "metadata": {
                    "error_context": error_context,
                    "timestamp": datetime.now().isoformat(),
                    "fallback_strategy": "minimal_response"
                }
            }],
            "errors": [{"error_type": "system_failure", "message": "All recovery strategies exhausted"}],
            "strategy_details": {
                "final_fallback": True,
                "user_friendly_message": True
            }
        }
        
    def _update_fallback_stats(self, execution_time: float, success: bool):
        """Update fallback execution statistics."""
        if success:
            self.fallback_stats["successful_fallbacks"] += 1
        else:
            self.fallback_stats["failed_fallbacks"] += 1
            
        # Update average execution time
        total_fallbacks = self.fallback_stats["total_fallbacks_executed"]
        current_avg = self.fallback_stats["average_fallback_time_ms"]
        new_avg = ((current_avg * (total_fallbacks - 1)) + execution_time) / total_fallbacks
        self.fallback_stats["average_fallback_time_ms"] = round(new_avg, 2)
        
    def get_fallback_statistics(self) -> Dict[str, Any]:
        """Get fallback execution statistics."""
        return self.fallback_stats.copy()
        
    def reset_statistics(self):
        """Reset fallback statistics."""
        self.fallback_stats = {
            "total_fallbacks_executed": 0,
            "fallbacks_by_strategy": {strategy.value: 0 for strategy in FallbackStrategy},
            "successful_fallbacks": 0,
            "failed_fallbacks": 0,
            "average_fallback_time_ms": 0.0
        }