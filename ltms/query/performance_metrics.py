"""
LTMC Performance Metrics Data Models
Core data structures for performance tracking - NO PLACEHOLDERS

Defines the data models and metrics calculations for LTMC execution performance monitoring.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from collections import deque, defaultdict

from .execution_plan import ExecutionPlan


@dataclass
class ExecutionMetrics:
    """Performance metrics for a single execution."""
    execution_id: str
    start_time: float
    end_time: Optional[float] = None
    execution_plan: Optional[ExecutionPlan] = None
    operation_count: int = 0
    parallel_operation_count: int = 0
    sequential_operation_count: int = 0
    databases_used: List[str] = None
    sla_compliance: bool = True
    error_occurred: bool = False
    
    def __post_init__(self):
        if self.databases_used is None:
            self.databases_used = []
            
    def get_execution_time_ms(self) -> float:
        """Get execution time in milliseconds."""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000


class PerformanceStatistics:
    """Container for performance statistics with calculation methods."""
    
    def __init__(self, sla_target_ms: float = 2000.0):
        self.sla_target_ms = sla_target_ms
        
        # Core statistics
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "sla_compliant_executions": 0,
            "sla_violations": 0,
            "average_execution_time_ms": 0.0,
            "median_execution_time_ms": 0.0,
            "p95_execution_time_ms": 0.0,
            "p99_execution_time_ms": 0.0,
            "fastest_execution_ms": float('inf'),
            "slowest_execution_ms": 0.0,
            "current_sla_compliance_rate": 100.0,
            "executions_by_database": defaultdict(int),
            "parallel_efficiency_avg": 0.0,
            "coordination_overhead_avg_ms": 0.0
        }
        
    def update_from_metrics(self, metrics: ExecutionMetrics, execution_time_ms: float, 
                           result: Dict[str, Any]):
        """Update statistics from execution metrics."""
        # Basic counters
        self.stats["total_executions"] += 1
        
        if not metrics.error_occurred:
            self.stats["successful_executions"] += 1
        else:
            self.stats["failed_executions"] += 1
            
        if metrics.sla_compliance:
            self.stats["sla_compliant_executions"] += 1
        else:
            self.stats["sla_violations"] += 1
            
        # Timing statistics
        self._update_timing_stats(execution_time_ms)
        
        # Database-specific statistics
        for db_name in metrics.databases_used:
            self.stats["executions_by_database"][db_name] += 1
            
        # Parallel execution efficiency
        if "coordination_stats" in result.get("execution_metadata", {}):
            coord_stats = result["execution_metadata"]["coordination_stats"]
            self._update_parallel_efficiency_stats(coord_stats)
            
        # Update SLA compliance rate
        total = self.stats["total_executions"]
        compliant = self.stats["sla_compliant_executions"]
        self.stats["current_sla_compliance_rate"] = round((compliant / total) * 100, 2)
        
    def _update_timing_stats(self, execution_time_ms: float):
        """Update execution timing statistics."""
        # Update min/max
        self.stats["fastest_execution_ms"] = min(
            self.stats["fastest_execution_ms"], execution_time_ms
        )
        self.stats["slowest_execution_ms"] = max(
            self.stats["slowest_execution_ms"], execution_time_ms
        )
        
        # Update average
        total_executions = self.stats["total_executions"]
        current_avg = self.stats["average_execution_time_ms"]
        new_avg = ((current_avg * (total_executions - 1)) + execution_time_ms) / total_executions
        self.stats["average_execution_time_ms"] = round(new_avg, 2)
        
    def _update_parallel_efficiency_stats(self, coordination_stats: Dict[str, Any]):
        """Update parallel execution efficiency statistics."""
        if "parallel_efficiency" in coordination_stats:
            efficiency = coordination_stats["parallel_efficiency"]
            total_executions = self.stats["total_executions"]
            current_avg = self.stats["parallel_efficiency_avg"]
            new_avg = ((current_avg * (total_executions - 1)) + efficiency) / total_executions
            self.stats["parallel_efficiency_avg"] = round(new_avg, 2)
            
        if "coordination_overhead_ms" in coordination_stats:
            overhead = coordination_stats["coordination_overhead_ms"]
            total_executions = self.stats["total_executions"]
            current_avg = self.stats["coordination_overhead_avg_ms"]
            new_avg = ((current_avg * (total_executions - 1)) + overhead) / total_executions
            self.stats["coordination_overhead_avg_ms"] = round(new_avg, 2)
            
    def update_percentiles(self, execution_history: deque):
        """Update percentile statistics from execution history."""
        if len(execution_history) >= 10:
            recent_times = []
            for metrics in list(execution_history)[-100:]:  # Last 100 executions
                if metrics.end_time:
                    execution_duration = metrics.get_execution_time_ms()
                    recent_times.append(execution_duration)
                    
            if recent_times:
                recent_times.sort()
                self.stats["median_execution_time_ms"] = self._calculate_percentile(recent_times, 50)
                self.stats["p95_execution_time_ms"] = self._calculate_percentile(recent_times, 95)
                self.stats["p99_execution_time_ms"] = self._calculate_percentile(recent_times, 99)
                
    def _calculate_percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return round(sorted_values[index], 2)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get copy of current statistics."""
        return dict(self.stats)
        
    def reset(self):
        """Reset all statistics."""
        for key, value in self.stats.items():
            if isinstance(value, (int, float)):
                if key == "fastest_execution_ms":
                    self.stats[key] = float('inf')
                else:
                    self.stats[key] = 0 if isinstance(value, int) else 0.0
            elif isinstance(value, defaultdict):
                self.stats[key] = defaultdict(int)


class DatabasePerformanceTracker:
    """Tracks performance metrics specific to individual databases."""
    
    def __init__(self):
        self.database_performance = defaultdict(lambda: {
            "total_operations": 0,
            "successful_operations": 0,
            "average_response_time_ms": 0.0,
            "reliability_score": 100.0
        })
        
    def update_database_performance(self, database_name: str, execution_time_ms: float, success: bool):
        """Update database-specific performance statistics."""
        db_stats = self.database_performance[database_name]
        db_stats["total_operations"] += 1
        
        if success:
            db_stats["successful_operations"] += 1
            
        # Update average response time
        current_avg = db_stats["average_response_time_ms"]
        total_ops = db_stats["total_operations"]
        new_avg = ((current_avg * (total_ops - 1)) + execution_time_ms) / total_ops
        db_stats["average_response_time_ms"] = round(new_avg, 2)
        
        # Update reliability score
        reliability = (db_stats["successful_operations"] / db_stats["total_operations"]) * 100
        db_stats["reliability_score"] = round(reliability, 2)
        
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        return dict(self.database_performance)
        
    def reset(self):
        """Reset database performance statistics."""
        self.database_performance.clear()


class RecentExecutionTracker:
    """Tracks recent executions in a time window."""
    
    def __init__(self, window_duration_seconds: int = 300):
        self.window_duration_seconds = window_duration_seconds
        self.recent_executions: deque = deque()
        
    def add_execution(self, execution_id: str, execution_time_ms: float, 
                     sla_compliant: bool, success: bool, databases_used: List[str]):
        """Add execution to recent tracking."""
        self.recent_executions.append({
            "execution_id": execution_id,
            "timestamp": time.time(),
            "execution_time_ms": execution_time_ms,
            "sla_compliant": sla_compliant,
            "success": success,
            "databases_used": databases_used
        })
        
        # Clean old entries
        self._clean_window()
        
    def _clean_window(self):
        """Remove old entries from time window."""
        current_time = time.time()
        cutoff_time = current_time - self.window_duration_seconds
        
        while self.recent_executions and self.recent_executions[0]["timestamp"] < cutoff_time:
            self.recent_executions.popleft()
            
    def get_recent_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics for recent time window."""
        if not self.recent_executions:
            return {
                "executions_in_window": 0,
                "average_time_ms": 0.0,
                "sla_compliance_rate": 100.0,
                "window_duration_minutes": self.window_duration_seconds / 60
            }
            
        recent_list = list(self.recent_executions)
        total_time = sum(exec_data["execution_time_ms"] for exec_data in recent_list)
        avg_time = total_time / len(recent_list)
        
        compliant_count = sum(1 for exec_data in recent_list if exec_data["sla_compliant"])
        compliance_rate = (compliant_count / len(recent_list)) * 100
        
        return {
            "executions_in_window": len(recent_list),
            "average_time_ms": round(avg_time, 2),
            "sla_compliance_rate": round(compliance_rate, 2),
            "window_duration_minutes": self.window_duration_seconds / 60
        }
        
    def reset(self):
        """Reset recent execution tracking."""
        self.recent_executions.clear()