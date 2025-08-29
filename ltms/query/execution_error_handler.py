"""
LTMC Execution Error Handler
Real error handling and graceful degradation for parallel execution - NO PLACEHOLDERS

Handles execution failures with intelligent fallback strategies, error classification,
and graceful degradation to ensure system resilience and user experience.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from .execution_plan import ExecutionPlan, DatabaseOperation
from .error_classification import ErrorClassifier, ErrorSeverity, FallbackStrategy
from .fallback_strategies import FallbackExecutor


class ExecutionErrorHandler:
    """
    Production error handler for LTMC parallel execution failures.
    
    Provides intelligent error classification, recovery strategies, and graceful
    degradation to maintain system resilience under various failure conditions.
    
    Design Philosophy:
    - Fail gracefully: Never leave user with no response
    - Smart fallbacks: Use best available alternative
    - Error learning: Track patterns for prevention
    - Performance preservation: Fast recovery paths
    """
    
    def __init__(self):
        """Initialize error handler with modular components."""
        # Use modular error classification and fallback execution
        self.classifier = ErrorClassifier()
        self.fallback_executor = FallbackExecutor()
        
        # Basic statistics tracking
        self.error_stats = {
            "total_errors_handled": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "average_recovery_time_ms": 0.0
        }
        
    async def handle_coordination_failure(self, execution_plan: ExecutionPlan,
                                        coordination_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle coordination failure with intelligent fallback strategy.
        
        Args:
            execution_plan: Original execution plan that failed
            coordination_result: Failed coordination result with error details
            
        Returns:
            Fallback execution result
        """
        start_time = time.time()
        self.error_stats["total_errors_handled"] += 1
        
        # Classify the coordination error using modular classifier
        error_messages = [str(err.get("message", "")) for err in coordination_result.get("errors", [])]
        primary_error = " ".join(error_messages) if error_messages else "Unknown coordination error"
        
        severity, strategy, classification_details = self.classifier.classify_error(
            primary_error, {"error_type": "coordination_failure"}
        )
        
        try:
            # Execute fallback strategy using modular executor
            failed_operations = self._extract_failed_operations(execution_plan, coordination_result)
            error_context = {
                "error_type": "coordination_failure",
                "original_errors": coordination_result.get("errors", []),
                "classification_details": classification_details
            }
            
            result = await self.fallback_executor.execute_fallback(
                strategy, execution_plan, failed_operations, error_context
            )
            
            # Track recovery success
            recovery_time = (time.time() - start_time) * 1000
            if result.get("success", False):
                self.error_stats["successful_recoveries"] += 1
            else:
                self.error_stats["failed_recoveries"] += 1
                
            self._update_recovery_time_stats(recovery_time)
            
            # Add error handling metadata
            result["error_handling"] = {
                "error_severity": severity.value,
                "fallback_strategy": strategy.value,
                "recovery_time_ms": round(recovery_time, 2),
                "recovery_successful": result.get("success", False),
                "classification_details": classification_details
            }
            
            return result
            
        except Exception as e:
            # Fallback to minimal response if recovery fails
            self.error_stats["failed_recoveries"] += 1
            return self._create_minimal_error_response(execution_plan, str(e))
            
    async def handle_execution_error(self, execution_plan: ExecutionPlan,
                                   error: Exception) -> Dict[str, Any]:
        """
        Handle unexpected execution errors with graceful degradation.
        
        Args:
            execution_plan: Execution plan that encountered error
            error: Exception that occurred
            
        Returns:
            Error handling result with fallback data
        """
        start_time = time.time()
        self.error_stats["total_errors_handled"] += 1
        
        # Classify the execution error using modular classifier
        severity, strategy, classification_details = self.classifier.classify_error(
            str(error), {"error_type": type(error).__name__}
        )
        
        try:
            # Execute fallback strategy using modular executor
            failed_operations = execution_plan.operations  # All operations failed
            error_context = {
                "error_type": type(error).__name__,
                "original_error": str(error),
                "classification_details": classification_details
            }
            
            result = await self.fallback_executor.execute_fallback(
                strategy, execution_plan, failed_operations, error_context
            )
                
            recovery_time = (time.time() - start_time) * 1000
            self._update_recovery_time_stats(recovery_time)
            
            if result.get("success", False):
                self.error_stats["successful_recoveries"] += 1
            else:
                self.error_stats["failed_recoveries"] += 1
                
            result["error_handling"] = {
                "original_error": str(error),
                "error_type": type(error).__name__,
                "error_severity": severity.value,
                "fallback_strategy": strategy.value,
                "recovery_time_ms": round(recovery_time, 2),
                "classification_details": classification_details
            }
            
            return result
            
        except Exception as fallback_error:
            self.error_stats["failed_recoveries"] += 1
            return self._create_minimal_error_response(execution_plan, str(fallback_error))
            
    def _extract_failed_operations(self, execution_plan: ExecutionPlan, 
                                 coordination_result: Dict[str, Any]) -> List[DatabaseOperation]:
        """Extract operations that failed from coordination result."""
        # For coordination failures, assume all operations failed
        return execution_plan.operations
        
        
    def _create_minimal_error_response(self, execution_plan: ExecutionPlan, error_message: str) -> Dict[str, Any]:
        """Create minimal error response when all fallbacks fail."""
        return {
            "success": False,
            "results": [],
            "databases_queried": [],
            "fallback_used": True,
            "fallback_type": "error_response",
            "error": error_message,
            "query_type": execution_plan.query_type.value if execution_plan else "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
    def _extract_search_terms_from_plan(self, execution_plan: ExecutionPlan) -> List[str]:
        """Extract search terms from execution plan operations."""
        search_terms = []
        for operation in execution_plan.operations:
            if "search_terms" in operation.parameters:
                search_terms.extend(operation.parameters["search_terms"])
            elif "query" in operation.parameters:
                query = operation.parameters["query"]
                if isinstance(query, str):
                    search_terms.extend(query.split())
        return list(set(search_terms))  # Remove duplicates
        
    def _update_database_reliability_stats(self, execution_plan: ExecutionPlan, error_info: Dict[str, Any]):
        """Update database reliability statistics based on errors."""
        for operation in execution_plan.operations:
            db_target = operation.database_target.value
            if db_target in self.error_stats["database_reliability"]:
                self.error_stats["database_reliability"][db_target]["failures"] += 1
                
    def _update_recovery_time_stats(self, recovery_time: float):
        """Update recovery time statistics."""
        total_recoveries = self.error_stats["successful_recoveries"] + self.error_stats["failed_recoveries"]
        if total_recoveries > 1:
            current_avg = self.error_stats["average_recovery_time_ms"]
            new_avg = ((current_avg * (total_recoveries - 1)) + recovery_time) / total_recoveries
            self.error_stats["average_recovery_time_ms"] = round(new_avg, 2)
        else:
            self.error_stats["average_recovery_time_ms"] = round(recovery_time, 2)
            
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics for monitoring."""
        stats = self.error_stats.copy()
        
        # Calculate derived statistics
        total_handled = stats["total_errors_handled"]
        if total_handled > 0:
            stats["overall_recovery_rate"] = round(
                stats["successful_recoveries"] / total_handled * 100, 2
            )
        else:
            stats["overall_recovery_rate"] = 0.0
            
        # Calculate database reliability scores
        for db_name, reliability_data in stats["database_reliability"].items():
            total_ops = reliability_data["failures"] + reliability_data["recoveries"]
            if total_ops > 0:
                reliability_data["reliability_score"] = round(
                    (1 - (reliability_data["failures"] / total_ops)) * 100, 2
                )
            else:
                reliability_data["reliability_score"] = 100.0
                
        return stats
        
    def reset_statistics(self):
        """Reset error handling statistics."""
        for key, value in self.error_stats.items():
            if isinstance(value, (int, float)):
                self.error_stats[key] = 0 if isinstance(value, int) else 0.0
            elif isinstance(value, dict):
                for sub_key in value:
                    if isinstance(value[sub_key], (int, float)):
                        value[sub_key] = 0 if isinstance(value[sub_key], int) else 0.0
                    elif isinstance(value[sub_key], dict):
                        for sub_sub_key in value[sub_key]:
                            value[sub_key][sub_sub_key] = 0