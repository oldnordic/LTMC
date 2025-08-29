"""
LTMC Execution Coordinator
Real async coordination for parallel/sequential database operations - NO PLACEHOLDERS

Coordinates execution of database operations from execution plans with proper
async parallelization, dependency management, and performance optimization.
"""

import asyncio
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime

from .execution_plan import DatabaseOperation, ExecutionStrategy
from .operation_runner import DatabaseOperationRunner
from .execution_stats import CoordinationStatistics


class ExecutionCoordinator:
    """
    Production execution coordinator for LTMC database operations.
    
    Manages parallel and sequential execution of database operations with
    real async coordination, dependency tracking, and performance monitoring.
    
    Design Philosophy:
    - Real parallelization: Uses asyncio.gather() for true concurrency
    - Dependency awareness: Respects sequential requirements
    - Performance optimization: Minimizes coordination overhead
    - Error isolation: Individual operation failures don't cascade
    """
    
    def __init__(self):
        """Initialize execution coordinator with modular components."""
        self.operation_runner = DatabaseOperationRunner()
        self.stats_tracker = CoordinationStatistics()
        
    async def coordinate_operations(self, operations: List[DatabaseOperation]) -> Dict[str, Any]:
        """
        Coordinate execution of database operations with real async parallelization.
        
        Args:
            operations: List of database operations to execute
            
        Returns:
            Coordination result with aggregated operation results and metadata
        """
        if not operations:
            return {
                "success": True,
                "results": [],
                "coordination_metadata": {
                    "execution_strategy": "empty",
                    "parallel_count": 0,
                    "sequential_count": 0,
                    "coordination_overhead_ms": 0
                },
                "errors": [],
                "warnings": []
            }
            
        start_time = time.time()
        
        try:
            # Step 1: Categorize operations by execution strategy
            parallel_ops, sequential_ops = self._categorize_operations(operations)
            
            # Step 2: Execute operations based on strategy
            results, errors, warnings = await self._execute_categorized_operations(
                parallel_ops, sequential_ops
            )
            
            # Step 3: Calculate coordination overhead
            coordination_time = (time.time() - start_time) * 1000
            coordination_overhead = self._calculate_coordination_overhead(
                coordination_time, len(operations)
            )
            
            # Step 4: Update statistics using modular tracker
            execution_type = self._determine_execution_strategy(parallel_ops, sequential_ops)
            self.stats_tracker.record_coordination(
                len(operations), execution_type, coordination_overhead, True
            )
            
            # Step 5: Build coordination result
            return {
                "success": len(results) > 0 or len(operations) == 0,
                "results": results,
                "coordination_metadata": {
                    "execution_strategy": self._determine_execution_strategy(parallel_ops, sequential_ops),
                    "parallel_count": len(parallel_ops),
                    "sequential_count": len(sequential_ops),
                    "coordination_overhead_ms": coordination_overhead,
                    "total_coordination_time_ms": coordination_time,
                    "operations_successful": len([r for r in results if r.get("success", False)]),
                    "operations_failed": len([r for r in results if not r.get("success", False)])
                },
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            # Handle coordination failure
            coordination_time = (time.time() - start_time) * 1000
            self.stats_tracker.record_coordination(
                len(operations), "failed", coordination_time, False
            )
            
            return {
                "success": False,
                "results": [],
                "coordination_metadata": {
                    "execution_strategy": "failed",
                    "coordination_overhead_ms": coordination_time,
                    "error_occurred": True
                },
                "errors": [{"error_type": "coordination_failure", "message": str(e)}],
                "warnings": []
            }
            
    def _categorize_operations(self, operations: List[DatabaseOperation]) -> Tuple[List[DatabaseOperation], List[DatabaseOperation]]:
        """Categorize operations into parallel and sequential groups."""
        parallel_ops = []
        sequential_ops = []
        
        for operation in operations:
            if operation.execution_strategy == ExecutionStrategy.PARALLEL:
                parallel_ops.append(operation)
            else:
                sequential_ops.append(operation)
                
        return parallel_ops, sequential_ops
        
    async def _execute_categorized_operations(self, parallel_ops: List[DatabaseOperation],
                                            sequential_ops: List[DatabaseOperation]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """Execute categorized operations with proper coordination."""
        all_results = []
        all_errors = []
        all_warnings = []
        
        # Execute parallel operations concurrently
        if parallel_ops:
            parallel_results, parallel_errors, parallel_warnings = await self._execute_parallel_operations(parallel_ops)
            all_results.extend(parallel_results)
            all_errors.extend(parallel_errors)
            all_warnings.extend(parallel_warnings)
            
        # Execute sequential operations in order
        if sequential_ops:
            sequential_results, sequential_errors, sequential_warnings = await self._execute_sequential_operations(sequential_ops)
            all_results.extend(sequential_results)
            all_errors.extend(sequential_errors)
            all_warnings.extend(sequential_warnings)
            
        return all_results, all_errors, all_warnings
        
    async def _execute_parallel_operations(self, operations: List[DatabaseOperation]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """Execute operations in parallel using asyncio.gather()."""
        if not operations:
            return [], [], []
            
        # Create async tasks for all parallel operations
        tasks = [
            self._execute_operation_with_error_handling(op)
            for op in operations
        ]
        
        # Execute all operations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate successful results from errors
        successful_results = []
        errors = []
        warnings = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "error_type": "operation_execution_error",
                    "operation_index": i,
                    "database_target": operations[i].database_target.value,
                    "message": str(result)
                })
            elif isinstance(result, dict):
                if result.get("success", False):
                    successful_results.append(result)
                else:
                    error_info = {
                        "error_type": "operation_failure",
                        "operation_index": i,
                        "database_target": operations[i].database_target.value,
                        "message": result.get("error", "Unknown operation failure")
                    }
                    errors.append(error_info)
                    
                    # Include partial results if available
                    if "results" in result:
                        successful_results.append(result)
                        
        return successful_results, errors, warnings
        
    async def _execute_sequential_operations(self, operations: List[DatabaseOperation]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """Execute operations sequentially with dependency awareness."""
        if not operations:
            return [], [], []
            
        results = []
        errors = []
        warnings = []
        
        for i, operation in enumerate(operations):
            try:
                result = await self._execute_operation_with_error_handling(operation)
                
                if isinstance(result, dict):
                    if result.get("success", False):
                        results.append(result)
                    else:
                        errors.append({
                            "error_type": "sequential_operation_failure",
                            "operation_index": i,
                            "database_target": operation.database_target.value,
                            "message": result.get("error", "Sequential operation failed")
                        })
                        
                        # For sequential operations, consider whether to continue or abort
                        if operation.operation_type in ["file_search", "graph_query"]:
                            # Non-critical operations - continue with warnings
                            warnings.append(f"Non-critical operation failed: {operation.database_target.value}")
                        else:
                            # Critical operation failed - but continue for robustness
                            warnings.append(f"Critical operation failed, continuing: {operation.database_target.value}")
                            
                else:
                    errors.append({
                        "error_type": "sequential_operation_exception",
                        "operation_index": i,
                        "database_target": operation.database_target.value,
                        "message": str(result) if result else "Unknown error"
                    })
                    
            except Exception as e:
                errors.append({
                    "error_type": "sequential_execution_exception",
                    "operation_index": i,
                    "database_target": operation.database_target.value,
                    "message": str(e)
                })
                
        return results, errors, warnings
        
    async def _execute_operation_with_error_handling(self, operation: DatabaseOperation) -> Dict[str, Any]:
        """Execute single operation with timeout and error handling."""
        try:
            # Apply timeout based on operation timeout setting
            timeout = operation.timeout_ms / 1000.0  # Convert to seconds
            
            result = await asyncio.wait_for(
                self.operation_runner.run_operation(operation),
                timeout=timeout
            )
            
            return result
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Operation timed out after {operation.timeout_ms}ms",
                "error_type": "timeout",
                "database_target": operation.database_target.value,
                "results": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_exception",
                "database_target": operation.database_target.value,
                "results": []
            }
            
    def _calculate_coordination_overhead(self, total_coordination_time: float,
                                       operation_count: int) -> float:
        """Calculate coordination overhead per operation."""
        if operation_count == 0:
            return 0.0
            
        # Estimate pure operation time (this is approximate)
        estimated_operation_time = operation_count * 50.0  # 50ms average per operation
        
        # Coordination overhead is time beyond estimated operation time
        overhead = max(0.0, total_coordination_time - estimated_operation_time)
        
        return round(overhead, 2)
        
    def _determine_execution_strategy(self, parallel_ops: List[DatabaseOperation],
                                    sequential_ops: List[DatabaseOperation]) -> str:
        """Determine overall execution strategy description."""
        if parallel_ops and sequential_ops:
            return "mixed"
        elif parallel_ops:
            return "parallel"
        elif sequential_ops:
            return "sequential"
        else:
            return "empty"
            
    def get_coordination_statistics(self) -> Dict[str, Any]:
        """Get coordination statistics using modular tracker."""
        return self.stats_tracker.get_performance_summary()
        
    def reset_statistics(self):
        """Reset coordination statistics using modular tracker."""
        self.stats_tracker.reset()