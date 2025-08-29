"""
LTMC Parallel Query Executor
Production parallel execution coordinator for multi-database queries - NO PLACEHOLDERS

Main entry point for executing federation router execution plans across multiple
LTMC database systems with real async coordination and performance monitoring.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .execution_plan import ExecutionPlan, DatabaseOperation
from .execution_coordinator import ExecutionCoordinator
from .operation_runner import DatabaseOperationRunner
from .result_aggregator import ResultAggregator
from .execution_error_handler import ExecutionErrorHandler
from .execution_performance_tracker import ExecutionPerformanceTracker


class ParallelQueryExecutor:
    """
    Production parallel query executor for LTMC unified query system.
    
    Orchestrates execution of federation router plans across multiple databases
    with real async coordination, error handling, and performance monitoring.
    
    Design Philosophy:
    - Single responsibility: Coordinates other specialized components
    - Real async execution: No fake parallel processing
    - Error resilience: Graceful degradation on failures
    - Performance monitoring: Real-time SLA tracking
    """
    
    def __init__(self):
        """Initialize parallel executor with specialized components."""
        self.coordinator = ExecutionCoordinator()
        self.runner = DatabaseOperationRunner()
        self.aggregator = ResultAggregator()
        self.error_handler = ExecutionErrorHandler()
        self.performance_tracker = ExecutionPerformanceTracker()
        
        # SLA requirements
        self.sla_target_ms = 2000  # 2 second tool call SLA
        
    async def execute_plan(self, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Execute execution plan with real parallel coordination.
        
        Args:
            execution_plan: ExecutionPlan from federation router
            
        Returns:
            Aggregated results with execution metadata
            
        Raises:
            ValueError: If execution plan is invalid
        """
        if not execution_plan or not execution_plan.operations:
            raise ValueError("Execution plan must contain operations")
            
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = time.time()
        
        # Start performance tracking
        self.performance_tracker.start_execution(execution_id, execution_plan)
        
        try:
            # Step 1: Coordinate operation execution (parallel/sequential)
            coordination_result = await self.coordinator.coordinate_operations(
                execution_plan.operations
            )
            
            # Step 2: Check for coordination errors
            if not coordination_result.get("success", False):
                return await self._handle_coordination_failure(
                    execution_plan, coordination_result, execution_id, start_time
                )
                
            # Step 3: Aggregate results from multiple databases
            raw_results = coordination_result.get("results", [])
            aggregated_results = self.aggregator.aggregate_results(raw_results)
            
            # Step 4: Build final response with metadata
            execution_time = (time.time() - start_time) * 1000
            final_result = self._build_final_result(
                aggregated_results,
                coordination_result,
                execution_plan,
                execution_id,
                execution_time
            )
            
            # Step 5: Complete performance tracking
            self.performance_tracker.complete_execution(
                execution_id, final_result, execution_time
            )
            
            return final_result
            
        except Exception as e:
            # Step 6: Handle unexpected errors
            return await self._handle_execution_error(
                execution_plan, e, execution_id, start_time
            )
            
    async def _handle_coordination_failure(self, execution_plan: ExecutionPlan,
                                         coordination_result: Dict[str, Any],
                                         execution_id: str, start_time: float) -> Dict[str, Any]:
        """Handle coordination failure with fallback strategy."""
        fallback_result = await self.error_handler.handle_coordination_failure(
            execution_plan, coordination_result
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "success": fallback_result.get("success", False),
            "results": fallback_result.get("results", []),
            "execution_metadata": {
                "execution_id": execution_id,
                "execution_time_ms": execution_time,
                "fallback_triggered": True,
                "fallback_reason": "coordination_failure",
                "original_error": coordination_result.get("error", "Unknown coordination error"),
                "databases_queried": fallback_result.get("databases_queried", []),
                "performance_metrics": self.performance_tracker.get_execution_metrics(execution_id)
            }
        }
        
    async def _handle_execution_error(self, execution_plan: ExecutionPlan,
                                    error: Exception, execution_id: str,
                                    start_time: float) -> Dict[str, Any]:
        """Handle unexpected execution errors."""
        error_result = await self.error_handler.handle_execution_error(
            execution_plan, error
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "success": False,
            "results": error_result.get("results", []),
            "execution_metadata": {
                "execution_id": execution_id,
                "execution_time_ms": execution_time,
                "error_occurred": True,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "fallback_triggered": error_result.get("fallback_used", False),
                "databases_queried": error_result.get("databases_queried", []),
                "performance_metrics": self.performance_tracker.get_execution_metrics(execution_id)
            }
        }
        
    def _build_final_result(self, aggregated_results: Dict[str, Any],
                          coordination_result: Dict[str, Any],
                          execution_plan: ExecutionPlan, execution_id: str,
                          execution_time: float) -> Dict[str, Any]:
        """Build final result with comprehensive metadata."""
        coordination_metadata = coordination_result.get("coordination_metadata", {})
        aggregation_metadata = aggregated_results.get("aggregation_metadata", {})
        
        # Extract database information
        databases_queried = []
        for op in execution_plan.operations:
            if op.database_target.value not in databases_queried:
                databases_queried.append(op.database_target.value)
                
        # Build performance metrics
        performance_metrics = self.performance_tracker.get_execution_metrics(execution_id)
        performance_metrics.update({
            "total_execution_time_ms": execution_time,
            "sla_target_ms": self.sla_target_ms,
            "sla_compliance": execution_time <= self.sla_target_ms,
            "speedup_factor": self._calculate_speedup_factor(execution_plan, execution_time),
            "parallel_efficiency": self._calculate_parallel_efficiency(
                coordination_metadata, execution_time
            )
        })
        
        # Build tool call metadata
        tool_calls_executed = []
        for op in execution_plan.operations:
            try:
                tool_call = op.to_tool_call()
                tool_calls_executed.append(tool_call)
            except Exception:
                continue
                
        return {
            "success": True,
            "results": aggregated_results.get("results", []),
            "execution_metadata": {
                "execution_id": execution_id,
                "execution_time_ms": execution_time,
                "databases_queried": databases_queried,
                "total_operations": len(execution_plan.operations),
                "parallel_operations": len(execution_plan.parallel_operations),
                "sequential_operations": len(execution_plan.sequential_operations),
                "tool_calls_executed": tool_calls_executed,
                "coordination_stats": {
                    "parallel_operations": coordination_metadata.get("parallel_count", 0),
                    "sequential_operations": coordination_metadata.get("sequential_count", 0),
                    "coordination_overhead_ms": coordination_metadata.get("coordination_overhead_ms", 0),
                    "execution_strategy": coordination_metadata.get("execution_strategy", "mixed")
                },
                "result_processing": {
                    "total_results_before_dedup": aggregation_metadata.get("raw_result_count", 0),
                    "total_results_after_dedup": aggregation_metadata.get("final_result_count", 0),
                    "deduplication_ratio": aggregation_metadata.get("deduplication_ratio", 0.0),
                    "ranking_algorithm": aggregation_metadata.get("ranking_algorithm", "score_based")
                },
                "performance_metrics": performance_metrics,
                "errors": coordination_result.get("errors", []),
                "warnings": coordination_result.get("warnings", [])
            }
        }
        
    def _calculate_speedup_factor(self, execution_plan: ExecutionPlan,
                                actual_time: float) -> float:
        """Calculate theoretical speedup from parallelization."""
        if not execution_plan.operations:
            return 1.0
            
        # Calculate theoretical sequential time
        sequential_time = sum(op.estimated_cost for op in execution_plan.operations)
        
        # Calculate speedup factor
        if actual_time > 0:
            speedup = sequential_time / actual_time
            return round(speedup, 2)
        return 1.0
        
    def _calculate_parallel_efficiency(self, coordination_metadata: Dict[str, Any],
                                     execution_time: float) -> float:
        """Calculate parallel execution efficiency percentage."""
        parallel_count = coordination_metadata.get("parallel_count", 0)
        sequential_count = coordination_metadata.get("sequential_count", 0)
        
        if parallel_count == 0:
            return 0.0  # No parallel operations
            
        total_ops = parallel_count + sequential_count
        if total_ops == 0:
            return 0.0
            
        # Simple efficiency calculation based on parallel operation ratio
        parallel_ratio = parallel_count / total_ops
        
        # Factor in coordination overhead
        coordination_overhead = coordination_metadata.get("coordination_overhead_ms", 0)
        overhead_penalty = min(coordination_overhead / execution_time, 0.5) if execution_time > 0 else 0
        
        efficiency = parallel_ratio * (1.0 - overhead_penalty)
        return round(max(0.0, min(1.0, efficiency)) * 100, 1)
        
    async def get_execution_statistics(self) -> Dict[str, Any]:
        """Get overall execution statistics for monitoring."""
        return {
            "performance_tracker": self.performance_tracker.get_overall_statistics(),
            "error_handler": self.error_handler.get_error_statistics(),
            "aggregator": self.aggregator.get_aggregation_statistics(),
            "coordinator": self.coordinator.get_coordination_statistics()
        }
        
    def reset_statistics(self):
        """Reset all component statistics for fresh monitoring."""
        self.performance_tracker.reset_statistics()
        self.error_handler.reset_statistics()
        self.aggregator.reset_statistics()
        self.coordinator.reset_statistics()