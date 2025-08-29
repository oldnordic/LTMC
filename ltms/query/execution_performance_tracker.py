"""
LTMC Execution Performance Tracker (Refactored)
Main performance tracking coordinator - NO PLACEHOLDERS

Coordinates performance tracking using modular components for metrics,
analytics, and reporting within the 300-350 line limit.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

from .execution_plan import ExecutionPlan
from .performance_metrics import ExecutionMetrics, PerformanceStatistics, DatabasePerformanceTracker, RecentExecutionTracker
from .performance_analytics import PerformanceAnalytics


class ExecutionPerformanceTracker:
    """
    Production performance tracker for LTMC parallel execution monitoring.
    
    Coordinates modular performance tracking components for comprehensive
    execution monitoring, SLA compliance, and performance analytics.
    
    Design Philosophy:
    - Modular composition: Uses specialized components for different concerns
    - Real-time tracking: Immediate metric collection and analysis
    - SLA enforcement: Continuous compliance monitoring
    - Low overhead: Minimal impact on execution performance
    """
    
    def __init__(self, sla_target_ms: float = 2000.0, history_size: int = 1000):
        """Initialize performance tracker with modular components."""
        self.sla_target_ms = sla_target_ms
        self.history_size = history_size
        
        # Active execution tracking
        self.active_executions: Dict[str, ExecutionMetrics] = {}
        
        # Historical performance data (ring buffer for memory efficiency)
        self.execution_history: deque = deque(maxlen=history_size)
        
        # Modular components
        self.performance_stats = PerformanceStatistics(sla_target_ms)
        self.database_tracker = DatabasePerformanceTracker()
        self.recent_tracker = RecentExecutionTracker()
        self.analytics = PerformanceAnalytics(sla_target_ms)
        
    def start_execution(self, execution_id: str, execution_plan: ExecutionPlan):
        """Start tracking execution performance."""
        metrics = ExecutionMetrics(
            execution_id=execution_id,
            start_time=time.time(),
            execution_plan=execution_plan,
            operation_count=len(execution_plan.operations),
            parallel_operation_count=len(execution_plan.parallel_operations),
            sequential_operation_count=len(execution_plan.sequential_operations),
            databases_used=[op.database_target.value for op in execution_plan.operations]
        )
        
        self.active_executions[execution_id] = metrics
        
    def complete_execution(self, execution_id: str, result: Dict[str, Any],
                          execution_time_ms: float):
        """Complete execution tracking and update all statistics."""
        if execution_id not in self.active_executions:
            return  # Execution not tracked
            
        metrics = self.active_executions[execution_id]
        metrics.end_time = time.time()
        metrics.sla_compliance = execution_time_ms <= self.sla_target_ms
        metrics.error_occurred = not result.get("success", False)
        
        # Move to historical data
        self.execution_history.append(metrics)
        del self.active_executions[execution_id]
        
        # Update all tracking components
        self._update_all_trackers(metrics, execution_time_ms, result)
        
    def _update_all_trackers(self, metrics: ExecutionMetrics, execution_time_ms: float,
                           result: Dict[str, Any]):
        """Update all tracking components with new metrics."""
        # Update performance statistics
        self.performance_stats.update_from_metrics(metrics, execution_time_ms, result)
        self.performance_stats.update_percentiles(self.execution_history)
        
        # Update database-specific performance
        for db_name in metrics.databases_used:
            self.database_tracker.update_database_performance(
                db_name, execution_time_ms, not metrics.error_occurred
            )
            
        # Update recent execution tracking
        self.recent_tracker.add_execution(
            metrics.execution_id, execution_time_ms, metrics.sla_compliance,
            not metrics.error_occurred, metrics.databases_used
        )
        
    def get_execution_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get detailed metrics for specific execution."""
        # Check active executions first
        if execution_id in self.active_executions:
            metrics = self.active_executions[execution_id]
            elapsed_time = metrics.get_execution_time_ms()
            
            return {
                "execution_id": execution_id,
                "status": "running",
                "elapsed_time_ms": round(elapsed_time, 2),
                "operation_count": metrics.operation_count,
                "parallel_operations": metrics.parallel_operation_count,
                "sequential_operations": metrics.sequential_operation_count,
                "databases_used": metrics.databases_used,
                "projected_sla_compliance": elapsed_time <= self.sla_target_ms
            }
            
        # Search historical data
        for historical_metrics in reversed(self.execution_history):
            if historical_metrics.execution_id == execution_id:
                total_time = historical_metrics.get_execution_time_ms()
                
                return {
                    "execution_id": execution_id,
                    "status": "completed",
                    "total_execution_time_ms": round(total_time, 2),
                    "operation_count": historical_metrics.operation_count,
                    "parallel_operations": historical_metrics.parallel_operation_count,
                    "sequential_operations": historical_metrics.sequential_operation_count,
                    "databases_used": historical_metrics.databases_used,
                    "sla_compliance": historical_metrics.sla_compliance,
                    "success": not historical_metrics.error_occurred
                }
                
        return {"execution_id": execution_id, "status": "not_found"}
        
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics from all components."""
        stats = self.performance_stats.get_stats()
        
        # Add current active executions count
        stats["active_executions"] = len(self.active_executions)
        
        # Add component-specific statistics
        stats["database_performance"] = self.database_tracker.get_database_stats()
        stats["recent_performance"] = self.recent_tracker.get_recent_stats()
        
        # Add analytics
        stats["sla_analysis"] = self.analytics.calculate_sla_analysis(stats)
        stats["trend_analysis"] = self.analytics.calculate_trend_analysis(self.execution_history)
        stats["health_indicators"] = self.analytics.calculate_health_indicators(
            stats, stats["database_performance"]
        )
        stats["efficiency_metrics"] = self.analytics.calculate_efficiency_metrics(
            stats, self.execution_history
        )
        
        return stats
        
    def get_sla_compliance_report(self) -> Dict[str, Any]:
        """Get detailed SLA compliance report."""
        performance_stats = self.performance_stats.get_stats()
        return self.analytics.generate_sla_compliance_report(
            performance_stats, self.execution_history
        )
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        performance_stats = self.performance_stats.get_stats()
        database_performance = self.database_tracker.get_database_stats()
        recent_stats = self.recent_tracker.get_recent_stats()
        
        return self.analytics.generate_performance_summary(
            performance_stats, database_performance, recent_stats, self.execution_history
        )
        
    def get_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        performance_stats = self.performance_stats.get_stats()
        database_performance = self.database_tracker.get_database_stats()
        
        return self.analytics.generate_performance_recommendations(
            performance_stats, database_performance
        )
        
    def reset_statistics(self):
        """Reset all performance statistics across all components."""
        self.active_executions.clear()
        self.execution_history.clear()
        
        # Reset all tracking components
        self.performance_stats.reset()
        self.database_tracker.reset()
        self.recent_tracker.reset()
        
    def get_health_status(self) -> str:
        """Get overall system health status."""
        stats = self.get_overall_statistics()
        health_indicators = stats.get("health_indicators", {})
        return health_indicators.get("overall_health", "unknown")
        
    def is_sla_compliant(self) -> bool:
        """Check if system is currently SLA compliant."""
        stats = self.performance_stats.get_stats()
        return stats["current_sla_compliance_rate"] >= 95.0
        
    def get_current_performance_snapshot(self) -> Dict[str, Any]:
        """Get current performance snapshot for monitoring."""
        stats = self.performance_stats.get_stats()
        recent_stats = self.recent_tracker.get_recent_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_executions": len(self.active_executions),
            "total_executions": stats["total_executions"],
            "current_sla_compliance_rate": stats["current_sla_compliance_rate"],
            "average_execution_time_ms": stats["average_execution_time_ms"],
            "recent_average_time_ms": recent_stats["average_time_ms"],
            "health_status": self.get_health_status(),
            "sla_compliant": self.is_sla_compliant()
        }